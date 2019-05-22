# -*- coding:utf-8 -*-

"""
OKEx Future Trade module 交易模块
https://www.okex.me/docs/zh/

Author: HuangTao
Date:   2019/01/19
"""

import time
import zlib
import json
import copy
import hmac
import base64
import asyncio
from urllib.parse import urljoin

from quant.order import Order
from quant.utils import tools
from quant.utils import logger
from quant.tasks import SingleTask
from quant.position import Position
from quant.const import OKEX_FUTURE
from quant.utils.websocket import Websocket
from quant.utils.http_client import AsyncHttpRequests
from quant.utils.decorator import async_method_locker
from quant.order import ORDER_ACTION_BUY, ORDER_ACTION_SELL
from quant.order import ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET
from quant.order import ORDER_STATUS_SUBMITTED, ORDER_STATUS_PARTIAL_FILLED, ORDER_STATUS_FILLED, \
    ORDER_STATUS_CANCELED, ORDER_STATUS_FAILED


class OKExFutureRestAPI:
    """ OKEx期货交易 交割合约 REST API 封装
    """

    def __init__(self, host, access_key, secret_key, passphrase):
        """ 初始化
        @param host 请求的host
        @param access_key 请求的access_key
        @param secret_key 请求的secret_key
        @param passphrase API KEY的密码
        """
        self._host = host
        self._access_key = access_key
        self._secret_key = secret_key
        self._passphrase = passphrase

    async def get_user_account(self):
        """ 获取账户信息
        """
        success, error = await self.request("GET", "/api/futures/v3/accounts", auth=True)
        return success, error

    async def get_position(self, instrument_id):
        """ 获取单个合约持仓信息
        @param instrument_id 合约ID，如BTC-USD-180213
        """
        uri = "/api/futures/v3/{instrument_id}/position".format(instrument_id=instrument_id)
        success, error = await self.request("GET", uri, auth=True)
        return success, error

    async def create_order(self, instrument_id, trade_type, price, size, match_price=0, leverage=20):
        """ 下单
        @param instrument_id 合约ID，如BTC-USD-180213
        @param trade_type 交易类型，1 开多 / 2 开空 / 3 平多 / 4 平空
        @param price 每张合约的价格
        @param size 买入或卖出合约的数量（以张计数）
        @param match_price 是否以对手价下单（0 不是 / 1 是），默认为0，当取值为1时。price字段无效
        @param leverage 要设定的杠杆倍数，10或20
        """
        body = {
            "instrument_id": instrument_id,
            "type": str(trade_type),
            "price": price,
            "size": size,
            "match_price": match_price,
            "leverage": leverage
        }
        success, error = await self.request("POST", "/api/futures/v3/order", body=body, auth=True)
        return success, error

    async def revoke_order(self, instrument_id, order_no):
        """ 撤单
        @param instrument_id 合约ID，如BTC-USD-180213
        @param order_id 订单ID
        """
        uri = "/api/futures/v3/cancel_order/{instrument_id}/{order_id}".format(
            instrument_id=instrument_id, order_id=order_no)
        success, error = await self.request("POST", uri, auth=True)
        if error:
            return None, error
        if not success["result"]:
            return None, success
        return success, None

    async def revoke_orders(self, instrument_id, order_ids):
        """ 批量撤单
        @param instrument_id 合约ID，如BTC-USD-180213
        @param order_ids 订单id列表
        """
        assert isinstance(order_ids, list)
        uri = "/api/futures/v3/cancel_batch_orders/{instrument_id}".format(instrument_id=instrument_id)
        body = {
            "order_ids": order_ids
        }
        success, error = await self.request("POST", uri, body=body, auth=True)
        if error:
            return None, error
        if not success["result"]:
            return None, success
        return success, None

    async def get_order_info(self, instrument_id, order_id):
        """ 获取订单信息
        @param instrument_id 合约ID，如BTC-USD-180213
        @param order_id 订单ID
        """
        uri = "/api/futures/v3/orders/{instrument_id}/{order_id}".format(
            instrument_id=instrument_id, order_id=order_id)
        success, error = await self.request("GET", uri, auth=True)
        return success, error

    async def get_order_list(self, instrument_id, status, _from=1, to=100, limit=100):
        """ 获取订单列表
        @param instrument_id 合约ID，如BTC-USD-180213
        @param status Order Status 订单状态("-2":失败,"-1":撤单成功,"0":等待成交 ,"1":部分成交, "2":完全成交,"3":下单中,"4":撤单中,"6": 未完成（等待成交+部分成交），"7":已完成（撤单成功+完全成交））
        @param _from Request paging content for this page number.（Example: 1,2,3,4,5. From 4 we only have 4, to 4 we only have 3）
        @param to Request page after (older) this pagination id. （Example: 1,2,3,4,5. From 4 we only have 4, to 4 we only have 3）
        @param limit Number of results per request. Maximum 100. (default 100)
        """
        uri = "/api/futures/v3/orders/{instrument_id}".format(instrument_id=instrument_id)
        params = {
            "status": status,
            "from": _from,
            "to": to,
            "limit": limit
        }
        success, error = await self.request("GET", uri, params=params, auth=True)
        return success, error

    async def request(self, method, uri, params=None, body=None, headers=None, auth=False):
        """ 发起请求
        @param method 请求方法 GET / POST / DELETE / PUT
        @param uri 请求uri
        @param params dict 请求query参数
        @param body dict 请求body数据
        @param headers 请求http头
        @param auth boolean 是否需要加入权限校验
        """
        if params:
            query = "&".join(["{}={}".format(k, params[k]) for k in sorted(params.keys())])
            uri += "?" + query
        url = urljoin(self._host, uri)

        # 增加签名
        if auth:
            timestamp = str(time.time()).split(".")[0] + "." + str(time.time()).split(".")[1][:3]
            if body:
                body = json.dumps(body)
            else:
                body = ""
            message = str(timestamp) + str.upper(method) + uri + str(body)
            mac = hmac.new(bytes(self._secret_key, encoding="utf8"), bytes(message, encoding="utf-8"),
                           digestmod="sha256")
            d = mac.digest()
            sign = base64.b64encode(d)

            if not headers:
                headers = {}
            headers["Content-Type"] = "application/json"
            headers["OK-ACCESS-KEY"] = self._access_key.encode().decode()
            headers["OK-ACCESS-SIGN"] = sign.decode()
            headers["OK-ACCESS-TIMESTAMP"] = str(timestamp)
            headers["OK-ACCESS-PASSPHRASE"] = self._passphrase

        _, success, error = await AsyncHttpRequests.fetch(method, url, body=body, headers=headers, timeout=10)
        return success, error


class OKExFutureTrade(Websocket):
    """ OKEX Future websocket
    """

    def __init__(self, account, strategy, symbol, host=None, wss=None, access_key=None, secret_key=None,
                 passphrase=None, order_update_callback=None, position_update_callback=None):
        """ 初始化
        @param account 账户
        @param strategy 策略名称
        @param symbol 交易对（合约名称）
        @param host HTTP请求主机地址
        @param wss websocket连接地址
        @param access_key ACCESS KEY
        @param secret_key SECRET KEY
        @param passphrase 密码
        @param order_update_callback 订单更新回调
        @param position_update_callback 持仓更新回调
        """
        self._account = account
        self._strategy = strategy
        self._platform = OKEX_FUTURE
        self._symbol = symbol
        self._host = host
        self._wss = wss
        self._access_key = access_key
        self._secret_key = secret_key
        self._passphrase = passphrase

        self._order_update_callback = order_update_callback
        self._position_update_callback = position_update_callback

        super(OKExFutureTrade, self).__init__(self._wss, send_hb_interval=5)
        self.heartbeat_msg = "ping"

        self._orders = {}  # 订单
        self._position = Position(self._platform, self._account, strategy, symbol)  # 仓位

        # 初始化 REST API 对象
        self._rest_api = OKExFutureRestAPI(self._host, self._access_key, self._secret_key, self._passphrase)

        self.initialize()

    @property
    def position(self):
        return copy.copy(self._position)

    @property
    def orders(self):
        return copy.copy(self._orders)

    async def connected_callback(self):
        """ 建立连接之后，授权登陆，然后订阅order和position
        """
        # 身份验证
        timestamp = str(time.time()).split(".")[0] + "." + str(time.time()).split(".")[1][:3]
        message = str(timestamp) + "GET" + "/users/self/verify"
        mac = hmac.new(bytes(self._secret_key, encoding="utf8"), bytes(message, encoding="utf8"), digestmod="sha256")
        d = mac.digest()
        signature = base64.b64encode(d).decode()
        data = {
            "op": "login",
            "args": [self._access_key, self._passphrase, timestamp, signature]
        }
        await self.ws.send_json(data)

        # 获取当前等待成交和部分成交的订单信息
        result, error = await self._rest_api.get_order_list(self._symbol, 6)
        if error:
            return
        for order_info in result["order_info"]:
            order = self._update_order(order_info)
            if self._order_update_callback:
                SingleTask.run(self._order_update_callback, order)

        # 获取当前持仓
        position, error = await self._rest_api.get_position(self._symbol)
        if error:
            return
        if len(position["holding"]) > 0:
            self._update_position(position["holding"][0])
        if self._position_update_callback:
            SingleTask.run(self._position_update_callback, self.position)

    @async_method_locker("process_binary.locker")
    async def process_binary(self, raw):
        """ 处理websocket上接收到的消息
        @param raw 原始的压缩数据
        """
        decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        msg = decompress.decompress(raw)
        msg += decompress.flush()
        msg = msg.decode()
        if msg == "pong":  # 心跳返回
            return
        msg = json.loads(msg)
        # logger.debug("msg:", msg, caller=self)

        # 登陆成功之后再订阅数据
        if msg.get("event") == "login":
            if not msg.get("success"):
                logger.error("websocket login error!", caller=self)
                return
            logger.info("Websocket connection authorized successfully.", caller=self)

            # 订阅account, order, position
            ch_account = "futures/account:BTC"
            ch_order = "futures/order:{symbol}".format(symbol=self._symbol)
            ch_position = "futures/position:{symbol}".format(symbol=self._symbol)
            data = {
                "op": "subscribe",
                "args": [ch_account, ch_order, ch_position]
            }
            await self.ws.send_json(data)
            logger.info("subscribe account/order/position successfully.", caller=self)
            return

        table = msg.get("table")
        if table not in ["futures/order", "futures/position"]:
            return

        for data in msg["data"]:
            if table == "futures/order":
                order = self._update_order(data)
                if self._order_update_callback:
                    await asyncio.get_event_loop().create_task(self._order_update_callback(order))

            elif table == "futures/position":
                self._update_position(data)
                if self._position_update_callback:
                    await asyncio.get_event_loop().create_task(self._position_update_callback(self.position))

    async def create_order(self, action, price, quantity, order_type=ORDER_TYPE_LIMIT):
        """ 创建订单
        @param action 交易方向 BUY/SELL
        @param price 委托价格
        @param quantity 委托数量(可以是正数，也可以是复数)
        @param order_type 委托类型 limit/market
        """
        if int(quantity) > 0:
            if action == ORDER_ACTION_BUY:
                trade_type = "1"
            else:
                trade_type = "3"
        else:
            if action == ORDER_ACTION_BUY:
                trade_type = "4"
            else:
                trade_type = "2"
        quantity = abs(int(quantity))
        result, error = await self._rest_api.create_order(self._symbol, trade_type, price, quantity)
        if error:
            return None, error
        return result["order_id"], None

    async def revoke_order(self, *order_nos):
        """ 撤销订单
        @param order_nos 订单号，可传入任意多个，如果不传入，那么就撤销所有订单
        * NOTE: 单次调用最多只能撤销100个订单，如果订单超过100个，请多次调用
        """
        # 如果传入order_nos为空，即撤销全部委托单
        if len(order_nos) == 0:
            result, error = await self._rest_api.get_order_list(self._symbol, 6)
            if error:
                return False, error
            for order_info in result["order_info"]:
                order_no = order_info["order_id"]
                _, error = await self._rest_api.revoke_order(self._symbol, order_no)
                if error:
                    return False, error
            return True, None

        # 如果传入order_nos为一个委托单号，那么只撤销一个委托单
        if len(order_nos) == 1:
            success, error = await self._rest_api.revoke_order(self._symbol, order_nos[0])
            if error:
                return order_nos[0], error
            else:
                return order_nos[0], None

        # 如果传入order_nos数量大于1，那么就批量撤销传入的委托单
        if len(order_nos) > 1:
            success, error = [], []
            for order_no in order_nos:
                _, e = await self._rest_api.revoke_order(self._symbol, order_no)
                if e:
                    error.append((order_no, e))
                else:
                    success.append(order_no)
            return success, error

    async def get_open_order_nos(self):
        """ 获取未完全成交订单号列表
        """
        success, error = await self._rest_api.get_order_list(self._symbol, 6)
        if error:
            return None, error
        else:
            order_nos = []
            for order_info in success["order_info"]:
                order_nos.append(order_info["order_id"])
            return order_nos, None

    def _update_order(self, order_info):
        """ 更新订单信息
        @param order_info 订单信息
        """
        order_no = str(order_info["order_id"])
        state = order_info["state"]
        remain = int(order_info["size"]) - int(order_info["filled_qty"])
        ctime = tools.utctime_str_to_mts(order_info["timestamp"])
        if state == "-2":
            status = ORDER_STATUS_FAILED
        elif state == "-1":
            status = ORDER_STATUS_CANCELED
        elif state == "0":
            status = ORDER_STATUS_SUBMITTED
        elif state == "1":
            status = ORDER_STATUS_PARTIAL_FILLED
        elif state == "2":
            status = ORDER_STATUS_FILLED
        else:
            return None

        order = self._orders.get(order_no)
        if not order:
            info = {
                "platform": self._platform,
                "account": self._account,
                "strategy": self._strategy,
                "order_no": order_no,
                "action": ORDER_ACTION_BUY if order_info["type"] in ["1", "4"] else ORDER_ACTION_SELL,
                "symbol": self._symbol,
                "price": order_info["price"],
                "quantity": order_info["size"],
                "trade_type": int(order_info["type"])
            }
            order = Order(**info)
        order.remain = remain
        order.status = status
        order.avg_price = order_info["price_avg"]
        order.ctime = ctime
        order.utime = ctime
        self._orders[order_no] = order
        if state in ["-1", "2"]:
            self._orders.pop(order_no)
        return order

    def _update_position(self, position_info):
        """ 更新持仓信息
        @param position_info 持仓信息
        """
        self._position.long_quantity = int(position_info["long_qty"])
        self._position.long_avg_price = position_info["long_avg_cost"]
        self._position.short_quantity = int(position_info["short_qty"])
        self._position.short_avg_price = position_info["short_avg_cost"]
        self._position.liquid_price = position_info["liquidation_price"]
        self._position.utime = tools.utctime_str_to_mts(position_info["updated_at"])
