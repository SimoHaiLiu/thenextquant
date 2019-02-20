# -*- coding:utf-8 -*-

"""
行情数据订阅模块

Author: HuangTao
Date:   2019/02/16
Update: None
"""

import asyncio

from quant.config import config
from quant.utils.agent import Agent


class Market:
    """ 行情数据订阅模块
    """

    def __init__(self):
        url = config.service.get("Market", {}).get("wss", "wss://thenextquant.com/ws/market")
        self._agent = Agent(url)
        self._agent.register_market_update_callback(self.on_event_market)
        self._callbacks = {}  # 行情订阅回调函数

    def subscribe(self, market_type, platform, symbol, callback):
        """ 订阅行情
        @param market_type 行情类型
        @param platform 交易平台
        @param symbol 交易对
        @param callback 回调函数
        """
        ok = self._set_callback(market_type, platform, symbol, callback)
        if ok:
            return
        params = {
            "type": market_type,
            "platform": platform,
            "symbol": symbol
        }
        asyncio.get_event_loop().create_task(self._agent.do_request("subscribe", params))

    def unsubscribe(self, market_type, platform, symbol):
        """ 取消订阅行情
        @param market_type 行情类型
        @param platform 交易平台
        @param symbol 交易对
        """
        params = {
            "type": market_type,
            "platform": platform,
            "symbol": symbol
        }
        asyncio.get_event_loop().create_task(self._agent.do_request("unsubscribe", params))

    async def on_event_market(self, market_type, data):
        """ 行情数据回调
        """
        callbacks = self._get_callback(market_type, data["platform"], data["symbol"])
        for callback in callbacks:
            await asyncio.get_event_loop().create_task(callback(data))

    def _set_callback(self, market_type, platform, symbol, callback):
        """ 设置回调函数
        """
        key = self._generate_callback_key(market_type, platform, symbol)
        if key in self._callbacks:
            self._callbacks[key].append(callback)
            return True
        else:
            self._callbacks[key] = [callback]

    def _get_callback(self, market_type, platform, symbol):
        """ 提取回调函数
        """
        key = self._generate_callback_key(market_type, platform, symbol)
        callbacks = self._callbacks.get(key, [])
        return callbacks

    def _generate_callback_key(self, market_type, platform, symbol):
        key = "{t}_{p}_{s}".format(t=market_type, p=platform, s=symbol)
        return key
