# -*- coding:utf-8 -*-

"""
服务代理

Author: HuangTao
Date:   2019/02/16
Update: None
"""

import asyncio

from quant import const
from quant.utils import tools
from quant.utils.websocket import Websocket


class Agent(Websocket):
    """ websocket长连接代理
    """

    def __init__(self, wss, proxy=None):
        """ 初始化
        @param wss websocket地址
        @param proxy HTTP代理
        """
        self._queries = {}  # 未完成的请求对象 {"request_id": future}
        self._market_update_callbacks = []  # 行情更新回调函数列表

        super(Agent, self).__init__(wss, proxy)
        self.initialize()

    def register_market_update_callback(self, callback):
        """ 注册行情更新回调
        """
        self._market_update_callbacks.append(callback)

    async def do_request(self, option, params):
        """ 发送请求
        @param option 操作类型
        @param params 请求参数
        """
        request_id = tools.get_uuid1()
        data = {
            "request_id": request_id,
            "option": option,
            "params": params
        }
        await self.ws.send_json(data)
        f = asyncio.futures.Future()
        self._queries[request_id] = f
        result = await f
        if result["code"] == 0:
            return True, result["msg"], result["data"]
        else:
            return False, result["msg"], result["data"]

    async def process(self, msg):
        """ 处理消息
        """
        if msg["option"] == const.AGENT_OPTION_UPDATE:
            if msg["type"] in [const.MARKET_TYPE_ORDERBOOK, const.MARKET_TYPE_TICKER, const.MARKET_TYPE_KLINE,
                               const.MARKET_TYPE_TRADE]:
                for callback in self._market_update_callbacks:
                    await asyncio.get_event_loop().create_task(callback(msg["type"], msg["data"]))
            return
        request_id = msg["request_id"]
        if request_id in self._queries:
            f = self._queries.pop(request_id)
            if f.done():
                return
            f.set_result(msg)
