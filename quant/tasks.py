# -*- coding:utf-8 -*-

"""
任务模块
1. 注册一个循环执行任务：指定执行函数、指定执行间隔时间、指定函数入参；
2. 启动一个协程来执行函数任务；

Author: HuangTao
Date:   2018/04/26
"""

import asyncio
import inspect

from quant.heartbeat import heartbeat

__all__ = ("LoopRunTask", "SingleTask")


class LoopRunTask(object):
    """ 独立协程 循环执行任务
    """

    @classmethod
    def register(cls, func, interval=1, *args, **kwargs):
        """ 注册一个任务，在每次心跳的时候执行调用
        @param func 心跳的时候执行的函数，必须的async异步函数
        @param interval 执行回调的时间间隔(秒)，必须是整秒
        @return task_id 任务id
        """
        task_id = heartbeat.register(func, interval, *args, **kwargs)
        return task_id

    @classmethod
    def unregister(cls, task_id):
        """ 注销一个任务
        @param task_id 任务id
        """
        heartbeat.unregister(task_id)


class SingleTask:
    """ 独立协程 执行任务
    """

    @classmethod
    def run(cls, func, *args, **kwargs):
        """ 运行独立函数func
        @param func 需要独立在协程里运行的函数，必须的async异步函数
        """
        asyncio.get_event_loop().create_task(func(*args, **kwargs))

    @classmethod
    def call_later(cls, func, delay=0, *args, **kwargs):
        """ 延迟执行func函数
        @param func 需要被执行的函数
        @param delay 函数被延迟执行的时间(秒)，可以为小数，如0.5秒
        """
        if not inspect.iscoroutinefunction(func):
            asyncio.get_event_loop().call_later(delay, func, *args)
        else:
            def foo(f, *args, **kwargs):
                asyncio.get_event_loop().create_task(f(*args, **kwargs))
            asyncio.get_event_loop().call_later(delay, foo, func, *args)
