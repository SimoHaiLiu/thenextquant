## 交易

通过交易模块(trade)，可以在任意交易平台发起交易，包括下单(create_order)、撤单(revoke_order)、查询订单状态(order_status)、
查询未完全成交订单(orders)等功能；

策略完成下单之后，底层框架将定时或实时将最新的订单状态更新通过策略注册的回调函数传递给策略，策略能够在第一时间感知到拿到订单状态
更新数据；

框架通过一条websocket长连接和 Agent 代理服务器建立连接，并发起交易平台账户的授权请求，授权通过之后，即可以进行交易；

Agent代理服务默认可以使用 wss://thenextquant.com/ws/trade 进行测试（有部分使用限制）；

- Agent代理服务器配置
```json
{
    "SERVICE": {
        "Trade": {
            "wss": "wss://thenextquant.com/ws/trade"
        }
    }
}
```


### 交易模块使用

```python
# 导入模块
from quant import const
from quant import order
from quant.trade import Trade

# 初始化
platform = const.BINANCE  # 交易平台 假设是binance
account = "abc@gmail.com"  # 交易账户
access_key = "ABC123"  # API KEY
secret_key = "abc123"  # SECRET KEY
symbol = "ETH/BTC"  # 交易对
name = "my_test_strategy"  # 自定义的策略名称
trader = Trade(platform, account, access_key, secret_key, symbol, name)

# 注册订单更新回调函数，注意此处注册的回调函数是 `async` 异步函数，回调参数为 `order` 对象，数据结构请查看下边的介绍。
async def on_event_order_update(self, order): pass
trader.register_callback(on_event_order_update)

# 下单
action = order.ORDER_ACTION_BUY  # 买单
price = "11.11"  # 委托价格
quantity = "22.22"  # 委托数量
order_type = order.ORDER_TYPE_LIMIT  # 限价单
order_no = await trader.create_order(action, price, quantity, order_type)  # 注意，此函数需要在 `async` 异步函数里执行


# 撤单
await trader.revoke_order(order_no)  # 注意，此函数需要在 `async` 异步函数里执行


# 查询所有未成交订单id列表
order_nos = await trader.get_open_orders()  # 注意，此函数需要在 `async` 异步函数里执行


# 查询当前所有未成交订单数据
orders = trader.orders  # orders是一个dict，key为order_no，value为order对象
```

### 订单对象模块

所有订单相关的数据常量和对象在框架的 `quant.order` 模块下。

- 订单类型
```python
from quant import order

order.ORDER_TYPE_LIMIT  # 限价单
order.ORDER_TYPE_MARKET  # 市价单
```

- 订单操作
```python
from quant import order

order.ORDER_ACTION_BUY  # 买入
order.ORDER_ACTION_SELL  # 卖出
```

- 订单状态
```python
from quant import order

order.ORDER_STATUS_NONE = "NONE"  # 新创建的订单，无状态
order.ORDER_STATUS_SUBMITTED = "SUBMITTED"  # 已提交
order.ORDER_STATUS_PARTIAL_FILLED = "PARTIAL-FILLED"  # 部分处理
order.ORDER_STATUS_FILLED = "FILLED"  # 处理
order.ORDER_STATUS_CANCELED = "CANCELED"  # 取消
order.ORDER_STATUS_FAILED = "FAILED"  # 失败订单
```

- 订单对象
```python
from quant import order

o = order.Order()
o.platform  # 交易平台
o.account  # 交易账户
o.strategy  # 策略名称
o.order_no  # 委托单号
o.action  # 买卖类型 SELL-卖，BUY-买
o.order_type  # 委托单类型 MKT-市价，LMT-限价
o.symbol  # 交易对 如: ETH/BTC
o.price  # 委托价格
o.quantity  # 委托数量（限价单）
o.remain  # 剩余未成交数量
o.status  # 委托单状态
o.timestamp  # 创建订单时间戳(毫秒)
```
