# -*- coding:utf-8 -*-

"""
外盘行情数据存储

Author: HuangTao
Date:   2018/05/17
Update: None
"""

from quant.utils import tools
from quant.utils.mongo import MongoDBBase


class TickerData(MongoDBBase):
    """ Ticker行情数据存储
    ticker行情数据格式:
        {
            "a": ask, # 卖一价
            "A": ask_quantity, # 卖一量
            "b": bid, # 买一价
            "B": bid_quantity, # 买一量
            "t": timestamp # 时间戳(秒)
        }
    """

    def __init__(self, platform):
        """ 初始化
        @param platform 交易平台
        """
        self._db = platform  # 将交易平台名称作为数据库名称
        self._collection = 'ticker'  # 表名
        self._platform = platform
        self._t_to_c = {}   # ticker行情 交易对对应的数据库cursor {"BTC/USDT": "ticker_btc_usdt"}
        super(TickerData, self).__init__(self._db, self._collection)

    async def create_new_ticker(self, symbol, ask, ask_quantity, bid, bid_quantity, timestamp):
        """ 创建新ticker行情数据
        @param symbol 交易对
        @param ask 卖一价
        @param ask_quantity 卖一量
        @param bid 买一价
        @param bid_quantity 卖一量
        @param timestamp 时间戳
        """
        cursor = self._get_ticker_cursor_by_symbol(symbol)
        data = {
            'a': ask,
            'A': ask_quantity,
            'b': bid,
            'B': bid_quantity,
            't': timestamp
        }
        price_id = await self.insert(data, cursor=cursor)
        return price_id

    async def get_latest_ticker_by_symbol(self, symbol):
        """ 根据交易对，获取ticker行情数据
        @param symbol 交易对
        """
        cursor = self._get_ticker_cursor_by_symbol(symbol)
        sort = [('create_time', -1)]
        result = await self.find_one(sort=sort, cursor=cursor)
        return result

    def _get_ticker_cursor_by_symbol(self, symbol):
        """ collection对应的交易对
        @param symbol 交易对
        * NOTE: BTC/USDT => bitfinex.price_btc_usdt
        """
        cursor = self._t_to_c.get(symbol)
        if not cursor:
            x, y = symbol.split('/')
            collection = 'ticker_{x}_{y}'.format(x=x.lower(), y=y.lower())
            cursor = self._conn[self._db][collection]
            self._t_to_c[symbol] = cursor
        return cursor


class KLineData(MongoDBBase):
    """ K线数据存储
    K线数据格式:
        {
            "o": open, # 开盘价
            "h": high, # 最高价
            "l": low, # 最低价
            "c": close, # 收盘价
            "a": ask, # 卖一实时价
            "b": bid, # 买一实时价
            "t": timestamp # 时间戳
        }
    """

    def __init__(self, platform):
        """ 初始化
        @param platform 交易平台
        """
        self._db = platform  # 将交易平台名称作为数据库名称
        self._collection = 'kline'  # 表名
        self._platform = platform
        self._k_to_c = {}   # K线 交易对对应的数据库cursor {"BTC/USD": "kline_btc_usd"}
        super(KLineData, self).__init__(self._db, self._collection)

    async def create_new_kline(self, symbol, open, high, low, close, ask, bid, timestamp):
        """ 创建新K线数据
        @param symbol 交易对
        @param open 开盘价
        @param high 最高价
        @param low 最低价
        @param close 收盘价
        @param ask 卖一价
        @param bid 买一价
        @param timestamp 时间戳(秒)
        """
        cursor = self._get_kline_cursor_by_symbol(symbol)
        data = {
            'o': open,
            'h': high,
            'l': low,
            'c': close,
            'a': ask,
            'b': bid,
            't': timestamp
        }
        kline_id = await self.insert(data, cursor=cursor)
        return kline_id

    async def get_kline_at_ts(self, symbol, ts=None):
        """ 获取一条指定时间戳的K线数据
        @param symbol 交易对
        @param ts 时间戳(秒) 如果为空，那么就是当前时间戳
        """
        cursor = self._get_kline_cursor_by_symbol(symbol)
        if ts:
            spec = {'t': {'$lte': ts}}
        else:
            spec = {}
        _sort = [('t', -1)]
        result = await self.find_one(spec, sort=_sort, cursor=cursor)
        return result

    async def get_latest_kline_by_symbol(self, symbol):
        """ 根据交易对，获取K线数据
        @param symbol 交易对
        """
        cursor = self._get_kline_cursor_by_symbol(symbol)
        sort = [('create_time', -1)]
        result = await self.find_one(sort=sort, cursor=cursor)
        return result

    async def get_kline_between_ts(self, symbol, start_ts, end_ts):
        """ 获取一段时间范围内的K线数据
        @param symbol 交易对
        @param start_ts 开始时间戳(秒)
        @param end_ts 结束时间戳(秒)
        """
        cursor = self._get_kline_cursor_by_symbol(symbol)
        spec = {
            't': {
                '$gte': start_ts,
                '$lte': end_ts
            }
        }
        fields = {
            'create_time': 0,
            'update_time': 0
        }
        _sort = [('t', 1)]
        datas = await self.get_list(spec, fields=fields, sort=_sort, cursor=cursor)
        return datas

    def _get_kline_cursor_by_symbol(self, symbol):
        """ collection对应的交易对
        @param symbol 交易对
        * NOTE: BTC/USDT => bitfinex.kline_btc_usdt
        """
        cursor = self._k_to_c.get(symbol)
        if not cursor:
            x, y = symbol.split('/')
            collection = 'kline_{x}_{y}'.format(x=x.lower(), y=y.lower())
            cursor = self._conn[self._db][collection]
            self._k_to_c[symbol] = cursor
        return cursor


class AssetData(MongoDBBase):
    """ 资产数据存储
    资产数据结构:
        {}
    """

    def __init__(self):
        """ 初始化
        """
        self._db = 'strategy'  # 数据库名
        self._collection = 'asset'  # 表名
        super(AssetData, self).__init__(self._db, self._collection)

    async def create_new_asset(self, platform, account, asset):
        """ 创建新的资产信息
        @param platform 交易平台
        @param account 账户
        @param asset 资产详情
        """
        d = {
            'platform': platform,
            'account': account
        }
        for key, value in asset.items():
            d[key] = value
        asset_id = await self.insert(d)
        return asset_id

    async def update_asset(self, platform, account, asset, delete=None):
        """ 更新资产
        @param platform 交易平台
        @param account string 账户
        @param asset dict 资产详情
        @param delete list 需要清除的币列表（已经置零的资产）
        """
        spec = {
            'platform': platform,
            'account': account
        }
        update_fields = {'$set': asset}
        if delete:
            d = {}
            for key in delete:
                d[key] = 1
            update_fields['$unset'] = d
        await self.update(spec, update_fields=update_fields, upsert=True)

    async def get_latest_asset(self, platform, account):
        """ 查询最新的资产信息
        @param platform 交易平台
        @param account 账户
        """
        spec = {
            'platform': platform,
            'account': account
        }
        _sort = [('update_time', -1)]
        fields = {
            'platform': 0,
            'account': 0,
            'index': 0,
            'create_time': 0,
            'update_time': 0
        }
        asset = await self.find_one(spec, sort=_sort, fields=fields)
        if asset:
            del asset['_id']
        return asset


class AssetSnapshotData(MongoDBBase):
    """ 资产数据快照存储 每隔一个小时，从 strategy.asset 表中，创建一次快照数据
    资产数据结构:
        {}
    """

    def __init__(self):
        """ 初始化
        """
        self._db = 'strategy'  # 数据库名
        self._collection = 'asset_snapshot'  # 表名
        super(AssetSnapshotData, self).__init__(self._db, self._collection)

    async def create_new_asset(self, platform, account, asset):
        """ 创建新的资产信息
        @param platform 交易平台
        @param account 账户
        @param asset 资产详情
        """
        d = {
            'platform': platform,
            'account': account
        }
        for key, value in asset.items():
            d[key] = value
        asset_id = await self.insert(d)
        return asset_id

    async def get_asset_snapshot(self, platform, account, start=None, end=None):
        """ 获取资产快照
        @param platform 交易平台
        @param account 账户
        @param start 开始时间戳(秒)
        @param end 结束时间戳(秒)
        """
        if not end:
            end = tools.get_cur_timestamp()  # 截止时间默认当前时间
        if not start:
            start = end - 60 * 60 * 24  # 开始时间默认一天前
        spec = {
            'platform': platform,
            'account': account,
            'create_time': {
                '$gte': start,
                '$lte': end
            }
        }
        fields = {
            'platform': 0,
            'account': 0,
            'update_time': 0
        }
        datas = await self.get_list(spec, fields=fields)
        return datas

    async def get_latest_asset_snapshot(self, platform, account):
        """ 查询最新的资产快照
        @param platform 交易平台
        @param account 账户
        """
        spec = {
            'platform': platform,
            'account': account
        }
        _sort = [('update_time', -1)]
        asset = await self.find_one(spec, sort=_sort)
        if asset:
            del asset['_id']
        return asset


class OrderData(MongoDBBase):
    """ 订单数据存储
    """

    def __init__(self):
        """ 初始化
        @param db 数据库
        @param collection 表
        """
        self._db = 'strategy'  # 数据库名
        self._collection = 'order'  # 表名
        super(OrderData, self).__init__(self._db, self._collection)

    async def create_new_order(self, order):
        """ 创建新订单
        @param order 订单对象
        """
        data = {
            'platform': order.platform,
            "account": order.account,
            'strategy': order.strategy,
            'symbol': order.symbol,
            'order_no': order.order_no,
            'action': order.action,
            'order_type': order.order_type,
            'status': order.status,
            'price': order.price,
            'quantity': order.quantity,
            'remain': order.remain,
            'timestamp': order.timestamp,
        }
        order_id = await self.insert(data)
        return order_id

    async def get_order_by_no(self, platform, order_no):
        """ 获取订单最新信息
        @param platform 交易平台
        @param order_no 订单号
        """
        spec = {
            'platform': platform,
            'order_no': order_no
        }
        data = await self.find_one(spec)
        return data

    async def get_order_by_nos(self, platform, order_nos):
        """ 批量获取订单状态
        @param platform 交易平台
        @param order_nos 订单号列表
        """
        spec = {
            'platform': platform,
            'order_no': {'$in': order_nos}
        }
        fields = {
            'status': 1
        }
        datas = await self.get_list(spec, fields=fields)
        return datas

    async def update_order_infos(self, order):
        """ 更新订单信息
        @param order 订单对象
        """
        spec = {
            'platform': order.platform,
            'order_no': order.order_no
        }
        update_fields = {
            'status': order.status,
            'remain': order.remain
        }
        await self.update(spec, update_fields={'$set': update_fields})

    async def get_latest_order(self, platform, symbol):
        """ 获取一条最新的订单
        @param platform 交易平台
        @param symbol 交易对
        """
        spec = {
            'platform': platform,
            'symbol': symbol
        }
        _sort = [('update_time', -1)]
        data = await self.find_one(spec, sort=_sort)
        return data
