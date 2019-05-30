# -*- coding:utf-8 -*-

"""
Binance Trade 模块
https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md

Author: HuangTao
Date:   2018/08/09
"""

import json
import copy
import hmac
import hashlib
from urllib.parse import urljoin

from quant.utils import tools
from quant.utils import logger
from quant.const import BINANCE
from quant.order import Order
from quant.utils.websocket import Websocket
from quant.tasks import SingleTask, LoopRunTask
from quant.utils.http_client import AsyncHttpRequests
from quant.utils.decorator import async_method_locker
from quant.order import ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET
from quant.order import ORDER_STATUS_SUBMITTED, ORDER_STATUS_PARTIAL_FILLED, ORDER_STATUS_FILLED, \
    ORDER_STATUS_CANCELED, ORDER_STATUS_FAILED


__all__ = ("BinanceRestAPI", )


class BinanceRestAPI:
    """ Binance REST API 封装
    """

    def __init__(self, host, access_key, secret_key):
        """ 初始化
        @param host 请求的host
        @param access_key 请求的access_key
        @param secret_key 请求的secret_key
        """
        self._host = host
        self._access_key = access_key
        self._secret_key = secret_key

    async def get_user_account(self):
        """ 获取账户信息
        """
        ts = tools.get_cur_timestamp_ms()
        params = {
            "timestamp": str(ts)
        }
        success, error = await self.request("GET", "/api/v3/account", params, auth=True)
        return success, error

    async def get_server_time(self):
        """ 获取服务器时间
        """
        success, error = await self.request("GET", "/api/v1/time")
        return success, error

    async def get_exchange_info(self):
        """ 获取交易所信息
        """
        success, error = await self.request("GET", "/api/v1/exchangeInfo")
        return success, error

    async def get_latest_ticker(self, symbol):
        """ 获取交易对实时ticker行情
        """
        params = {
            "symbol": symbol
        }
        success, error = await self.request("GET", "/api/v1/ticker/24hr", params=params)
        return success, error

    async def get_orderbook(self, symbol, limit=10):
        """ 获取订单薄数据
        @param symbol 交易对
        @param limit 订单薄的档位数，默认为10，可选 5, 10, 20, 50, 100, 500, 1000
        """
        params = {
            "symbol": symbol,
            "limit": limit
        }
        success, error = await self.request("GET", "/api/v1/depth", params=params)
        return success, error

    async def create_order(self, action, symbol, price, quantity):
        """ 创建订单
        @param action 操作类型 BUY SELL
        @param symbol 交易对
        @param quantity 交易量
        @param price 交易价格
        * NOTE: 仅实现了限价单
        """
        info = {
            "symbol": symbol,
            "side": action,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": quantity,
            "price": price,
            "recvWindow": "5000",
            "newOrderRespType": "FULL",
            "timestamp": tools.get_cur_timestamp_ms()
        }
        success, error = await self.request("POST", "/api/v3/order", body=info, auth=True)
        return success, error

    async def revoke_order(self, symbol, order_id, client_order_id):
        """ 撤销订单
        @param symbol 交易对
        @param order_id 订单id
        @param client_order_id 创建订单返回的客户端信息
        """
        params = {
            "symbol": symbol,
            "orderId": str(order_id),
            "origClientOrderId": client_order_id,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        success, error = await self.request("DELETE", "/api/v3/order", params=params, auth=True)
        return success, error

    async def get_order_status(self, symbol, order_id, client_order_id):
        """ 获取订单的状态
        @param symbol 交易对
        @param order_id 订单id
        @param client_order_id 创建订单返回的客户端信息
        """
        params = {
            "symbol": symbol,
            "orderId": str(order_id),
            "origClientOrderId": client_order_id,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        success, error = await self.request("GET", "/api/v3/order", params=params, auth=True)
        return success, error

    async def get_all_orders(self, symbol):
        """ 获取所有订单信息
        @param symbol 交易对
        """
        params = {
            "symbol": symbol,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        success, error = await self.request("GET", "/api/v3/allOrders", params=params, auth=True)
        return success, error

    async def get_open_orders(self, symbol):
        """ 获取当前还未完全成交的订单信息
        @param symbol 交易对
        """
        params = {
            "symbol": symbol,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        success, error = await self.request("GET", "/api/v3/openOrders", params=params, auth=True)
        return success, error

    async def get_listen_key(self):
        """ 获取一个新的用户数据流key
        @return listen_key string wss监听用户数据的key
        """
        success, error = await self.request("POST", "/api/v1/userDataStream")
        return success, error

    async def put_listen_key(self, listen_key):
        """ 保持listen key连接
        @param listen_key string wss监听用户数据的key
        """
        params = {
            "listenKey": listen_key
        }
        success, error = await self.request("PUT", "/api/v1/userDataStream", params=params)
        return success, error

    async def delete_listen_key(self, listen_key):
        """ 删除一个listen key
        @param listen_key string wss监听用户数据的key
        """
        params = {
            "listenKey": listen_key
        }
        success, error = await self.request("DELETE", "/api/v1/userDataStream", params=params)
        return success, error

    async def request(self, method, uri, params=None, body=None, headers=None, auth=False):
        """ 发起请求
        @param method 请求方法 GET POST DELETE PUT
        @param uri 请求uri
        @param params dict 请求query参数
        @param body dict 请求body数据
        @param headers 请求http头
        @param auth boolean 是否需要加入权限校验
        """
        url = urljoin(self._host, uri)
        data = {}
        if params:
            data.update(params)
        if body:
            data.update(body)

        if data:
            query = "&".join(["=".join([str(k), str(v)]) for k, v in data.items()])
        else:
            query = ""
        if auth and query:
            signature = hmac.new(self._secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
            query += "&signature={s}".format(s=signature)
        if query:
            url += ("?" + query)

        if not headers:
            headers = {}
        headers["X-MBX-APIKEY"] = self._access_key
        _, success, error = await AsyncHttpRequests.fetch(method, url, headers=headers, timeout=10, verify_ssl=False)
        return success, error


class BinanceTrade(Websocket):
    """ binance用户数据流
    """

    def __init__(self, account, strategy, symbol, host=None, wss=None, access_key=None, secret_key=None,
                 order_update_callback=None):
        """ 初始化
        @param account 账户
        @param strategy 策略名称
        @param symbol 交易对（合约名称）
        @param host HTTP请求主机地址
        @param wss websocket连接地址
        @param access_key ACCESS KEY
        @param secret_key SECRET KEY
        @param order_update_callback 订单更新回调
        """
        self._account = account
        self._strategy = strategy
        self._platform = BINANCE
        self._symbol = symbol
        self._raw_symbol = symbol.replace("/", "")
        self._host = host if host else "https://api.binance.com"
        self._wss = wss if wss else "wss://stream.binance.com:9443"
        self._access_key = access_key
        self._secret_key = secret_key
        self._order_update_callback = order_update_callback

        super(BinanceTrade, self).__init__(self._wss)

        self._listen_key = None # websocket连接鉴权使用
        self._orders = {}  # 订单

        # 初始化 REST API 对象
        self._rest_api = BinanceRestAPI(self._host, self._access_key, self._secret_key)

        # 30分钟重置一下listen key
        LoopRunTask.register(self._reset_listen_key, 60 * 30)
        # 获取listen key
        SingleTask.run(self._init_websocket)

    @property
    def orders(self):
        return copy.copy(self._orders)

    async def _init_websocket(self):
        """ 初始化websocket
        """
        # 获取listen key
        success, error = await self._rest_api.get_listen_key()
        if error:
            logger.error("get listen key error:", error, caller=self)
            return
        self._listen_key = success["listenKey"]
        uri = "/ws/" + self._listen_key
        self._url = urljoin(self._wss, uri)
        self.initialize()

    async def _reset_listen_key(self, *args, **kwargs):
        """ 重置listen key
        """
        if not self._listen_key:
            logger.error("listen key not initialized!", caller=self)
            return
        await self._rest_api.put_listen_key(self._listen_key)
        logger.info("reset listen key success!", caller=self)

    async def connected_callback(self):
        """ 建立连接之后，获取当前所有未完全成交的订单
        """
        order_infos, error = await self._rest_api.get_open_orders(self._raw_symbol)
        if error:
            return
        for order_info in order_infos:
            order_no = "{}_{}".format(order_info["orderId"], order_info["clientOrderId"])
            if order_info["status"] == "NEW":  # 部分成交
                status = ORDER_STATUS_SUBMITTED
            elif order_info["status"] == "PARTIALLY_FILLED":  # 部分成交
                status = ORDER_STATUS_PARTIAL_FILLED
            elif order_info["status"] == "FILLED":  # 完全成交
                status = ORDER_STATUS_FILLED
            elif order_info["status"] == "CANCELED":  # 取消
                status = ORDER_STATUS_CANCELED
            elif order_info["status"] == "REJECTED":  # 拒绝
                status = ORDER_STATUS_FAILED
            elif order_info["status"] == "EXPIRED":  # 过期
                status = ORDER_STATUS_FAILED
            else:
                logger.warn("unknown status:", order_info, caller=self)
                return

            info = {
                "platform": self._platform,
                "account": self._account,
                "strategy": self._strategy,
                "order_no": order_no,
                "action": order_info["side"],
                "order_type": order_info["type"],
                "symbol": self._symbol,
                "price": order_info["price"],
                "quantity": order_info["origQty"],
                "remain": float(order_info["origQty"]) - float(order_info["executedQty"]),
                "status": status,
                "ctime": order_info["time"],
                "utime": order_info["updateTime"]
            }
            order = Order(**info)
            self._orders[order_no] = order
            if self._order_update_callback:
                SingleTask.run(self._order_update_callback, order)

    async def create_order(self, action, price, quantity, order_type=ORDER_TYPE_LIMIT):
        """ 创建订单
        @param action 交易方向 BUY/SELL
        @param price 委托价格
        @param quantity 委托数量
        @param order_type 委托类型 LIMIT / MARKET
        """
        price = tools.float_to_str(price)
        quantity = tools.float_to_str(quantity)
        result, error = await self._rest_api.create_order(action, self._raw_symbol, price, quantity)
        if error:
            return None, error
        order_no = "{}_{}".format(result["orderId"], result["clientOrderId"])
        return order_no, None

    async def revoke_order(self, *order_nos):
        """ 撤销订单
        @param order_nos 订单号列表，可传入任意多个，如果不传入，那么就撤销所有订单
        """
        # 如果传入order_nos为空，即撤销全部委托单
        if len(order_nos) == 0:
            order_infos, error = await self._rest_api.get_open_orders(self._raw_symbol)
            if error:
                return False, error
            for order_info in order_infos:
                _, error = await self._rest_api.revoke_order(self._raw_symbol, order_info["orderId"],
                                                             order_info["clientOrderId"])
                if error:
                    return False, error
            return True, None

        # 如果传入order_nos为一个委托单号，那么只撤销一个委托单
        if len(order_nos) == 1:
            order_id, client_order_id = order_nos[0].split("_")
            success, error = await self._rest_api.revoke_order(self._raw_symbol, order_id, client_order_id)
            if error:
                return order_nos[0], error
            else:
                return order_nos[0], None

        # 如果传入order_nos数量大于1，那么就批量撤销传入的委托单
        if len(order_nos) > 1:
            success, error = [], []
            for order_no in order_nos:
                order_id, client_order_id = order_no.split("_")
                _, e = await self._rest_api.revoke_order(self._raw_symbol, order_id, client_order_id)
                if e:
                    error.append((order_no, e))
                else:
                    success.append(order_no)
            return success, error

    async def get_open_order_nos(self):
        """ 获取未完全成交订单号列表
        """
        success, error = await self._rest_api.get_open_orders(self._raw_symbol)
        if error:
            return None, error
        else:
            order_nos = []
            for order_info in success:
                order_no = "{}_{}".format(order_info["orderId"], order_info["clientOrderId"])
                order_nos.append(order_no)
            return order_nos, None

    @async_method_locker("process.locker")
    async def process(self, msg):
        """ 处理websocket上接收到的消息
        """
        logger.debug("msg:", json.dumps(msg), caller=self)
        e = msg.get("e")
        if e == "executionReport":  # 订单更新
            order_no = "{}_{}".format(msg["i"], msg["c"])
            if msg["X"] == "NEW":  # 部分成交
                status = ORDER_STATUS_SUBMITTED
            elif msg["X"] == "PARTIALLY_FILLED":  # 部分成交
                status = ORDER_STATUS_PARTIAL_FILLED
            elif msg["X"] == "FILLED":  # 完全成交
                status = ORDER_STATUS_FILLED
            elif msg["X"] == "CANCELED":  # 取消
                status = ORDER_STATUS_CANCELED
            elif msg["X"] == "REJECTED":  # 拒绝
                status = ORDER_STATUS_FAILED
            elif msg["X"] == "EXPIRED":  # 过期
                status = ORDER_STATUS_FAILED
            else:
                logger.warn("unknown status:", msg, caller=self)
                return
            order = self._orders.get(order_no)
            if not order:
                info = {
                    "platform": self._platform,
                    "account": self._account,
                    "strategy": self._strategy,
                    "order_no": order_no,
                    "action": msg["S"],
                    "order_type": msg["o"],
                    "symbol": self._symbol,
                    "price": msg["p"],
                    "quantity": msg["q"],
                    "ctime": msg["O"]
                }
                order = Order(**info)
                self._orders[order_no] = order
            order.remain = float(msg["q"]) - float(msg["z"])
            order.status = status
            order.utime = msg["T"]
            if self._order_update_callback:
                SingleTask.run(self._order_update_callback, order)
        # elif e == "outboundAccountInfo": # 账户资产更新
        #     for func in self._account_update_cb_funcs:
        #         asyncio.get_event_loop().create_task(func(msg))
