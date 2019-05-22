# -*- coding:utf-8 -*-

"""
aiohttp client接口封装

Author: HuangTao
Date:   2018/05/03
"""

import aiohttp
from urllib.parse import urlparse

from quant.utils import logger
from quant.config import config


class AsyncHttpRequests(object):
    """ HTTP异步请求封装
    """

    _SESSIONS = {}  # 每个域名保持一个公用的session连接（每个session持有自己的连接池），这样可以节省资源、加快请求速度

    @classmethod
    async def fetch(cls, method, url, params=None, body=None, data=None, headers=None, timeout=30, **kwargs):
        """ 发起HTTP请求
        @param method 请求方法 GET/POST/PUT/DELETE
        @param url 请求的url
        @param params 请求的uri参数
        @param body 请求的body参数
        @param data json格式的数据
        @param headers 请求的headers
        @param timeout 超时时间(秒)
        @return (code, success, error) 如果成功，error为None，失败success为None，error为失败信息
        """
        session = cls._get_session(url)
        if not kwargs.get("proxy"):
            kwargs["proxy"] = config.proxy  # HTTP代理配置
        try:
            if method == "GET":
                response = await session.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
            elif method == "POST":
                response = await session.post(url, params=params, data=body, json=data, headers=headers,
                                              timeout=timeout, **kwargs)
            elif method == "PUT":
                response = await session.put(url, params=params, data=body, json=data, headers=headers,
                                             timeout=timeout, **kwargs)
            elif method == "DELETE":
                response = await session.delete(url, params=params, data=body, json=data, headers=headers,
                                                timeout=timeout, **kwargs)
            else:
                error = "http method error!"
                return None, None, error
        except Exception as e:
            logger.error("method:", method, "url:", url, "params:", params, "body:", body, "data:", data, "Error:", e,
                         caller=cls)
            return None, None, e
        code = response.status
        if code not in (200, 201, 202, 203, 204, 205, 206):
            text = await response.text()
            logger.error("method:", method, "url:", url, "params:", params, "body:", body, "headers:", headers,
                         "code:", code, "result:", text, caller=cls)
            return code, None, text
        try:
            result = await response.json()
        except:
            logger.warn("response data is not json format!", "method:", method, "url:", url, "params:", params,
                        caller=cls)
            result = await response.text()
        logger.debug("method:", method, "url:", url, "params:", params, "body:", body, "data:", data,
                     "code:", code, "result:", result, caller=cls)
        return code, result, None

    @classmethod
    async def get(cls, url, params=None, body=None, data=None, headers=None, timeout=30, **kwargs):
        """ HTTP GET 请求
        """
        result = await cls.fetch("GET", url, params, body, data, headers, timeout, **kwargs)
        return result

    @classmethod
    async def post(cls, url, params=None, body=None, data=None, headers=None, timeout=30, **kwargs):
        """ HTTP POST 请求
        """
        result = await cls.fetch("POST", url, params, body, data, headers, timeout, **kwargs)
        return result

    @classmethod
    async def delete(cls, url, params=None, body=None, data=None, headers=None, timeout=30, **kwargs):
        """ HTTP DELETE 请求
        """
        result = await cls.fetch("DELETE", url, params, body, data, headers, timeout, **kwargs)
        return result

    @classmethod
    async def put(cls, url, params=None, body=None, data=None, headers=None, timeout=30, **kwargs):
        """ HTTP PUT 请求
        """
        result = await cls.fetch("PUT", url, params, body, data, headers, timeout, **kwargs)
        return result

    @classmethod
    def _get_session(cls, url):
        """ 获取url对应的session连接
        """
        parsed_url = urlparse(url)
        key = parsed_url.netloc or parsed_url.hostname
        if key not in cls._SESSIONS:
            session = aiohttp.ClientSession()
            cls._SESSIONS[key] = session
        return cls._SESSIONS[key]
