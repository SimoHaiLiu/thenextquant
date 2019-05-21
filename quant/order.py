# -*- coding:utf-8 -*-

"""
订单

Author: HuangTao
Date:   2018/05/14
"""

from quant.utils import tools


# 订单类型
ORDER_TYPE_LIMIT = "LIMIT"  # 限价单
ORDER_TYPE_MARKET = "MARKET"  # 市价单

# 订单操作 买/卖
ORDER_ACTION_BUY = "BUY"  # 买
ORDER_ACTION_SELL = "SELL"  # 卖

# 订单状态
ORDER_STATUS_NONE = "NONE"  # 新创建的订单，无状态
ORDER_STATUS_SUBMITTED = "SUBMITTED"  # 已提交
ORDER_STATUS_PARTIAL_FILLED = "PARTIAL-FILLED"  # 部分处理
ORDER_STATUS_FILLED = "FILLED"  # 处理
ORDER_STATUS_CANCELED = "CANCELED"  # 取消
ORDER_STATUS_FAILED = "FAILED"  # 失败订单

# 合约订单类型
TRADE_TYPE_NONE = 0  # 未知订单类型，订单不是由框架创建，且某些平外的订单不能判断订单类型
TRADE_TYPE_BUY_OPEN = 1  # 买入开多 action=BUY, quantity>0
TRADE_TYPE_SELL_OPEN = 2  # 卖出开空 action=SELL, quantity<0
TRADE_TYPE_SELL_CLOSE = 3  # 卖出平多 action=SELL, quantity>0
TRADE_TYPE_BUY_CLOSE = 4  # 买入平空 action=BUY, quantity<0


class Order:
    """ 订单对象
    """

    def __init__(self, account=None, platform=None, strategy=None, order_no=None, symbol=None, action=None, price=0,
                 quantity=0, remain=0, status=ORDER_STATUS_NONE, avg_price=0, order_type=ORDER_TYPE_LIMIT,
                 trade_type=TRADE_TYPE_NONE):
        self.platform = platform  # 交易平台
        self.account = account  # 交易账户
        self.strategy = strategy  # 策略名称
        self.order_no = order_no  # 委托单号
        self.action = action  # 买卖类型 SELL-卖，BUY-买
        self.order_type = order_type  # 委托单类型 MARKET-市价，LIMIT-限价
        self.symbol = symbol  # 交易对 如: ETH/BTC
        self.price = price  # 委托价格
        self.quantity = quantity  # 委托数量（限价单）
        self.remain = remain  # 剩余未成交数量
        self.status = status  # 委托单状态
        self.avg_price = avg_price  # 成交均价
        self.trade_type = trade_type  # 合约订单类型 开多/开空/平多/平空
        self.ctime = tools.get_cur_timestamp()  # 创建订单时间戳
        self.utime = None  # 交易所订单更新时间

    def __str__(self):
        info = "[platform: {platform}, account: {account}, strategy: {strategy}, order_no: {order_no}, " \
               "action: {action}, symbol: {symbol}, price: {price}, quantity: {quantity}, remain: {remain}, " \
               "status: {status}, avg_price: {avg_price}, order_type: {order_type}, trade_type: {trade_type}, " \
               "ctime: {ctime}, utime: {utime}]".format(
            platform=self.platform, account=self.account, strategy=self.strategy, order_no=self.order_no,
            action=self.action, symbol=self.symbol, price=self.price, quantity=self.quantity,
            remain=self.remain, status=self.status, avg_price=self.avg_price, order_type=self.order_type,
            trade_type=self.trade_type, ctime=self.ctime, utime=self.utime)
        return info

    def __repr__(self):
        return str(self)
