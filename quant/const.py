# -*- coding:utf-8 -*-

"""
常量

Author: HuangTao
Date:   2018/07/31
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
CUSTOM = "custom"  # 自定义


# 行情
AGENT_MSG_OPT_SUB_ORDERBOOK     = "subscribe.orderbook"     # 订阅 orderbook
AGENT_MSG_OPT_UNSUB_ORDERBOOK   = "unsubscribe.orderbook"   # 取消订阅 orderbook
AGENT_MSG_OPT_UPDATE_ORDERBOOK  = "update.orderbook"        # 更新推送 orderbook
AGENT_MSG_OPT_SUB_KLINE         = "subscribe.kline"         # 订阅 kline
AGENT_MSG_OPT_UNSUB_KLINE       = "unsubscribe.kline"       # 取消订阅 kline
AGENT_MSG_OPT_UPDATE_KLINE      = "update.kline"            # 更新推送 kline
AGENT_MSG_OPT_SUB_TRADE         = "subscribe.trade"         # 订阅 trade
AGENT_MSG_OPT_UNSUB_TRADE       = "unsubscribe.trade"       # 取消订阅 trade
AGENT_MSG_OPT_UPDATE_TRADE      = "update.trade"            # 更新推送 trade
AGENT_MSG_OPT_SUB_TICKER        = "subscribe.ticker"        # 订阅 ticker
AGENT_MSG_OPT_UNSUB_TICKER      = "unsubscribe.ticker"      # 取消订阅 ticker
AGENT_MSG_OPT_UPDATE_TICKER     = "update.ticker"           # 更新推送 ticker


# 交易
AGENT_MSG_OPT_AUTH              = "auth"                    # 账户授权
AGENT_MSG_OPT_ASSET             = "asset"                   # 获取资产
AGENT_MSG_OPT_CREATE_OREDER     = "create_order"            # 创建订单
AGENT_MSG_OPT_REVOKE_ORDER      = "revoke_order"            # 撤销订单
AGENT_MSG_OPT_ORDER_STATUS      = "order_status"            # 查询订单状态
AGENT_MSG_OPT_OPEN_ORDERS       = "open_orders"             # 查询未完全成交订单号列表
AGENT_MSG_OPT_SUB_ASSET         = "subscribe.asset"         # 订阅 资产
AGENT_MSG_OPT_UNSUB_ASSET       = "unsubscribe.asset"       # 取消订阅 资产
AGENT_MSG_OPT_UPDATE_ASSET      = "update.asset"            # 更新推送 资产
AGENT_MSG_OPT_SUB_ORDER         = "subscribe.order"         # 订阅 订单
AGENT_MSG_OPT_UNSUB_ORDER       = "unsubscribe.order"       # 取消订阅 订单
AGENT_MSG_OPT_UPDATE_ORDER      = "update.order"            # 更新推送 订单
AGENT_MSG_OPT_SUB_POSITION      = "subscribe.position"      # 订阅 持仓
AGENT_MSG_OPT_UNSUB_POSITION    = "unsubscribe.position"    # 取消订阅 持仓
AGENT_MSG_OPT_UPDATE_POSITION   = "update.position"         # 更新推送 持仓
