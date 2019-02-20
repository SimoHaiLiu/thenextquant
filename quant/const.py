# -*- coding:utf-8 -*-

"""
常量

Author: HuangTao
Date:   2018/07/31
Update: None
"""


# 交易所名称
COINSUPER = "coinsuper"
BCOIN = "bcoin"
GBX = "gbx"
BITFINEX = "bitfinex"
BINANCE = "binance"
OKEX = "okex"  # OKEx现货
OKEX_FUTURE = "okex_future"  # OKEx交割合约
OKEX_SWAP = "okex_swap"  # OKEx永续合约
BITMEX = "bitmex"
HUOBI = "huobi"
HUOBI_FUTURE = "huobi_future"
OKCOIN = "okcoin"
COINBASE = "coinbase"
MXC = "mxc"
DERIBIT = "deribit"
KRAKEN = "kraken"
BITSTAMP = "bitstamp"
GEMINI = "gemini"
FOTA = "fota"
BIBOX = "bibox"

# 自定义
CUSTOM = "custom"


# 行情类型
MARKET_TYPE_ORDERBOOK = "orderbook"  # 订单薄
MARKET_TYPE_KLINE = "kline"  # K线
MARKET_TYPE_TICKER = "ticker"  # ticker
MARKET_TYPE_TRADE = "trade"  # trade


# 代理操作类型
AGENT_OPTION_AUTH = "auth"  # 账户授权
AGENT_OPTION_CREATE_ORDER = "create_order"  # 创建订单
AGENT_OPTION_REVOKE_ORDER = "revoke_order"  # 撤销订单
AGENT_OPTION_ORDER_STATUS = "order_status"  # 查询订单状态
AGENT_OPTION_OPEN_ORDERS = "open_orders"  # 查询未完成订单
AGENT_OPTION_SUBSCRIBE = "subscribe"  # 订阅行情
AGENT_OPTION_UNSUBSCRIBE = "unsubscribe"  # 取消订阅行情
AGENT_OPTION_UPDATE = "update"  # 服务器推送更新
