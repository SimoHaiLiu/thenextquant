# -*- coding:utf-8 -*-

"""
OKEx现货交易 Trade 模块
https://www.okex.com/docs/zh/

Author: HuangTao
Date:   2019/01/19
"""

import time
import json
import copy
import hmac
import zlib
import base64
from urllib.parse import urljoin

from quant.utils import tools
from quant.utils import logger
from quant.const import OKEX
from quant.order import Order
from quant.tasks import SingleTask
from quant.utils.websocket import Websocket
from quant.utils.decorator import async_method_locker
from quant.utils.http_client import AsyncHttpRequests
from quant.order import ORDER_ACTION_BUY, ORDER_ACTION_SELL
from quant.order import ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET
from quant.order import ORDER_STATUS_SUBMITTED, ORDER_STATUS_PARTIAL_FILLED, ORDER_STATUS_FILLED, \
    ORDER_STATUS_CANCELED, ORDER_STATUS_FAILED


__all__ = ("OKExRestAPI", "OKExTrade", )


class OKExRestAPI:
    """ OKEx现货交易 REST API 封装
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
        result, error = await self.request("GET", "/api/spot/v3/accounts", auth=True)
        return result, error

    async def create_order(self, action, symbol, price, quantity, order_type=ORDER_TYPE_LIMIT):
        """ 创建订单
        @param action 操作类型 BUY SELL
        @param symbol 交易对
        @param quantity 交易量
        @param price 交易价格
        @param order_type 订单类型 市价 / 限价
        """
        info = {
            "side": "buy" if action == ORDER_ACTION_BUY else "sell",
            "instrument_id": symbol,
            "margin_trading": 1
        }
        if order_type == ORDER_TYPE_LIMIT:
            info["type"] = "limit"
            info["price"] = price
            info["size"] = quantity
        elif order_type == ORDER_TYPE_MARKET:
            info["type"] = "market"
            if action == ORDER_ACTION_BUY:
                info["notional"] = quantity  # 买入金额，市价买入是必填notional
            else:
                info["size"] = quantity  # 卖出数量，市价卖出时必填size
        else:
            logger.error("order_type error! order_type:", order_type, caller=self)
            return None
        result, error = await self.request("POST", "/api/spot/v3/orders", body=info, auth=True)
        return result, error

    async def revoke_order(self, symbol, order_no):
        """ 撤销委托单
        @param symbol 交易对
        @param order_no 订单id
        """
        body = {
            "instrument_id": symbol
        }
        uri = "/api/spot/v3/cancel_orders/{order_no}".format(order_no=order_no)
        result, error = await self.request("POST", uri, body=body, auth=True)
        if error:
            return order_no, error
        if result["result"]:
            return order_no, None
        return order_no, result

    async def revoke_orders(self, symbol, order_nos):
        """ 批量撤销委托单
        @param symbol 交易对
        @param order_nos 订单列表
        * NOTE: 单次不超过4个订单id
        """
        if len(order_nos) > 4:
            logger.warn("only revoke 4 orders per request!", caller=self)
        body = [
            {
                "instrument_id": symbol,
                "order_ids": order_nos[:4]
            }
        ]
        result, error = await self.request("POST", "/api/spot/v3/cancel_batch_orders", body=body, auth=True)
        return result, error

    async def get_open_orders(self, symbol):
        """ 获取当前还未完全成交的订单信息
        @param symbol 交易对
        * NOTE: 查询上限最多100个订单
        """
        params = {
            "instrument_id": symbol
        }
        result, error = await self.request("GET", "/api/spot/v3/orders_pending", params=params, auth=True)
        return result, error

    async def get_order_status(self, symbol, order_no):
        """ 获取订单的状态
        @param symbol 交易对
        @param order_no 订单id
        """
        params = {
            "instrument_id": symbol
        }
        uri = "/api/spot/v3/orders/{order_no}".format(order_no=order_no)
        result, error = await self.request("GET", uri, params=params, auth=True)
        return result, error

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


class OKExTrade(Websocket):
    """ OKEX Trade模块
    """

    def __init__(self, account, strategy, symbol, host=None, wss=None, access_key=None, secret_key=None,
                 passphrase=None, order_update_callback=None):
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
        """
        self._account = account
        self._strategy = strategy
        self._platform = OKEX
        self._symbol = symbol
        self._host = host if host else "https://www.okex.com"
        self._wss = wss if wss else "wss://real.okex.com:10442/ws/v3"
        self._access_key = access_key
        self._secret_key = secret_key
        self._passphrase = passphrase
        self._order_update_callback = order_update_callback

        self._raw_symbol = symbol.replace("/", "-")  # 转换成交易所对应的交易对格式

        super(OKExTrade, self).__init__(self._wss, send_hb_interval=5)
        self.heartbeat_msg = "ping"

        self._orders = {}  # 订单

        # 初始化 REST API 对象
        self._rest_api = OKExRestAPI(self._host, self._access_key, self._secret_key, self._passphrase)

        self.initialize()

    @property
    def orders(self):
        return copy.copy(self._orders)

    async def connected_callback(self):
        """ 建立连接之后，授权登陆，然后订阅order和position
        """
        # 身份验证
        timestamp = str(time.time()).split('.')[0] + '.' + str(time.time()).split('.')[1][:3]
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
        order_infos, error = await self._rest_api.get_open_orders(self._raw_symbol)
        if error:
            return
        for order_info in order_infos:
            order_info["ctime"] = order_info["created_at"]
            order_info["utime"] = order_info["timestamp"]
            order = self._update_order(order_info)
            if self._order_update_callback:
                SingleTask.run(self._order_update_callback, order)

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
        logger.debug('msg:', msg, caller=self)

        # 登陆成功之后再订阅数据
        if msg.get("event") == "login":
            if not msg.get("success"):
                logger.error("websocket login error!", caller=self)
                return
            logger.info("Websocket connection authorized successfully.", caller=self)

            # 订阅 order
            ch_order = "spot/order:{symbol}".format(symbol=self._raw_symbol)
            data = {
                "op": "subscribe",
                "args": [ch_order]
            }
            await self.ws.send_json(data)
            logger.info("subscribe order successfully.", caller=self)
            return

        table = msg.get("table")
        if table not in ["spot/order", ]:
            return

        for data in msg["data"]:
            if table == "spot/order":
                data["ctime"] = data["timestamp"]
                data["utime"] = data["last_fill_time"]
                order = self._update_order(data)
                if order and self._order_update_callback:
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
        result, error = await self._rest_api.create_order(action, self._raw_symbol, price, quantity, order_type)
        if error:
            return None, error
        if not result["result"]:
            return None, result
        return result["order_id"], None

    async def revoke_order(self, *order_nos):
        """ 撤销订单
        @param order_nos 订单号列表，可传入任意多个，如果不传入，那么就撤销所有订单
        * NOTE: 单次调用最多只能撤销4个订单，如果订单超过4个，请多次调用
        """
        # 如果传入order_nos为空，即撤销全部委托单
        if len(order_nos) == 0:
            order_infos, error = await self._rest_api.get_open_orders(self._raw_symbol)
            if error:
                return False, error
            for order_info in order_infos:
                order_no = order_info["order_id"]
                _, error = await self._rest_api.revoke_order(self._raw_symbol, order_no)
                if error:
                    return False, error
            return True, None

        # 如果传入order_nos为一个委托单号，那么只撤销一个委托单
        if len(order_nos) == 1:
            success, error = await self._rest_api.revoke_order(self._raw_symbol, order_nos[0])
            if error:
                return order_nos[0], error
            else:
                return order_nos[0], None

        # 如果传入order_nos数量大于1，那么就批量撤销传入的委托单
        if len(order_nos) > 1:
            success, error = [], []
            for order_no in order_nos:
                _, e = await self._rest_api.revoke_order(self._raw_symbol, order_no)
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
                order_nos.append(order_info["order_id"])
            return order_nos, None

    def _update_order(self, order_info):
        """ 更新订单信息
        @param order_info 订单信息
        """
        order_no = str(order_info["order_id"])
        state = order_info["state"]
        remain = float(order_info["size"]) - float(order_info["filled_size"])
        ctime = tools.utctime_str_to_mts(order_info["ctime"])
        utime = tools.utctime_str_to_mts(order_info["utime"])

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
            logger.error("status error! order_info:", order_info, caller=self)
            return None

        order = self._orders.get(order_no)
        if order:
            order.remain = remain
            order.status = status
            order.price = order_info["price"]
        else:
            info = {
                "platform": self._platform,
                "account": self._account,
                "strategy": self._strategy,
                "order_no": order_no,
                "action": ORDER_ACTION_BUY if order_info["side"] == "buy" else ORDER_ACTION_SELL,
                "symbol": self._symbol,
                "price": order_info["price"],
                "quantity": order_info["size"],
                "remain": remain,
                "status": status,
                "avg_price": order_info["price"]
            }
            order = Order(**info)
            self._orders[order_no] = order
        order.ctime = ctime
        order.utime = utime
        if status in [ORDER_STATUS_FAILED, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED]:
            self._orders.pop(order_no)
        return order
