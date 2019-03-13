
## 定时任务 & 服务器心跳

定时任务模块可以注册任意多个回调函数，利用服务器每秒执行一次心跳的过程，创建新的协程，在协程里执行回调函数。


##### 1. 服务器心跳配置
```json
{
    "HEARTBEAT": {
        "interval": 1, 
        "broadcast": 10
    }
}
```

**参数说明**:
- interval `int` 心跳打印时间间隔(秒)，0为不打印 `可选，默认1`
- broadcast `int` 心跳广播间隔(秒)，0为不广播 `可选，默认0`

> 配置文件可参考 [服务配置模块](../configure/README.md);


##### 2. 注册回调任务

```python
# 导入心跳模块
from quant.heartbeat import heartbeat

# 定义回调函数
async def function_callback(*args, **kwargs):
    pass

# 回调间隔时间(秒)
callback_interval = 5

# 注册回调函数
task_id = heartbeat.register(function_callback, callback_interval)

# 取消回调函数
heartbeat.unregister(task_id)  # 假设此定时任务已经不需要，那么取消此任务回调
```

> 注意:
- 回调函数 `function_callback` 必须是 `async` 异步的，且入参必须包含 `*args` 和 `**kwargs`；
- 回调时间间隔 `callback_interval` 为秒，默认为1秒；
- 回调函数将会在心跳执行的时候被执行，因此可以对心跳次数 `heartbeat.count` 取余，来确定是否该执行当前任务；
