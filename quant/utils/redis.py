# -*- coding:utf-8 -*-

"""
Redis async操作接口
    * Redis连接池

Author: HuangTao
Date:   2018/06/06
Update: None
"""

import aioredis

from quant.utils import logger


__all__ = ('initRedisPool', 'exec_redis_cmd')


REDIS_CONN_POOL = None  # redis连接池


async def initRedisPool(host='127.0.0.1', port=6379, db=None, password=None):
    """ 初始化连接池
    """
    global REDIS_CONN_POOL
    address = 'redis://{host}:{port}'.format(host=host, port=port)
    REDIS_CONN_POOL = await aioredis.create_redis_pool(address, db=db, password=password, encoding='utf-8')
    logger.info('create redis pool success.')


async def exec_redis_cmd(*args, **kwargs):
    """ 执行命令
    """
    result = await REDIS_CONN_POOL.execute(*args, **kwargs)
    return result
