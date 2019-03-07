# -*- coding:utf-8 -*-

# 策略实现

from quant import const
from quant.utils import tools
from quant.utils import logger
from quant.config import config
from quant.order import ORDER_ACTION_BUY, ORDER_STATUS_FAILED, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED
from quant.market import Market
from quant.trade import Trade
from quant.const import BINANCE


class MyStrategy:

    def __init__(self):
        """ 初始化
        """
        self.platform = BINANCE
        self.account = config.platforms.get(self.platform, {}).get("account")
        self.access_key = config.platforms.get(self.platform, {}).get("access_key")
        self.secret_key = config.platforms.get(self.platform, {}).get("secret_key")
        self.symbol = config.symbol
        self.name = config.strategy

        self.market = None  # 行情模块
        self.trader = None  # 交易模块

        self.order_no = None  # 创建订单的id
        self.create_order_price = "0.0"  # 创建订单的价格

    def initialize(self):
        """ 初始化
        """
        self.market = Market()
        self.trader = Trade(self.platform, self.account, self.access_key, self.secret_key, self.symbol, self.name)

        # 订阅行情
        self.market.subscribe(const.MARKET_TYPE_ORDERBOOK, const.BINANCE, self.symbol, self.on_event_orderbook_update)

        # 注册订单状态更新回调
        self.trader.register_callback(self.on_event_order_update)

    async def on_event_orderbook_update(self, orderbook):
        """ 订单薄更新
        """
        logger.debug("orderbook:", orderbook, caller=self)
        bid3_price = orderbook["bids"][2][0]  # 买三价格
        bid4_price = orderbook["bids"][3][0]  # 买四价格

        # 判断是否需要撤单
        if self.order_no:
            if float(self.create_order_price) < float(bid3_price) or float(self.create_order_price) > float(bid4_price):
                return
            await self.trader.revoke_order(self.order_no)
            self.order_no = None
            logger.info("revoke order:", self.order_no, caller=self)

        # 创建新订单
        new_price = (float(bid3_price) + float(bid4_price)) / 2
        quantity = "0.1"  # 假设委托数量为0.1
        action = ORDER_ACTION_BUY
        price = tools.float_to_str(new_price)
        quantity = tools.float_to_str(quantity)
        order_no = await self.trader.create_order(action, price, quantity)
        self.order_no = order_no
        self.create_order_price = price
        logger.info("create new order:", order_no, caller=self)

    async def on_event_order_update(self, order):
        """ 订单状态更新
        """
        logger.info("order update:", order, caller=self)

        # 如果订单失败、订单取消、订单完成交易
        if order.status in [ORDER_STATUS_FAILED, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED]:
            self.order_no = None
