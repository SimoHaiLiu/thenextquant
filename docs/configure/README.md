
## 配置文件

框架启动的时候，需要指定一个 `json` 格式的配置文件。
- [一个完整的配置文件示例](config.json)


## 配置使用
所有 `config.json` 配置文件里的 `key-value` 格式数据，都可以通过如下方式使用：
```python
from quant.config import config

config.name  # 使用配置里的name字段
config.abc  # 使用配置里的abd字段
```

## 系统配置参数
> 所有系统配置参数均为 `大写字母` 为key;  
> 所有系统配置参数均为 `可选`;  

##### 1. SERVICE
配置需要使用的代理服务，如果不配置，将使用默认的示例配置如下。  

示例：
```json
{
    "SERVICE": {
        "Market": {
            "wss": "wss://thenextquant.com/ws/market"
        },
        "Trade": {
            "wss": "wss://thenextquant.com/ws/trade"
        }
    }
}
```
**配置说明**:
- Market `dict` 行情代理服务配置，可以订阅任意交易平台的任意行情数据
- Trade `dict` 交易代理服务配置，可以在任意平台的任意交易区发起交易


##### 2. LOG
日志配置。包含如下配置：

**示例**:
```json
{
    "LOG": {
        "console": false,
        "level": "DEBUG",
        "path": "/var/log/servers/Quant",
        "name": "quant.log",
        "clear": true,
        "backup_count": 5
    }
}
```

**配置说明**:
- console `boolean` 是否在命令行打印日志 `true 打印日志到命令行` / `false 打印日志到文件`
- level `string` 日志级别 `DEBUG` / `INFO`， 默认 `DEBUG`
- path `string` 日志路径 `默认 /var/log/servers/Quant`
- name `string` 日志文件名 `默认 quant.log`
- clear `boolean` 重启的时候，是否清理历史日志（true将删除整个日志保存文件夹）
- backup_count `int` 日志保存个数（日志按天分割，默认保留5天日志, `0`为永久保存）


##### 3. HEARTBEAT
服务心跳配置。

**示例**:
```json
{
    "HEARTBEAT": {
        "interval": 3,
        "broadcast": 0
    }
}
```

**配置说明**:
- interval `int` 心跳打印时间间隔(秒)，0为不打印 `可选，默认为1`
- broadcast `int` 心跳广播间隔(秒)，0为不广播 `可选，默认为0`
