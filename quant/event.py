# -*— coding:utf-8 -*-

"""
事件处理中心

Author: HuangTao
Date:   2018/05/04
Update: 2018/09/26  1. 优化回调函数由exchange和routing_key确定；
        2018/11/23  1. 事件增加批量订阅消息类型；
        2018/11/28  1. 增加断线重连机制；
"""

import json
import asyncio

import aioamqp

from quant.utils import tools
from quant.utils import logger
from quant.config import config
from quant.heartbeat import heartbeat
from quant.utils.decorator import async_method_locker


__all__ = ('EventCenter', 'EventConfig', 'EventHeartbeat', 'EventAsset', 'EventOrder', 'EventKline', 'EventKline5Min',
           'EventKline15Min', 'EventOrderbook', 'EventTicker')


class EventCenter:
    """ 事件处理中心
    """

    def __init__(self):
        self._host = config.rabbitmq.get('host', 'localhost')
        self._port = config.rabbitmq.get('port', 5672)
        self._username = config.rabbitmq.get('username', 'guest')
        self._password = config.rabbitmq.get('password', 'guest')
        self._protocol = None
        self._channel = None  # 连接通道
        self._connected = False  # 是否连接成功
        self._subscribers = []  # 订阅者 [(event, callback, multi), ...]
        self._event_handler = {}  # 事件对应的处理函数 {"exchange:routing_key": [callback_function, ...]}

        heartbeat.register(self._check_connection, 10)  # 检查连接是否正常

    def initialize(self):
        """ 初始化
        """
        asyncio.get_event_loop().run_until_complete(self.connect())

    @async_method_locker('EventCenter.subscribe')
    async def subscribe(self, event, callback=None, bind_queue=True, multi=False):
        """ 注册事件
        @param event 事件
        @param callback 回调函数
        @param broadcast 交换机是否需要广播消息
        @param bind_queue 此事件是否需要绑定队列接收消息
        @param multi 是否批量订阅消息，即routing_key为批量匹配
        """
        logger.info('EXCHANGE:', event.EXCHANGE, 'QUEUE:', event.QUEUE, 'NAME:', event.NAME, 'ROUTING_KEY:',
                    event.ROUTING_KEY, caller=self)
        self._subscribers.append((event, callback, multi))

    async def publish(self, event):
        """ 发布消息
        @param event 发布的事件对象
        """
        if not self._connected:
            logger.warn('RabbitMQ not ready right now!', caller=self)
            return
        data = event.dumps()
        await self._channel.basic_publish(payload=data, exchange_name=event.exchange, routing_key=event.routing_key)

    async def connect(self, reconnect=False):
        """ 建立TCP连接
        @param reconnect 是否是断线重连
        """
        logger.debug('host:', self._host, 'port:', self._port, caller=self)
        if self._connected:
            return

        # 建立连接
        try:
            transport, protocol = await aioamqp.connect(host=self._host, port=self._port, login=self._username,
                                                        password=self._password)
        except Exception as e:
            logger.error('connection error:', e, caller=self)
            return
        finally:
            # 如果已经有连接已经建立好，那么直接返回（此情况在连续发送了多个连接请求后，若干个连接建立好了连接）
            if self._connected:
                return
        channel = await protocol.channel()
        self._protocol = protocol
        self._channel = channel
        self._connected = True
        logger.info('Rabbitmq initialize success!', caller=self)

        # 创建默认的交换机
        await self._channel.exchange_declare(exchange_name=EventAsset.EXCHANGE, type_name='topic')
        await self._channel.exchange_declare(exchange_name=EventOrder.EXCHANGE, type_name='topic')
        await self._channel.exchange_declare(exchange_name=EventConfig.EXCHANGE, type_name='topic')
        await self._channel.exchange_declare(exchange_name=EventHeartbeat.EXCHANGE, type_name='topic')
        await self._channel.exchange_declare(exchange_name=EventKline.EXCHANGE, type_name='topic')
        await self._channel.exchange_declare(exchange_name=EventKline5Min.EXCHANGE, type_name='topic')
        await self._channel.exchange_declare(exchange_name=EventKline15Min.EXCHANGE, type_name='topic')
        await self._channel.exchange_declare(exchange_name=EventOrderbook.EXCHANGE, type_name='topic')
        await self._channel.exchange_declare(exchange_name=EventTicker.EXCHANGE, type_name='topic')
        logger.info('create default exchanges success!', caller=self)

        # 如果是断线重连，那么直接绑定队列并开始消费数据，如果是首次连接，那么等待5秒再绑定消费（等待程序各个模块初始化完成）
        if reconnect:
            self._bind_and_consume()
        else:
            asyncio.get_event_loop().call_later(5, self._bind_and_consume)

    def _bind_and_consume(self):
        """ 绑定并开始消费事件消息
        """
        async def do_them():
            for event, callback, multi in self._subscribers:
                await self._initialize(event, callback, multi)
        asyncio.get_event_loop().create_task(do_them())

    async def _initialize(self, event, callback=None, multi=False):
        """ 创建/绑定交易所相关消息队列
        @param event 订阅的事件
        @param callback 回调函数
        @param multi 是否批量订阅消息，即routing_key为批量匹配
        """
        if event.QUEUE:
            await self._channel.queue_declare(queue_name=event.QUEUE)
            queue_name = event.QUEUE
        else:
            result = await self._channel.queue_declare(exclusive=True)
            queue_name = result['queue']
        await self._channel.queue_bind(queue_name=queue_name, exchange_name=event.EXCHANGE,
                                       routing_key=event.ROUTING_KEY)
        await self._channel.basic_qos(prefetch_count=event.PRE_FETCH_COUNT)  # 消息窗口大小，越大，消息推送越快，但也需要处理越快
        if callback:
            if multi:
                # 消费队列，routing_key为批量匹配，无需ack
                await self._channel.basic_consume(callback=callback, queue_name=queue_name, no_ack=True)
                logger.info('multi message queue:', queue_name, 'callback:', callback, caller=self)
            else:
                # 消费队列，routing_key唯一确定，需要ack确定
                await self._channel.basic_consume(self._on_consume_event_msg, queue_name=queue_name)
                logger.info('queue:', queue_name, caller=self)
                self._add_event_handler(event, callback)

    async def _on_consume_event_msg(self, channel, body, envelope, properties):
        """ 收到订阅的事件消息
        @param channel 消息队列通道
        @param body 接收到的消息
        @param envelope
        @param properties 消息属性(发布消息时候携带)
        """
        try:
            e = Event()
            e.loads(body.decode())
        except:
            logger.error('event format error! body:', body, caller=self)
            return
        # logger.debug('exchange:', envelope.exchange_name, 'routing_key:', envelope.routing_key,
        #              'body:', body, caller=self)

        key = '{exchange}:{routing_key}'.format(exchange=envelope.exchange_name, routing_key=envelope.routing_key)
        if key not in self._event_handler:
            logger.error('event exchange not found! event:', e, caller=self)
            return

        # 执行事件回调函数
        funcs = self._event_handler[key]
        for func in funcs:
            asyncio.get_event_loop().create_task(func(e))

        # response ack
        await self._channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    def _add_event_handler(self, event, callback):
        """ 增加事件处理回调函数
        * NOTE: {"exchange:routing_key": [callback_function, ...]}
        """
        key = '{exchange}:{routing_key}'.format(exchange=event.EXCHANGE, routing_key=event.ROUTING_KEY)
        if key in self._event_handler:
            self._event_handler[key].append(callback)
        else:
            self._event_handler[key] = [callback]
        logger.info('self._event_handler:', self._event_handler, caller=self)

    async def _check_connection(self, *args, **kwargs):
        """ 检查连接是否正常，如果连接已经断开，那么立即发起连接
        """
        if self._connected and self._channel and self._channel.is_open:
            logger.debug('RabbitMQ connection ok.', caller=self)
            return
        logger.error('CONNECTION LOSE! START RECONNECT RIGHT NOW!', caller=self)
        self._connected = False
        self._protocol = None
        self._channel = None
        self._event_handler = {}
        asyncio.get_event_loop().create_task(self.connect(reconnect=True))


class Event:
    """ 事件
    """
    EXCHANGE = None  # 事件被投放的RabbitMQ交换机
    QUEUE = None  # 事件被投放的RabbitMQ队列
    ROUTING_KEY = ''  # 路由规则
    NAME = None  # 事件名
    PRE_FETCH_COUNT = 1  # 每次从消息队列里获取处理的消息条数，越多处理效率越高，但同时消耗内存越大，对进程压力也越大

    def __init__(self, data=None):
        """ 初始化
        @param data 初始化数据
        """
        self._exchange = self.EXCHANGE
        self._queue = self.QUEUE
        self._routing_key = self.ROUTING_KEY
        self._pre_fetch_count = self.PRE_FETCH_COUNT
        self._name = self.NAME
        self._data = data

    @property
    def exchange(self):
        return self._exchange

    @property
    def queue(self):
        return self._queue

    @property
    def routing_key(self):
        return self._routing_key

    @property
    def prefetch_count(self):
        return self._pre_fetch_count

    @property
    def name(self):
        return self._name

    @property
    def data(self):
        return self._data

    def dumps(self):
        """ 导出Json格式的数据
        """
        d = {
            'n': self._name,
            'd': self._data
        }
        return json.dumps(d)

    def loads(self, b):
        """ 加载Json格式的bytes数据
        @param b bytes类型的数据
        """
        d = json.loads(b)
        self._name = d.get('n')
        self._data = d.get('d')
        return d

    def parse(self):
        """ 解析self._data数据
        """
        pass

    def duplicate(self, event):
        """ 复制事件消息
        @param event 被复制的事件对象
        """
        self._exchange = event.exchange
        self._queue = event.queue
        self._name = event.name
        self._data = event.data
        self.parse()
        return self

    def subscribe(self, callback, bind_queue=True, multi=False):
        """ 订阅此事件
        @param callback 回调函数
        @param bind_queue 此事件是否需要绑定队列
        @param multi 是否批量订阅消息，即routing_key为批量匹配
        """
        from quant.quant import quant
        quant.loop.create_task(quant.event_center.subscribe(self, callback, bind_queue, multi))

    def publish(self):
        """ 发布此事件
        """
        from quant.quant import quant
        quant.loop.create_task(quant.event_center.publish(self))

    def __str__(self):
        info = 'EVENT: exchange={e}, queue={q}, routing_key={r}, name={n}, data={d}'.format(
            e=self._exchange, q=self._queue, r=self.routing_key, n=self._name, d=self._data)
        return info

    def __repr__(self):
        return str(self)


class EventConfig(Event):
    """ 配置更新事件
    * NOTE:
        订阅：配置模块
        发布：管理工具
    """
    EXCHANGE = 'config'
    QUEUE = None
    NAME = 'EVENT_CONFIG'

    def __init__(self, server_id=None, params=None):
        """ 初始化
        """
        routing_key = '{server_id}'.format(server_id=server_id)
        self.ROUTING_KEY = routing_key
        self.server_id = server_id
        self.params = params
        data = {
            'server_id': server_id,
            'params': params
        }
        super(EventConfig, self).__init__(data)

    def parse(self):
        """ 解析self._data数据
        """
        self.server_id = self._data.get('server_id')
        self.params = self._data.get('params')


class EventHeartbeat(Event):
    """ 服务心跳事件
    * NOTE:
        订阅：监控模块
        发布：业务服务进程
    """
    EXCHANGE = 'heartbeat'
    QUEUE = None
    NAME = 'EVENT_HEARTBEAT'

    def __init__(self, server_id=None, count=None):
        """ 初始化
        @param server_id 服务进程id
        @param count 心跳次数
        """
        self.server_id = server_id
        self.count = count
        data = {
            'server_id': server_id,
            'count': count
        }
        super(EventHeartbeat, self).__init__(data)

    def parse(self):
        """ 解析self._data数据
        """
        self.server_id = self._data.get('server_id')
        self.count = self._data.get('count')


class EventAsset(Event):
    """ 资产更新事件
    * NOTE:
        订阅：业务模块
        发布：Asset资产服务器
    """
    EXCHANGE = 'asset'
    QUEUE = None
    NAME = 'EVENT_ASSET'

    def __init__(self, platform=None, account=None, assets=None, timestamp=None):
        """ 初始化
        """
        timestamp = timestamp or tools.get_cur_timestamp_ms()
        self.ROUTING_KEY = '{platform}.{account}'.format(platform=platform, account=account)
        self.platform = platform
        self.account = account
        self.assets = assets
        self.timestamp = timestamp
        data = {
            'platform': platform,
            'account': account,
            'assets': assets,
            'timestamp': timestamp
        }
        super(EventAsset, self).__init__(data)

    def parse(self):
        """ 解析self._data数据
        """
        self.platform = self._data.get('platform')
        self.account = self._data.get('account')
        self.assets = self._data.get('assets')
        self.timestamp = self._data.get('timestamp')


class EventOrder(Event):
    """ 委托单事件
    * NOTE:
        订阅：订单管理器
        发布：业务服务器
    """
    EXCHANGE = 'order'
    QUEUE = None
    NAME = 'ORDER'

    def __init__(self, platform=None, account=None, strategy=None, order_no=None, symbol=None, action=None, price=None,
                 quantity=None, status=None, order_type=None, timestamp=None):
        """ 初始化
        @param platform 交易平台名称
        @param account 交易账户
        @param strategy 策略名
        @param order_no 订单号
        @param symbol 交易对
        @param action 操作类型
        @param price 限价单价格
        @param quantity 限价单数量
        @param status 订单状态
        @param order_type 订单类型
        @param timestamp 时间戳(毫秒)
        """
        data = {
            'platform': platform,
            'account': account,
            'strategy': strategy,
            'order_no': order_no,
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'status': status,
            'order_type': order_type,
            'timestamp': timestamp
        }
        super(EventOrder, self).__init__(data)

    def parse(self):
        """ 解析self._data数据
        """
        self.platform = self._data.get('platform')
        self.account = self._data.get('account')
        self.strategy = self._data.get('strategy')
        self.order_no = self._data.get('order_no')
        self.symbol = self._data.get('symbol')
        self.action = self._data.get('action')
        self.price = self._data.get('price')
        self.quantity = self._data.get('quantity')
        self.status = self._data.get('status')
        self.order_type = self._data.get('order_type')
        self.timestamp = self._data.get('timestamp')


class EventKline(Event):
    """ K线更新事件 1分钟
    """
    EXCHANGE = 'kline'
    QUEUE = None
    NAME = 'EVENT_KLINE'
    PRE_FETCH_COUNT = 20

    def __init__(self, platform=None, symbol=None, open=None, high=None, low=None, close=None, ask=None, bid=None,
                 volume=None, timestamp=None):
        """ 初始化
        @param platform 平台 比如: bitfinex
        @param symbol 交易对
        @param open 开盘价
        @param high 最高价
        @param low 最低价
        @param close 收盘价
        @param ask 卖一价格
        @param bid 买一价格
        @param volume 成交量
        @param timestamp 时间戳
        """
        routing_key = '{platform}.{symbol}'.format(platform=platform, symbol=symbol)
        self.ROUTING_KEY = routing_key
        self.platform = platform
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.ask = ask
        self.bid = bid
        self.volume = volume
        self.timestamp = timestamp
        data = [platform, symbol, open, high, low, close, ask, bid, volume, timestamp]
        super(EventKline, self).__init__(data)

    def parse(self):
        """ 解析self._data数据
        """
        self.platform = self._data[0]
        self.symbol = self._data[1]
        self.open = self._data[2]
        self.high = self._data[3]
        self.low = self._data[4]
        self.close = self._data[5]
        self.ask = self._data[6]
        self.bid = self._data[7]
        self.volume = self._data[8]
        self.timestamp = self._data[9]


class EventKline5Min(Event):
    """ K线更新事件 5分钟
    """
    EXCHANGE = 'kline.5min'
    QUEUE = None
    NAME = 'EVENT_KLINE_5MIN'
    PRE_FETCH_COUNT = 20

    def __init__(self, platform=None, symbol=None, open=None, high=None, low=None, close=None, volume=None,
                 timestamp=None):
        """ 初始化
        @param platform 平台 比如: bitfinex
        @param symbol 交易对
        @param open 开盘价
        @param high 最高价
        @param low 最低价
        @param close 收盘价
        @param volume 成交量
        @param timestamp 时间戳
        """
        routing_key = '{platform}.{symbol}'.format(platform=platform, symbol=symbol)
        self.ROUTING_KEY = routing_key
        self.platform = platform
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.timestamp = timestamp
        data = [platform, symbol, open, high, low, close, volume, timestamp]
        super(EventKline5Min, self).__init__(data)

    def parse(self):
        """ 解析self._data数据
        """
        self.platform = self._data[0]
        self.symbol = self._data[1]
        self.open = self._data[2]
        self.high = self._data[3]
        self.low = self._data[4]
        self.close = self._data[5]
        self.volume = self._data[6]
        self.timestamp = self._data[7]


class EventKline15Min(Event):
    """ K线更新事件 5分钟
    """
    EXCHANGE = 'kline.15min'
    QUEUE = None
    NAME = 'EVENT_KLINE_15MIN'
    PRE_FETCH_COUNT = 20

    def __init__(self, platform=None, symbol=None, open=None, high=None, low=None, close=None, volume=None,
                 timestamp=None):
        """ 初始化
        @param platform 平台 比如: bitfinex
        @param symbol 交易对
        @param open 开盘价
        @param high 最高价
        @param low 最低价
        @param close 收盘价
        @param volume 成交量
        @param timestamp 时间戳
        """
        routing_key = '{platform}.{symbol}'.format(platform=platform, symbol=symbol)
        self.ROUTING_KEY = routing_key
        self.platform = platform
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.timestamp = timestamp
        data = [platform, symbol, open, high, low, close, volume, timestamp]
        super(EventKline15Min, self).__init__(data)

    def parse(self):
        """ 解析self._data数据
        """
        self.platform = self._data[0]
        self.symbol = self._data[1]
        self.open = self._data[2]
        self.high = self._data[3]
        self.low = self._data[4]
        self.close = self._data[5]
        self.volume = self._data[6]
        self.timestamp = self._data[7]


class EventOrderbook(Event):
    """ 订单薄更新事件
    * NOTE:
        订阅：业务模块
        发布：交易所代理
    """
    EXCHANGE = 'orderbook'
    QUEUE = None
    NAME = 'EVENT_ORDERBOOK'

    def __init__(self, platform=None, symbol=None, asks=None, bids=None, timestamp=None):
        """ 初始化
        @param platform 交易所平台
        @param symbol 交易对
        @param asks 卖单列表 [[price, quantity], [...], ...]
        @param bids 买单列表 [[price, quantity], [...], ...]
        @param timestamp 时间戳(秒)
        """
        routing_key = '{platform}.{symbol}'.format(platform=platform, symbol=symbol)
        self.ROUTING_KEY = routing_key
        self.platform = platform
        self.symbol = symbol
        self.asks = asks
        self.bids = bids
        self.timestamp = timestamp
        data = [
            platform,
            symbol,
            asks,
            bids,
            timestamp
        ]
        super(EventOrderbook, self).__init__(data)

    def parse(self):
        """ 解析self._data数据
        """
        self.platform = self._data[0]
        self.symbol = self._data[1]
        self.asks = self._data[2]
        self.bids = self._data[3]
        self.timestamp = self._data[4]


class EventTicker(Event):
    """ 外盘ticker行情更新事件
    """
    EXCHANGE = 'ticker'
    QUEUE = None
    NAME = 'EVENT_TICKER'
    PRE_FETCH_COUNT = 20

    def __init__(self, platform=None, symbol=None, ask=None, ask_quantity=None, bid=None, bid_quantity=None,
                 timestamp=None):
        """ 初始化
        @param platform 平台 比如: bitfinex
        @param symbol 交易对
        @param ask 卖一价格
        @param bid_quantity 卖一的量
        @param bid 买一的价格
        @param bid_quantity 买一的量
        @param timestamp 时间戳
        """
        routing_key = '{platform}.{symbol}'.format(platform=platform, symbol=symbol)
        self.ROUTING_KEY = routing_key
        self.platform = platform
        self.symbol = symbol
        self.ask = ask
        self.ask_quantity = ask_quantity
        self.bid = bid
        self.bid_quantity = bid_quantity
        self.timestamp = timestamp
        data = [
            platform, symbol, ask, ask_quantity, bid, bid_quantity, timestamp
        ]
        super(EventTicker, self).__init__(data)

    def parse(self):
        """ 解析self._data数据
        """
        self.platform = self._data[0]
        self.symbol = self._data[1]
        self.ask = self._data[2]
        self.ask_quantity = self._data[3]
        self.bid = self._data[4]
        self.bid_quantity = self._data[5]
        self.timestamp = self._data[6]
