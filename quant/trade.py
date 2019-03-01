# -*- coding:utf-8 -*-

"""
交易模块

Author: HuangTao
Date:   2018/05/13
Update: None
"""

import copy
import asyncio

from quant import const
from quant.utils import tools
from quant.utils import logger
from quant.config import config
from quant.utils import decorator
from quant.utils.agent import Agent
from quant.heartbeat import heartbeat
from quant.order import Order, ORDER_TYPE_MKT, ORDER_TYPE_LMT, ORDER_ACTION_BUY, ORDER_ACTION_SELL, \
    ORDER_STATUS_SUBMITTED, ORDER_STATUS_CANCEL, ORDER_STATUS_DEAL, ORDER_STATUS_PARTDEAL, ORDER_STATUS_FAILED


class Trade:
    """ 交易模块
    """

    def __init__(self, platform, account, access_key, secret_key, symbol, strategy, order_update_interval=2):
        """ 初始化
        @param platform 交易平台
        @param account 交易账户
        @param access_key 公钥
        @param secret_key 私钥
        @param symbol 交易对
        @param strategy 策略名称
        @param order_update_interval 检查订单更新时间间隔(秒)
        """
        self._platform = platform
        self._account = account
        self._access_key = access_key
        self._secret_key = secret_key
        self._symbol = symbol
        self._strategy = strategy
        self._order_update_interval = order_update_interval

        url = config.service.get("Trade", {}).get("wss", "wss://thenextquant.com/ws/trade")
        self._agent = Agent(url)

        # 订单对象
        self._orders = {}   # 订单列表 key:order_no, value:order_object

        # 回调函数列表
        self._callback_funcs = []

        # 定时回调 查询订单状态
        heartbeat.register(self.check_order_update, self._order_update_interval)

        # 定时回调 请求登陆
        self._login_task_id = heartbeat.register(self.auth, 1)
        self._is_logined = False  # 账户是否授权
        self._is_logining = False  # 账户是否正在授权

    @property
    def orders(self):
        return copy.copy(self._orders)

    def register_callback(self, callback):
        """ 订单更新回调
        @param callback 回调函数(回调参数为更新的订单对象)
            async def callback_func(order):
                pass
        """
        self._callback_funcs.append(callback)

    @decorator.async_method_locker("Trade.login")
    async def auth(self, *args, **kwargs):
        """ 登陆账户
        * NOTE: 和TradeProxy建立连接之后，将立即回执行登陆请求
        """
        if self._is_logining:
            return
        self._is_logining = True
        if self._is_logined:
            heartbeat.unregister(self._login_task_id)  # 取消定时登陆回调
            return
        params = {
            "platform": self._platform,
            "access_key": self._access_key,
            "secret_key": self._secret_key
        }
        ok, _, result = await self._agent.do_request(const.AGENT_OPTION_AUTH, params)
        if not ok:
            logger.error("auth error!", "platform:", self._platform, "account:", self._account, "result:", result,
                         caller=self)
        else:
            self._is_logined = True
            logger.debug("auth success!", "platform:", self._platform, "account:", self._account, caller=self)
        self._is_logining = False

    async def create_order(self, action, price, quantity, order_type=ORDER_TYPE_LMT):
        """ 创建委托单
        @param action 操作类型 BUY买/SELL卖
        @param price 委托价格
        @param quantity 委托数量
        @param order_type 委托单类型 LMT限价单/MKT市价单
        """
        if not self._is_logined:
            logger.warn("not auth! platform:", self._platform, "account:", self._account, caller=self)
            return
        if action not in [ORDER_ACTION_BUY, ORDER_ACTION_SELL]:
            logger.error('action error! action:', action, caller=self)
            return
        if order_type not in [ORDER_TYPE_MKT, ORDER_TYPE_LMT]:
            logger.error('order_type error! order_type:', order_type, caller=self)
            return

        # 创建订单
        price = tools.float_to_str(price)
        quantity = tools.float_to_str(quantity)
        params = {
            "symbol": self._symbol,
            "action": action,
            "price": price,
            "quantity": quantity,
            "order_type": order_type
        }
        success, _, result = await self._agent.do_request(const.AGENT_OPTION_CREATE_ORDER, params)
        if not success:
            logger.error('create order error! strategy:', self._strategy, 'symbol:', self._symbol, 'action:', action,
                         'price:', price, 'quantity:', quantity, 'order_type:', order_type, "result:", result,
                         caller=self)
            return None

        order_no = result["order_no"]
        infos = {
            'platform': self._platform,
            'account': self._account,
            'strategy': self._strategy,
            'order_no': order_no,
            'symbol': self._symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'order_type': order_type
        }
        order = Order(**infos)

        # 增加订单到订单列表
        self._add_order(order)
        logger.info('order:', order, caller=self)
        return order_no

    async def revoke_order(self, *order_nos):
        """ 撤销委托单
        @param order_nos 委托单号（支持传入单个或多个）
        @return success, failed 撤单成功的订单号列表，撤单失败的订单号列表
        """
        if not self._is_logined:
            logger.warn("not auth! platform:", self._platform, "account:", self._account, caller=self)
            return
        params = {
            "symbol": self._symbol,
            "order_nos": list(order_nos)
        }
        success, _, result = await self._agent.do_request(const.AGENT_OPTION_REVOKE_ORDER, params)
        if not success:
            logger.error("revoke order error! order_nos:", order_nos, "order_nos:", order_nos, caller=self)
            return [], list(order_nos)
        logger.info("symbol:", self._symbol, "order_nos:", order_nos, caller=self)
        return result["success"], result["failed"]

    async def check_order_update(self, *args, **kwargs):
        """ 检查订单更新
        """
        if not self._is_logined:
            return
        # 获取需要查询的订单列表
        order_nos = list(self._orders.keys())
        logger.info('length:', len(order_nos), 'orders:', order_nos, caller=self)
        if not order_nos:  # 暂时没有需要更新的委托单，那么延迟1秒，再次发布执行委托单更新事件
            logger.debug('no find any order nos', caller=self)
            return

        # 获取订单最新状态，每次最多请求50个订单
        while order_nos:
            nos = order_nos[:100]
            params = {
                "symbol": self._symbol,
                "order_nos": nos
            }
            success, _, results = await self._agent.do_request(const.AGENT_OPTION_ORDER_STATUS, params)
            if not success:
                logger.error("get order status error!", "symbol:", self._symbol, "order_nos:", order_nos,
                             "results:", results, caller=self)
            await self._process_order_update_infos(results)
            order_nos = order_nos[100:]

    async def _process_order_update_infos(self, results):
        """ 处理委托单更新
        @param results 获取的委托单状态
        """
        for detail in results:
            if not detail:
                logger.warn('detail is none!', caller=self)
                return
            status_updated = False
            order_no = detail.get("order_no")
            status = detail["status"]
            remain = detail["remain"]
            order = await self._get_order_by_order_no(order_no)
            if not order:
                continue

            # 已提交
            if status == ORDER_STATUS_SUBMITTED:
                if order.status != status:
                    status_updated = True
            # 订单部分成交
            elif status == ORDER_STATUS_PARTDEAL:
                if order.remain != float(remain):
                    status_updated = True
            # 订单成交完成
            elif status == ORDER_STATUS_DEAL:
                status_updated = True
            # 订单取消
            elif status == ORDER_STATUS_CANCEL:
                status_updated = True
            # 订单成交失败
            elif status == ORDER_STATUS_FAILED:
                status_updated = True
            else:
                logger.warn('status error! order_no:', order.order_no, 'status:', order.status, caller=self)
                continue

            # 有状态更新 更新数据库订单信息
            if status_updated:
                order.update(status, remain)

                # 执行回调
                for func in self._callback_funcs:
                    await asyncio.get_event_loop().create_task(func(copy.copy(order)))

                # 删除已完成订单
                if order.status in [ORDER_STATUS_DEAL, ORDER_STATUS_CANCEL, ORDER_STATUS_FAILED]:
                    self._remove_order(order.order_no)

    async def get_open_orders(self):
        """ 获取未完全成交的订单
        """
        if not self._is_logined:
            logger.warn("not auth! platform:", self._platform, "account:", self._account, caller=self)
            return
        params = {
            "symbol": self._symbol
        }
        success, _, results = await self._agent.do_request(const.AGENT_OPTION_OPEN_ORDERS, params)
        if not success:
            logger.error("get open orders error! symbol:", self._symbol, caller=self)
            return None
        logger.info("symbol:", self._symbol, "open orders:", results, caller=self)
        return results

    async def _get_order_by_order_no(self, order_no):
        """ 根据订单号获取订单数据 如果没找到，那么从数据库提取数据出来重置数据
        @param order_no 订单号
        """
        order = self._orders.get(order_no)
        if not order:
            return None
        return order

    def _add_order(self, order):
        """ 将新的订单添加的订单列表
        @param order 新订单对象
        """
        if not order or order.order_no in self._orders:
            return
        self._orders[order.order_no] = order

    def _remove_order(self, order_no):
        """ 移除订单
        """
        if order_no in self._orders:
            del self._orders[order_no]
