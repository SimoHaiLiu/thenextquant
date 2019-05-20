# -*- coding:utf-8 -*-

"""
装饰器

Author: HuangTao
Date:   2018/08/03
"""

import asyncio
import functools


# 协程间加锁，锁名对应的锁对象 {"locker_name": locker}
METHOD_LOCKERS = {}


def async_method_locker(name, wait=True):
    """ 异步方法加锁，用于多个协程执行同一个单列的函数时候，避免共享内存相互修改
    @param name 锁名称
    @param wait 如果被锁是否等待，True等待执行完成再返回，False不等待直接返回
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
            if not wait and locker.locked():
                return
            try:
                await locker.acquire()
                return await method(*args, **kwargs)
            finally:
                locker.release()
        return wrapper
    return decorating_function


# class Test:
#
#     @async_method_locker('my_fucker', False)
#     async def test(self, x):
#         print('hahaha ...', x)
#         await asyncio.sleep(0.1)
#
#
# t = Test()
# for i in range(10):
#     asyncio.get_event_loop().create_task(t.test(i))
#
# asyncio.get_event_loop().run_forever()
