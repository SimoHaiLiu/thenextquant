# -*- coding:utf-8 -*-

"""
装饰器

Author: HuangTao
Date:   2018/08/03
Update: None
"""

import time
import asyncio
import functools

from quant.utils import tools
from quant.utils.exceptions import GlobalLockerException


# 协程间加锁，锁名对应的锁对象 {"locker_name": locker}
METHOD_LOCKERS = {}

# 全局锁解锁脚本
GLOBAL_UNLOCK_SCRIPT = '''
if redis.call("get",KEYS[1]) == ARGV[1]
then
    return redis.call("del",KEYS[1])
else
    return 0
end
'''


def async_method_locker(name):
    """ 异步方法加锁，用于多个协程执行同一个单列的函数时候，避免共享内存相互修改
    @param name 锁名称
    * NOTE: 此装饰器需要加到async异步方法上
    """
    assert isinstance(name, str)

    def decorating_function(method):
        global METHOD_LOCKERS
        locker = METHOD_LOCKERS.get(name)
        if not locker:
            locker = asyncio.Lock()
            METHOD_LOCKERS[name] = locker

        @functools.wraps(method)
        async def wrapper(*args, **kwargs):
            try:
                await locker.acquire()
                return await method(*args, **kwargs)
            finally:
                locker.release()
        return wrapper
    return decorating_function


def global_locker(name):
    """ 全局锁，用于分布式进程间加锁
    @param name 锁名称
    * NOTE: 此装饰器需要加到async异步方法上
    """
    from quant.utils.redis import exec_redis_cmd
    assert isinstance(name, str)

    def decorating_function(method):

        locker_name = 'global_locker:' + name
        random_value = tools.get_uuid1()  # 获取一个随机值

        @functools.wraps(method)
        async def wrapper(*args, **kwargs):
            try:
                ok = 0
                ct = time.time()
                while not ok:
                    # 如果不存在才执行创建，并且在1秒后自动删除
                    ok = await exec_redis_cmd('SET', locker_name, random_value, 'PX', '1000', 'NX')
                    if ok:
                        break
                    else:
                        if time.time() - ct > 1.0:  # 如果1秒之后还没有获取到全局锁，那么就返回错误
                            raise GlobalLockerException()
                        else:
                            await asyncio.sleep(0.01)
                return await method(*args, **kwargs)
            finally:
                await exec_redis_cmd('EVAL', GLOBAL_UNLOCK_SCRIPT, 1, locker_name, random_value)
        return wrapper
    return decorating_function



# class Test:
#
#     @async_method_locker('fucker')
#     async def test(self):
#         print('hahaha ...')
#
#
# t = Test()
# for _ in range(10):
#     asyncio.get_event_loop().create_task(t.test())
#
# asyncio.get_event_loop().run_forever()
