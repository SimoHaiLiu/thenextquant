# -*- coding:utf-8 -*-

"""
持仓对象

Author: HuangTao
Date:   2018/04/22
"""


class Position:
    """ 持仓对象
    """

    def __init__(self, platform=None, account=None, strategy=None, symbol=None):
        """ 初始化持仓对象
        @param platform 交易平台
        @param account 账户
        @param strategy 策略名称
        @param symbol 合约名称
        """
        self.platform = platform
        self.account = account
        self.strategy = strategy
        self.symbol = symbol
        self.short_quantity = 0  # 空仓数量
        self.long_quantity = 0  # 多仓数量
        self.average_price = 0  # 平均价格
        self.liquid_price = 0  # 预估爆仓价格
        self.utime = None  # 更新时间戳

    def __str__(self):
        info = "[platform: {platform}, account: {account}, strategy: {strategy}, symbol: {symbol}, " \
               "short_quantity: {short_quantity}, long_quantity: {long_quantity}, average_price: {average_price}, " \
               "liquid_price={liquid_price}]"\
            .format(platform=self.platform, account=self.account, strategy=self.strategy, symbol=self.symbol,
                    short_quantity=self.short_quantity, long_quantity=self.long_quantity,
                    average_price=self.average_price, liquid_price=self.liquid_price)
        return info

    def __repr__(self):
        return str(self)
