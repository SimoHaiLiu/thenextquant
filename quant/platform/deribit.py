# -*- coding:utf-8 -*-

"""
Deribit Trade module 交易模块
https://docs.deribit.com/v2/

Author: HuangTao
Date:   2019/04/20
"""

import json
import copy
import asyncio

from quant.utils import logger
from quant.const import DERIBIT
from quant.position import Position
from quant.tasks import LoopRunTask
from quant.utils.websocket import Websocket
from quant.utils.decorator import async_method_locker
from quant.order import Order
from quant.order import ORDER_ACTION_BUY, ORDER_ACTION_SELL
from quant.order import ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET
from quant.order import ORDER_STATUS_SUBMITTED, ORDER_STATUS_PARTIAL_FILLED, ORDER_STATUS_FILLED, \
    ORDER_STATUS_CANCELED, ORDER_STATUS_FAILED
from quant.order import TRADE_TYPE_BUY_OPEN, TRADE_TYPE_SELL_OPEN, TRADE_TYPE_SELL_CLOSE, TRADE_TYPE_BUY_CLOSE


class DeribitTrade(Websocket):
    """ Deribit Trade module 交易模块
    """

    def __init__(self, account, strategy, symbol, host=None, wss=None, access_key=None, secret_key=None,
                 order_update_callback=None, position_update_callback=None):
        """ 初始化
        @param account 账户
        @param strategy 策略名称
        @param symbol 交易对（合约名称）
        @param host HTTP请求主机地址
        @param wss websocket连接地址
        @param access_key ACCESS KEY
        @param secret_key SECRET KEY
        @param order_update_callback 订单更新回调
        @param position_update_callback 持仓更新回调
        """
        self._account = account
        self._strategy = strategy
        self._platform = DERIBIT
        self._symbol = symbol
        self._host = host
        self._wss = wss
        self._access_key = access_key
        self._secret_key = secret_key

        self._order_update_callback = order_update_callback
        self._position_update_callback = position_update_callback

        self._order_channel = "user.orders.{symbol}.raw".format(symbol=symbol)  # 订单订阅频道

        super(DeribitTrade, self).__init__(self._wss, send_hb_interval=5)

        self._orders = {}  # 订单
        self._position = Position(self._platform, self._account, strategy, symbol)  # 仓位

        self._query_id = 0  # 消息序号id，用来唯一标识请求消息
        self._queries = {}  # 未完成的post请求 {"request_id": future}

        self.initialize()

        # 注册定时任务
        LoopRunTask.register(self._do_auth, 60 * 60)  # 每隔1小时重新授权
        LoopRunTask.register(self._check_position_update, 1)  # 获取持仓

        self._ok = False  # 是否建立授权成功的websocket连接

    @property
    def position(self):
        return copy.copy(self._position)

    @property
    def orders(self):
        return copy.copy(self._orders)

    async def connected_callback(self):
        """ 建立连接之后，授权登陆，然后订阅order和position
        """
        # 授权
        success, error = await self._do_auth()
        if error:
            return
        if success.get("access_token"):
            self._ok = True
        else:
            return

        # 获取未完全成交的订单
        success, error = await self.get_open_orders()
        if error:
            return
        for order_info in success:
            order = self._update_order(order_info)
            if self._order_update_callback:
                asyncio.get_event_loop().create_task(self._order_update_callback(order))

        # 获取持仓
        await self._check_position_update()

        # 授权成功之后，订阅数据
        method = "private/subscribe"
        params = {
            "channels": [
                self._order_channel
            ]
        }
        await self._send_message(method, params)

    async def _do_auth(self, *args, **kwargs):
        """ 鉴权
        """
        method = "public/auth"
        params = {
            "grant_type": "client_credentials",
            "client_id": self._access_key,
            "client_secret": self._secret_key
        }
        success, error = await self._send_message(method, params)
        return success, error

    async def get_server_time(self):
        """ 获取服务器时间
        """
        method = "public/get_time"
        params = {}
        success, error = await self._send_message(method, params)
        return success, error

    async def get_position(self):
        """ 获取当前持仓
        """
        method = "private/get_position"
        params = {"instrument_name": self._symbol}
        success, error = await self._send_message(method, params)
        return success, error

    async def create_order(self, action, price, quantity, order_type=ORDER_TYPE_LIMIT):
        """ 创建订单
        @param action 委托方向 BUY SELL
        @param price 委托价格
        @param quantity 委托数量
        @param order_type 委托类型 limit/market
        """
        if int(quantity) > 0:
            if action == ORDER_ACTION_BUY:
                trade_type = TRADE_TYPE_BUY_OPEN
            else:
                trade_type = TRADE_TYPE_SELL_CLOSE
        else:
            if action == ORDER_ACTION_BUY:
                trade_type = TRADE_TYPE_BUY_CLOSE
            else:
                trade_type = TRADE_TYPE_SELL_OPEN
        quantity = abs(int(quantity))
        if action == ORDER_ACTION_BUY:
            method = "private/buy"
        elif action == ORDER_ACTION_SELL:
            method = "private/sell"
        else:
            logger.error("action error! action:", action, caller=self)
            return None
        if order_type == ORDER_TYPE_LIMIT:
            type_ = "limit"
        else:
            type_ = "market"
        params = {
            "instrument_name": self._symbol,
            "price": price,
            "amount": quantity,
            "type": type_,
            "label": str(trade_type)
        }
        success, error = await self._send_message(method, params)
        if error:
            return None, error
        order_no = success["order"]["order_id"]
        return order_no, None

    async def revoke_order(self, *order_nos):
        """ 撤销订单
        @param order_nos 订单号，如果没有指定订单号，那么撤销所有订单
        * NOTE: 单次调换最多只能撤销100个订单，如果订单超过100个，请多次调用
        """
        # 如果传入order_nos为空，即撤销全部委托单
        if len(order_nos) == 0:
            method = "private/cancel_all_by_instrument"
            params = {"instrument_name": self._symbol}
            success, error = await self._send_message(method, params)
            if error:
                return False, error
            else:
                return True, None

        # 如果传入order_nos为一个委托单号，那么只撤销一个委托单
        if len(order_nos) == 1:
            method = "private/cancel"
            params = {"order_id": order_nos[0]}
            success, error = await self._send_message(method, params)
            if error:
                return order_nos[0], error
            else:
                return order_nos[0], None

        # 如果传入order_nos数量大于1，那么就批量撤销传入的委托单
        if len(order_nos) > 1:
            success, error = [], []
            method = "private/cancel"
            for order_no in order_nos:
                params = {"order_id": order_no}
                r, e = await self._send_message(method, params)
                if e:
                    error.append((order_no, e))
                else:
                    success.append(order_no)
            return success, error

    async def get_order_status(self, order_no):
        """ 获取订单状态
        @param order_no 订单号
        """
        method = "private/get_order_state"
        params = {"order_id": order_no}
        success, error = await self._send_message(method, params)
        return success, error

    async def get_open_orders(self):
        """ 获取未完全成交订单
        """
        method = "private/get_open_orders_by_instrument"
        params = {"instrument_name": self._symbol}
        success, error = await self._send_message(method, params)
        return success, error

    async def _send_message(self, method, params):
        """ 发送消息
        """
        f = asyncio.futures.Future()
        request_id = await self._generate_query_id()
        self._queries[request_id] = f
        data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        await self.ws.send_json(data)
        logger.debug("send message:", data, caller=self)
        success, error = await f
        if error:
            logger.error("data:", data, "error:", error, caller=self)
        return success, error

    @async_method_locker("generate_query_id.locker")
    async def _generate_query_id(self):
        """ 生成query id，加锁，确保每个请求id唯一
        """
        self._query_id += 1
        return self._query_id

    @async_method_locker("process.locker")
    async def process(self, msg):
        """ 处理websocket消息
        """
        logger.debug("msg:", json.dumps(msg), caller=self)

        # 请求消息
        request_id = msg.get("id")
        if request_id:
            f = self._queries.pop(request_id)
            if f.done():
                return
            success = msg.get("result")
            error = msg.get("error")
            f.set_result((success, error))

        # 推送订阅消息
        if msg.get("method") == "subscription":
            if msg["params"]["channel"] == self._order_channel:
                order_info = msg["params"]["data"]
                order = self._update_order(order_info)
                if self._order_update_callback:
                    asyncio.get_event_loop().create_task(self._order_update_callback(copy.copy(order)))

    async def _check_position_update(self, *args, **kwargs):
        """ 定时获取持仓
        """
        if not self._ok:
            return
        update = False
        success, error = await self.get_position()
        if error:
            return
        if not self._position.utime:  # 如果持仓还没有被初始化，那么初始化之后推送一次
            update = True
            self._position.update()
        size = int(success["size"])
        average_price = float(success["average_price"])
        liquid_price = float(success["estimated_liquidation_price"])
        if size > 0:
            if self._position.long_quantity != size:
                update = True
                self._position.update(0, 0, 0, size, average_price, liquid_price)
        elif size < 0:
            if self._position.short_quantity != abs(size):
                update = True
                self._position.update(abs(size), average_price, liquid_price)
        elif size == 0:
            if self._position.long_quantity != 0 or self._position.short_quantity != 0:
                update = True
                self._position.update()
        if update:
            await self._position_update_callback(self._position)

    def _update_order(self, order_info):
        """ 更新订单信息
        @param order_info 订单信息
        """
        order_no = order_info["order_id"]
        quantity = int(order_info["amount"])
        filled_amount = int(order_info["filled_amount"])
        remain = quantity - filled_amount
        average_price = order_info.get("average_price")
        state = order_info["order_state"]
        if state == "open":
            status = ORDER_STATUS_SUBMITTED
            if filled_amount > 0:
                status = ORDER_STATUS_PARTIAL_FILLED
        elif state == "filled":
            status = ORDER_STATUS_FILLED
        elif state == "cancelled":
            status = ORDER_STATUS_CANCELED
        else:
            status = ORDER_STATUS_FAILED

        order = self._orders.get(order_no)
        if not order:
            action = ORDER_ACTION_BUY if order_info["direction"] == "buy" else ORDER_ACTION_SELL
            trade_type = int(order_info.get("label"))
            info = {
                "platform": self._platform,
                "account": self._account,
                "strategy": self._strategy,
                "symbol": self._symbol,
                "order_no": order_no,
                "action": action,
                "price": order_info["price"],
                "quantity": quantity,
                "remain": remain,
                "trade_type": trade_type
            }
            order = Order(**info)
            self._orders[order_no] = order
        order.status = status
        order.remain = remain
        order.avg_price = average_price
        order.ctime = order_info["creation_timestamp"]
        order.utime = order_info["last_update_timestamp"]
        if order.status in [ORDER_STATUS_FILLED, ORDER_STATUS_CANCELED, ORDER_STATUS_FAILED]:
            self._orders.pop(order.order_no)
        return order
