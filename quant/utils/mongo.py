# -*- coding:utf-8 -*-

"""
mongodb async操作接口

Author: HuangTao
Date:   2018/04/28
Update: 2018/12/11  1. 取消初始化使用类变量 DB 和 COLLECTION，直接在 self.__init__ 函数传入 db 和 collection;
                    2. 修改名称 self.conn 到 self._conn;
                    3. 修改名称 self.cursor 到 self._cursor;
"""

import copy

import motor.motor_asyncio
from bson.objectid import ObjectId
from urllib.parse import quote_plus

from quant.utils import tools
from quant.utils import logger


__all__ = ('initMongodb', 'MongoDBBase', )


MONGO_CONN = None
DELETE_FLAG = 'delete'  # True 已经删除，False 或者没有该字段表示没有删除


def initMongodb(host='127.0.0.1', port=27017, username='', password='', dbname='admin'):
    """ 初始化mongodb连接
    """
    if username and password:
        uri = 'mongodb://{username}:{password}@{host}:{port}/{dbname}'.format(username=quote_plus(username),
                                                                              password=quote_plus(password),
                                                                              host=quote_plus(host),
                                                                              port=port,
                                                                              dbname=dbname)
    else:
        uri = "mongodb://{host}:{port}/{dbname}".format(host=host, port=port, dbname=dbname)
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    global MONGO_CONN
    MONGO_CONN = mongo_client
    logger.info('create mongodb connection pool.')


class MongoDBBase(object):
    """ mongodb 数据库操作接口
    """

    def __init__(self, db, collection):
        """ 初始化
        @param db 数据库
        @param collection 表
        """
        self._db = db
        self._collection = collection
        self._conn = MONGO_CONN
        self._cursor = self._conn[db][collection]

    async def get_list(self, spec={}, fields=None, sort=[], skip=0, limit=9999, cursor=None):
        """ 批量获取数据
        @param spec 查询条件
        @param fields 返回数据的字段
        @param sort 排序规则
        @param skip 查询起点
        @param limit 返回数据条数
        @param cursor 查询游标，如不指定默认使用self._cursor
        * NOTE: 必须传入limit，否则默认返回数据条数可能因为pymongo的默认值而改变
        """
        if not cursor:
            cursor = self._cursor
        if '_id' in spec:
            spec['_id'] = self._convert_id_object(spec['_id'])
        spec[DELETE_FLAG] = {'$ne': True}
        datas = []
        result = cursor.find(spec, fields, sort=sort, skip=skip, limit=limit)
        async for item in result:
            item['_id'] = str(item['_id'])
            datas.append(item)
        return datas

    async def find_one(self, spec={}, fields=None, sort=[], cursor=None):
        """ 查找单条数据
        @param spec 查询条件
        @param fields 返回数据的字段
        @param sort 排序规则
        @param cursor 查询游标，如不指定默认使用self._cursor
        """
        if not cursor:
            cursor = self._cursor
        data = await self.get_list(spec, fields, sort, limit=1, cursor=cursor)
        if data:
            return data[0]
        else:
            return None

    async def count(self, spec={}, cursor=None):
        """ 计算数据条数
        @param spec 查询条件
        @param n 返回查询的条数
        @param cursor 查询游标，如不指定默认使用self._cursor
        """
        if not cursor:
            cursor = self._cursor
        spec[DELETE_FLAG] = {'$ne': True}
        n = await cursor.count(spec)
        return n

    async def insert(self, docs_data, cursor=None):
        """ 插入数据
        @param docs_data 插入数据 dict或list
        @param ret_ids 插入数据的id列表
        @param cursor 查询游标，如不指定默认使用self._cursor
        """
        if not cursor:
            cursor = self._cursor
        docs = copy.deepcopy(docs_data)
        ret_ids = []
        is_one = False
        create_time = tools.get_cur_timestamp()
        if not isinstance(docs, list):
            docs = [docs]
            is_one = True
        for doc in docs:
            doc['_id'] = ObjectId()
            doc['create_time'] = create_time
            doc['update_time'] = create_time
            ret_ids.append(str(doc['_id']))
        cursor.insert_many(docs)
        if is_one:
            return ret_ids[0]
        else:
            return ret_ids

    async def update(self, spec, update_fields, upsert=False, multi=False, cursor=None):
        """ 更新
        @param spec 更新条件
        @param update_fields 更新字段
        @param upsert 如果不满足条件，是否插入新数据
        @param multi 是否批量更新
        @return modified_count 更新数据条数
        @param cursor 查询游标，如不指定默认使用self._cursor
        """
        if not cursor:
            cursor = self._cursor
        update_fields = copy.deepcopy(update_fields)
        spec[DELETE_FLAG] = {'$ne': True}
        if '_id' in spec:
            spec['_id'] = self._convert_id_object(spec['_id'])
        set_fields = update_fields.get('$set', {})
        set_fields['update_time'] = tools.get_cur_timestamp()
        update_fields['$set'] = set_fields
        if not multi:
            result = await cursor.update_one(spec, update_fields, upsert=upsert)
            return result.modified_count
        else:
            result = await cursor.update_many(spec, update_fields, upsert=upsert)
            return result.modified_count

    async def delete(self, spec, cursor=None):
        """ 软删除
        @param spec 删除条件
        @return delete_count 删除数据的条数
        @param cursor 查询游标，如不指定默认使用self._cursor
        """
        if not cursor:
            cursor = self._cursor
        spec[DELETE_FLAG] = {'$ne': True}
        if '_id' in spec:
            spec['_id'] = self._convert_id_object(spec['_id'])
        update_fields = {'$set': {DELETE_FLAG: True}}
        delete_count = await self.update(spec, update_fields, multi=True, cursor=cursor)
        return delete_count

    async def remove(self, spec, multi=False, cursor=None):
        """ 彻底删除数据
        @param spec 删除条件
        @param multi 是否全部删除
        @return deleted_count 删除数据的条数
        @param cursor 查询游标，如不指定默认使用self._cursor
        """
        if not cursor:
            cursor = self._cursor
        if not multi:
            result = await cursor.delete_one(spec)
            return result.deleted_count
        else:
            result = await cursor.delete_many(spec)
            return result.deleted_count

    async def distinct(self, key, spec={}, cursor=None):
        """ distinct查询
        @param key 查询的key
        @param spec 查询条件
        @return result 过滤结果list
        @param cursor 查询游标，如不指定默认使用self._cursor
        """
        if not cursor:
            cursor = self._cursor
        spec[DELETE_FLAG] = {'$ne': True}
        if '_id' in spec:
            spec['_id'] = self._convert_id_object(spec['_id'])
        result = await cursor.distinct(key, spec)
        return result

    async def find_one_and_update(self, spec, update_fields, upsert=False, return_document=False, fields=None, cursor=None):
        """ 查询一条指定数据，并修改这条数据
        @param spec 查询条件
        @param update_fields 更新字段
        @param upsert 如果不满足条件，是否插入新数据，默认False
        @param return_document 返回修改之前数据或修改之后数据，默认False为修改之前数据
        @param fields 需要返回的字段，默认None为返回全部数据
        @return result 修改之前或之后的数据
        @param cursor 查询游标，如不指定默认使用self._cursor
        """
        if not cursor:
            cursor = self._cursor
        spec[DELETE_FLAG] = {'$ne': True}
        if '_id' in spec:
            spec['_id'] = self._convert_id_object(spec['_id'])
        set_fields = update_fields.get('$set', {})
        set_fields['update_time'] = tools.get_cur_timestamp()
        update_fields['$set'] = set_fields
        result = await cursor.find_one_and_update(spec, update_fields, projection=fields, upsert=upsert,
                                                  return_document=return_document)
        if result and '_id' in result:
            result['_id'] = str(result['_id'])
        return result

    async def find_one_and_delete(self, spec={}, fields=None, cursor=None):
        """ 查询一条指定数据，并删除这条数据
        @param spec 删除条件
        @param fields 需要返回的字段，默认None为返回全部数据
        @param result 删除之前的数据
        @param cursor 查询游标，如不指定默认使用self._cursor
        """
        if not cursor:
            cursor = self._cursor
        spec[DELETE_FLAG] = {'$ne': True}
        if '_id' in spec:
            spec['_id'] = self._convert_id_object(spec['_id'])
        result = await cursor.find_one_and_delete(spec, projection=fields)
        if result and '_id' in result:
            result['_id'] = str(result['_id'])
        return result

    def _convert_id_object(self, origin):
        """ 将字符串的_id转换成ObjectId类型
        """
        if isinstance(origin, str):
            return ObjectId(origin)
        elif isinstance(origin, (list, set)):
            return [ObjectId(item) for item in origin]
        elif isinstance(origin, dict):
            for key, value in origin.items():
                origin[key] = self._convert_id_object(value)
        return origin
