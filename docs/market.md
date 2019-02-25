## 交易行情

通过行情模块(market)，可以订阅任意交易所的任意交易对的实时行情，包括订单薄(Orderbook)、K线(KLine)、成交(Trade)、交易(Ticker)，  
根据不同交易所提供的行情信息，实时将行情信息推送给策略；

框架通过一条websocket长连接和 `Agent` 代理服务器建立连接，并发起 `订阅(Subscribe)` 和 `取消订阅(Unsubscribe)` 请求；  
`Agent`代理服务默认可以使用 `wss://thenextquant.com/ws/market` 进行测试（有部分使用限制）；


### 行情模块使用

```python
# 导入模块
from quant import const
from quant.market import Market

# 初始化
market = Market()

# 订阅订单薄行情
async def on_event_orderbook_update(orderbook): pass
market.subscribe(const.MARKET_TYPE_ORDERBOOK, const.BINANCE, "ETH/BTC", on_event_orderbook_update)

# 取消订阅订单薄行情
market.unsubscribe(const.MARKET_TYPE_ORDERBOOK, const.BINANCE, "ETH/BTC")
```

> 使用同样的方式，可以订阅 KLine(const.MARKET_TYPE_KLINE)、Trade(const.MARKET_TYPE_TRADE)、Ticker(const.MARKET_TYPE_TICKER);


### 行情数据结构

所有交易平台的行情，全部使用统一的数据结构；

##### 订单薄(Orderbook)
```json
{
    "platform": "binance",
    "symbol": "ETH/BTC",
    "asks": [
        ["11.11", "11"]
    ],
    "bids": [
        ["22.22", "22"]
    ],
    "timestamp": 12345678901234
}
```

**字段说明**:
- platform `string` 交易平台
- symbol `string` 交易对
- asks `list` 卖盘 `[price, quantity]`
- bids `list` 买盘 `[price, quantity]`
- timestamp `int` 时间戳(毫秒)


##### K线(KLine)
```json
{
    "platform": "binance",
    "symbol": "ETH/BTC",
    "open": "11",
    "high": "22",
    "low": "10",
    "close": "20",
    "volume": "123",
    "timestamp": 12345678901234
}
```

**字段说明**:
- platform `string` 交易平台
- symbol `string` 交易对
- open `string` 开盘价
- high `string` 最高价
- low `string` 最低价
- close `string` 收盘价
- volume `string` 成交量
- timestamp `int` 时间戳(毫秒)


##### 交易(Ticker)
```json
{
    "platform": "binance",
    "symbol": "ETH/BTC",
    "ask": "11.11",
    "ask_quantity": "22.22",
    "bid": "33.33",
    "bid_quantity": "44.44",
    "timestamp": 12345678901234
}
```

**字段说明**:
- platform `string` 交易平台
- symbol `string` 交易对
- ask `string` 卖单价格
- ask_quantity `string` 卖单数量
- bid `string` 买单价格
- bid_quantity `string` 买单数量
- timestamp `int` 时间戳(毫秒)


##### 成交(Trade)
```json
{
    "platform": "binance",
    "symbol": "ETH/BTC",
    "action": "BUY",
    "price": "11.11",
    "quantity": "22.22",
    "timestamp": 12345678901234
}
```

**字段说明**:
- platform `string` 交易平台
- symbol `string` 交易对
- action `string` 买或卖(可能有些交易所没指定，那么就是空字符串)
- price `string` 委托价格
- quantity `string` 委托数量
- timestamp `int` 时间戳(毫秒)
