# -*- coding:utf-8 -*-

"""
服务代理

Author: HuangTao
Date:   2019/02/16
"""

import asyncio

from quant.utils import tools
from quant.utils.websocket import Websocket


class Agent(Websocket):
    """ websocket长连接代理
    """

    def __init__(self, wss, proxy=None, connected_callback=None, update_callback=None):
        """ 初始化
        @param wss websocket地址
        @param proxy HTTP代理
        @param connected_callback websocket连接建立成功回调
        @param update_callback websocket数据更新回调
        """
        self._connected_callback = connected_callback
        self._update_callback = update_callback
        self._queries = {}  # 未完成的请求对象 {"request_id": future}

        super(Agent, self).__init__(wss, proxy)
        self.initialize()

    async def connected_callback(self):
        """ websocket连接建立成功回调
        """
        if self._connected_callback:
            await asyncio.sleep(0.1)  # 延迟0.1秒执行回调，等待初始化函数完成准备工作
            await self._connected_callback()

    async def do_request(self, option, params):
        """ 发送请求
        @param option 操作类型
        @param params 请求参数
        """
        request_id = tools.get_uuid1()
        data = {
            "id": request_id,
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
        request_id = msg.get("id")
        if request_id in self._queries:
            f = self._queries.pop(request_id)
            if f.done():
                return
            f.set_result(msg)
        else:
            if self._update_callback:
                asyncio.get_event_loop().create_task(self._update_callback(msg["option"], msg["data"]))
