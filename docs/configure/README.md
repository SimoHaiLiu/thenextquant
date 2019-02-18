
## 配置文件

框架启动的时候，需要指定一个 `json` 格式的配置文件。
- [一个完整的配置文件示例](config.json)


## 配置使用
所有 `config.json` 配置文件里的 `key-value` 格式数据，都可以通过如下方式使用：
```python
from quant.config import config

config.server_id
config.abc
```

## 系统配置参数
> 所有系统配置参数均为 `大写字母` 为key;  
> 所有系统配置参数均为 `可选`;  

##### 1. SERVER_ID
服务id，唯一指定每个运行的服务。  

示例：
```json
	{
		"SERVER_ID": "5b16406f9870140001c29607"
	}
```


##### 1. RUN_TIME_UPDATE
是否允许动态更新服务配置。  

示例：
```json
	{
		"RUN_TIME_UPDATE": true
	}
```


##### 3. RABBITMQ
RabbitMQ配置。

**示例**:
```json
	{
		"RABBITMQ": {
			"host": "127.0.0.1",
			"port": 5672,
			"username": "quant",
			"password": "test123456"
		}
	}
```

**配置说明**:
- host `string` host地址
- port `int` 端口
- username `string` 用户名
- password `string` 密码


##### 4. MONGODB
MongoDB配置。

**示例**:
```json
	{
		"MONGODB": {
			"host": "127.0.0.1",
			"port": 5672,
			"username": "quant",
			"password": "test123456"
		}
	}
```

**配置说明**:
- host `string` host地址
- port `int` 端口
- username `string` 用户名
- password `string` 密码


##### 5. REDIS
Redis配置。

**示例**:
```json
	{
		"REDIS": {
			"host": "127.0.0.1",
			"port": 5672,
			"password": "test123456"
		}
	}
```

**配置说明**:
- host `string` host地址
- port `int` 端口
- password `string` 密码


##### 6. LOG
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


##### 7. HEARTBEAT
服务心跳配置。

**示例**:
```json
	{
		"HEARTBEAT": {
            "interval": 3,
            "broadcast": 5
        }
	}
```

**配置说明**:
- interval `int` 心跳打印时间间隔(秒)，0为不打印 `可选，默认为1`
- broadcast `int` 心跳广播间隔(秒)，0为不广播 `可选，默认为0`
