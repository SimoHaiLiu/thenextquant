# -*- coding:utf-8 -*-

"""
订单

Author: HuangTao
Date:   2018/05/14
Update: None
"""

from quant.utils import tools


# 订单类型
ORDER_TYPE_MARKET = "MARKET"  # 市价单
ORDER_TYPE_LIMIT = "LIMIT"  # 限价单

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


class Order:
    """ 订单对象
    """

    def __init__(self, platform=None, account=None, strategy=None, order_no=None, symbol=None, action=None, price=0,
                 quantity=0, order_type=ORDER_TYPE_LIMIT):
        self.platform = platform  # 交易平台
        self.account = account  # 交易账户
        self.strategy = strategy  # 策略名称
        self.order_no = order_no  # 委托单号
        self.action = action  # 买卖类型 SELL-卖，BUY-买
        self.order_type = order_type  # 委托单类型 MARKET-市价，LIMIT-限价
        self.symbol = symbol  # 交易对 如: ETH/BTC
        self.price = price  # 委托价格
        self.quantity = quantity  # 委托数量（限价单）
        self.remain = quantity  # 剩余未成交数量
        self.status = ORDER_STATUS_NONE  # 委托单状态
        self.timestamp = tools.get_cur_timestamp_ms()  # 创建订单时间戳(毫秒)

    def update(self, status, remain):
        """ 更新订单详情
        @param status 订单状态
        @param remain 剩余委托量
        """
        self.status = status
        self.remain = remain
        return self

    def restore(self, order_info):
        """ 还原订单信息
        @param order_info 从数据库里取出的信息
        """
        self.platform = order_info.get("platform")
        self.account = order_info.get("account")
        self.strategy = order_info.get("strategy")
        self.order_no = order_info.get("order_no")
        self.action = order_info.get("action")
        self.order_type = order_info.get("order_type")
        self.symbol = order_info.get("symbol")
        self.price = order_info.get("price")
        self.quantity = order_info.get("quantity")
        self.remain = order_info.get("remain")
        self.status = order_info.get("status")
        self.timestamp = order_info.get("timestamp")
        return self

    def __str__(self):
        info = "[platform: {platform}, account: {account}, strategy: {strategy}, order_no: {order_no}," \
               "action: {action}, order_type: {order_type}, symbol: {symbol}, price: {price}, quantity: {quantity}, " \
               "remain: {remain}, status: {status}]"\
            .format(platform=self.platform,
                    account=self.account,
                    strategy=self.strategy,
                    order_no=self.order_no,
                    action=self.action,
                    order_type=self.order_type,
                    symbol=self.symbol,
                    price=self.price,
                    quantity=self.quantity,
                    remain=self.remain,
                    status=self.status)
        return info

    def __repr__(self):
        return str(self)
