## 行情

通过行情模块(market)，可以订阅任意交易所的任意交易对的实时行情，包括订单薄(Orderbook)、K线(KLine)、成交(Trade)、交易(Ticker)，
根据不同交易所提供的行情信息，实时将行情信息推送给策略；

在订阅行情之前，需要先部署 `行情服务器`，行情服务器将通过 REST API 或 Websocket 的方式从交易所获取实时行情信息，并将行情信息按照
统一的数据格式打包，通过事件的形式发布至事件中心；


### 行情模块使用

```python
# 导入模块
from quant import const
from quant.market import Market, Orderbook


# 订阅订单薄行情，注意此处注册的回调函数是`async` 异步函数，回调参数为 `orderbook` 对象，数据结构查看下边的介绍。
async def on_event_orderbook_update(orderbook: Orderbook): pass
Market(const.MARKET_TYPE_ORDERBOOK, const.BINANCE, "ETH/BTC", on_event_orderbook_update)
```

> 使用同样的方式，可以订阅任意的行情
```python
from quant import const

const.MARKET_TYPE_ORDERBOOK  # 订单薄(Orderbook)
const.MARKET_TYPE_KLINE  # K线(KLine)
const.MARKET_TYPE_TRADE  # K线(KLine)
```


### 行情数据结构

所有交易平台的行情，全部使用统一的数据结构；

#### 订单薄(Orderbook)
```json
{
    "platform": "binance",
    "symbol": "ETH/USDT",
    "asks": [
        ["8680.70000000", "0.00200000"]
    ],
    "bids": [
        ["8680.60000000", "2.82696138"]
    ],
    "timestamp": 1558949307370
}
```

**字段说明**:
- platform `string` 交易平台
- symbol `string` 交易对
- asks `list` 卖盘 `[price, quantity]`
- bids `list` 买盘 `[price, quantity]`
- timestamp `int` 时间戳(毫秒)


#### K线(KLine)
```json
{
    "platform": "okex",
    "symbol": "BTC/USDT",
    "open": "8665.50000000",
    "high": "8668.40000000",
    "low": "8660.00000000",
    "close": "8660.00000000",
    "volume": "73.14728136",
    "timestamp": 1558946340000
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


#### 交易数据(Trade)
```json
{
    "platform": "okex", 
    "symbol": "BTC/USDT", 
    "action": "SELL", 
    "price": "8686.40000000", 
    "quantity": "0.00200000", 
    "timestamp": 1558949571111,
}
```

**字段说明**:
- platform `string` 交易平台
- symbol `string` 交易对
- action `string` 操作类型 BUY 买入 / SELL 卖出
- price `string` 价格
- quantity `string` 数量
- timestamp `int` 时间戳(毫秒)
