# -*- coding:utf-8 -*-

# 策略实现

from quant.utils import logger
from quant.config import config
from quant.heartbeat import heartbeat
from quant.order import ORDER_ACTION_BUY
from quant.trade import Trade
from quant.const import BINANCE


class MyStrategy:

    def __init__(self):
        """ 初始化
        """
        self.platfrom = BINANCE
        self.account = config.platforms.get(self.platfrom, {}).get("account")
        self.access_key = config.platforms.get(self.platfrom, {}).get("access_key")
        self.secret_key = config.platforms.get(self.platfrom, {}).get("secret_key")
        self.symbol = config.symbol
        self.name = config.strategy

        self.order_manager = None

    def initialize(self):
        """ 初始化
        """
        self.trader = Trade(self.platfrom, self.account, self.access_key, self.secret_key, self.symbol, self.name)

        # 注册订单状态更新回调
        self.trader.register_callback(self.on_event_order_update)

        # 注册定时任务
        heartbeat.register(self.do_task)

    async def on_event_order_update(self, order):
        """ 订单状态更新
        """
        logger.info("order update:", order, caller=self)

    async def create_order(self):
        """ 创建订单
        """
        action = ORDER_ACTION_BUY
        price = "0.031898"
        quantity = "0.2"
        order_no = await self.trader.create_order(action, price, quantity)
        logger.info("create new order:", order_no, caller=self)

    async def do_task(self, *args, **kwargs):
        """ 定时任务
        * NOTE: 每秒钟执行一次，假设在程序启动12秒的时候，挂一个买单
        """
        if heartbeat.count != 12:
            return
        await self.create_order()
