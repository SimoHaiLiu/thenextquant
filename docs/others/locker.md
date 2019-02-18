
## 进程锁 & 线程锁

当业务复杂到使用多进程或多线程的时候，并发提高的同时，对内存共享也需要使用锁来解决资源争夺问题。


##### 1. 线程（协程）锁

> 使用  

```python
    from quant.utils.decorator import async_method_locker
    
    @async_method_locker("unique_locker_name")
    async def func_foo():
        pass
```

> 说明  
- `async_method_locker` 为装饰器，需要装饰到 `async` 异步函数上；
- 装饰器需要传入一个名字，作为此函数的锁名；


##### 2. 全局（进程）锁

> 使用  

```python
    from quant.utils.decorator import global_locker
    
    @global_locker("unique_locker_name")
    async def func_bar():
        pass
```

> 说明  
- `global_locker` 为装饰器，需要装饰到 `async` 异步函数上；
- 装饰器需要传入一个名字，作为此函数的锁名；
- 需要使用 `redis` 来同步锁信息；
