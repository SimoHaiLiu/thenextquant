# -*- coding:utf-8 -*-

"""
行情数据订阅模块

Author: HuangTao
Date:   2019/02/16
"""

import json

from quant import const


class Orderbook:
    """ 订单薄
    """

    def __init__(self, platform=None, symbol=None, asks=None, bids=None, timestamp=None):
        """ 初始化
        @param platform 交易平台
        @param symbol 交易对
        @param asks 买盘数据 [[price, quantity], [...], ...]
        @param bids 卖盘数据 [[price, quantity], [...], ...]
        @param timestamp 时间戳(毫秒)
        """
        self.platform = platform
        self.symbol = symbol
        self.asks = asks
        self.bids = bids
        self.timestamp = timestamp

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "asks": self.asks,
            "bids": self.bids,
            "timestamp": self.timestamp
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Trade:
    """ 交易数据
    """

    def __init__(self, platform=None, symbol=None, action=None, price=None, quantity=None, timestamp=None):
        """ 初始化
        @param platform 交易平台
        @param symbol 交易对
        @param action 操作 BUY / SELL
        @param price 价格
        @param quantity 数量
        @param timestamp 时间戳(毫秒)
        """
        self.platform = platform
        self.symbol = symbol
        self.action = action
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "quantity": self.quantity,
            "timestamp": self.timestamp
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Kline:
    """ K线 1分钟
    """

    def __init__(self, platform=None, symbol=None, open=None, high=None, low=None, close=None, volume=None,
                 timestamp=None):
        """ 初始化
        @param platform 平台
        @param symbol 交易对
        @param open 开盘价
        @param high 最高价
        @param low 最低价
        @param close 收盘价
        @param volume 成交量
        @param timestamp 时间戳(毫秒)
        """
        self.platform = platform
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.timestamp = timestamp

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timestamp": self.timestamp
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Market:
    """ 行情订阅模块
    """

    def __init__(self, market_type, platform, symbol, callback):
        """ 初始化
        @param market_type 行情类型
        @param platform 交易平台
        @param symbol 交易对
        @param callback 更新回调函数
        """
        if market_type == const.MARKET_TYPE_ORDERBOOK:
            from quant.event import EventOrderbook
            EventOrderbook(platform, symbol).subscribe(callback)
        elif market_type == const.MARKET_TYPE_TRADE:
            from quant.event import EventTrade
            EventTrade(platform, symbol).subscribe(callback)
        elif market_type == const.MARKET_TYPE_KLINE:
            from quant.event import EventKline
            EventKline(platform, symbol).subscribe(callback)
