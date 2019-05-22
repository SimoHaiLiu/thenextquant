# -*- coding:utf-8 -*-

"""
Trade 交易模块，整合所有交易所为一体

Author: HuangTao
Date:   2019/04/21
"""

from quant.utils import logger
from quant.order import ORDER_TYPE_LIMIT
from quant.const import OKEX, OKEX_FUTURE, DERIBIT, BITMEX
from quant.platform.okex import OKExTrade
# from quant.platform.bitmex.trade import BitmexTrade
from quant.platform.deribit import DeribitTrade
# from quant.platform.okex_future.trade import OKExFutureTrade


class Trade:
    """ 交易模块
    """

    def __init__(self, strategy, platform, symbol, order_update_callback=None,
                 position_update_callback=None, **kwargs):
        """ 初始化
        @param strategy 策略名称
        @param platform 交易平台
        @param symbol 交易对
        @param order_update_callback 订单更新回调
        @param position_update_callback 持仓更新回调
        """
        self._platform = platform
        self._strategy = strategy
        self._symbol = symbol

        if platform == OKEX:
            self._t = OKExTrade(kwargs["account"], strategy, symbol, kwargs["host"], kwargs["wss"],
                                kwargs["access_key"], kwargs["secret_key"], kwargs["passphrase"],
                                order_update_callback=order_update_callback)
        elif platform == OKEX_FUTURE:
            self._t = OKExFutureTrade(kwargs["account"], strategy, symbol, kwargs["host"], kwargs["wss"],
                                      kwargs["access_key"], kwargs["secret_key"], kwargs["passphrase"],
                                      order_update_callback=order_update_callback,
                                      position_update_callback=position_update_callback)
        elif platform == DERIBIT:
            self._t = DeribitTrade(kwargs["account"], strategy, symbol, kwargs["host"], kwargs["wss"],
                                   kwargs["access_key"], kwargs["secret_key"],
                                   order_update_callback=order_update_callback,
                                   position_update_callback=position_update_callback)
        elif platform == BITMEX:
            self._t = BitmexTrade(kwargs["account"], strategy, symbol, kwargs["host"], kwargs["wss"],
                                  kwargs["access_key"], kwargs["secret_key"],
                                  order_update_callback=order_update_callback,
                                  position_update_callback=position_update_callback)
        else:
            logger.error("platform error:", platform, caller=self)
            exit(-1)

    @property
    def position(self):
        return self._t.position

    @property
    def orders(self):
        return self._t.orders

    async def create_order(self, action, price, quantity, order_type=ORDER_TYPE_LIMIT):
        """ 创建委托单
        @param action 交易方向 BUY/SELL
        @param price 委托价格
        @param quantity 委托数量(当为负数时，代表合约操作空单)
        @param order_type 委托类型 LIMIT/MARKET
        @return (order_no, error) 如果成功，order_no为委托单号，error为None，否则order_no为None，error为失败信息
        """
        order_no, error = await self._t.create_order(action, price, quantity, order_type)
        return order_no, error

    async def revoke_order(self, *order_nos):
        """ 撤销委托单
        @param order_nos 订单号列表，可传入任意多个，如果不传入，那么就撤销所有订单
        @return (success, error) success为撤单成功列表，error为撤单失败的列表
        """
        success, error = await self._t.revoke_order(*order_nos)
        return success, error

    async def get_open_order_nos(self):
        """ 获取未完成委托单id列表
        @return (result, error) result为成功获取的未成交订单列表，error如果成功为None，如果不成功为错误信息
        """
        result, error = await self._t.get_open_order_nos()
        return result, error
