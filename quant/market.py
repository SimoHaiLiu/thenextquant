# -*- coding:utf-8 -*-

"""
行情数据订阅模块

Author: HuangTao
Date:   2019/02/16
Update: None
"""

import asyncio

from quant import const
from quant.utils import logger
from quant.config import config
from quant.utils.agent import Agent


class Market:
    """ 行情数据订阅模块
    """

    ORDERBOOK = "orderbook"
    KLINE = "kline"
    TICKER = "ticker"
    TRADE = "trade"

    def __init__(self):
        url = config.service.get("Market", {}).get("wss", "wss://thenextquant.com/ws/market")
        self._agent = Agent(url, update_callback=self._on_event_market)
        self._callbacks = {}  # 行情订阅回调函数

    def subscribe(self, market_type, platform, symbol, callback):
        """ 订阅行情
        @param market_type 行情类型
        @param platform 交易平台
        @param symbol 交易对
        @param callback 回调函数
        """
        if market_type == self.ORDERBOOK:
            op = const.AGENT_MSG_OPT_SUB_ORDERBOOK
        elif market_type == self.KLINE:
            op = const.AGENT_MSG_OPT_SUB_KLINE
        elif market_type == self.TICKER:
            op = const.AGENT_MSG_OPT_SUB_TICKER
        elif market_type == self.TRADE:
            op = const.AGENT_MSG_OPT_SUB_TRADE
        else:
            logger.error("market type error! market_type:", market_type, caller=self)
            return

        ok = self._set_callback(op, platform, symbol, callback)
        if ok:
            return
        params = {
            "platform": platform,
            "symbol": symbol
        }
        asyncio.get_event_loop().create_task(self._agent.do_request(const.AGENT_MSG_TYPE_MARKET, op, params))

    def unsubscribe(self, market_type, platform, symbol):
        """ 取消订阅行情
        @param market_type 行情类型
        @param platform 交易平台
        @param symbol 交易对
        """
        if market_type == self.ORDERBOOK:
            op = const.AGENT_MSG_OPT_UNSUB_ORDERBOOK
        elif market_type == self.KLINE:
            op = const.AGENT_MSG_OPT_UNSUB_KLINE
        elif market_type == self.TICKER:
            op = const.AGENT_MSG_OPT_UNSUB_TICKER
        elif market_type == self.TRADE:
            op = const.AGENT_MSG_OPT_UNSUB_TRADE
        else:
            logger.error("market type error! market_type:", market_type, caller=self)
            return
        params = {
            "platform": platform,
            "symbol": symbol
        }
        asyncio.get_event_loop().create_task(self._agent.do_request(const.AGENT_MSG_TYPE_MARKET, op, params))

    async def _on_event_market(self, type_, option, data):
        """ 行情数据回调
        @param type_ agent消息类型
        @param option 操作类型
        @param data 返回数据
        """
        callbacks = self._get_callback(option, data["platform"], data["symbol"])
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

    def _generate_callback_key(self, option, platform, symbol):
        key = "{o}_{p}_{s}".format(o=option, p=platform, s=symbol)
        return key
