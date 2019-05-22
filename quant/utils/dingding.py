# -*- coding:utf-8 -*-

"""
钉钉机器人接口

Author: HuangTao
Date:   2018/08/04
"""

from quant.utils import logger
from quant.utils.http_client import AsyncHttpRequests


class DingTalk:
    """ 钉钉机器人接口
    """
    BASE_URL = "https://oapi.dingtalk.com/robot/send?access_token="

    @classmethod
    async def send_text_msg(cls, access_token, content, phones=None, is_at_all=False):
        """ 发送文本消息
        @param access_token 钉钉消息access_token
        @param content 消息内容
        @param phones 需要@提醒的群成员手机号列表
        @param is_at_all 是否需要@所有人，默认为False
        """
        body = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        if is_at_all:
            body["at"] = {"isAtAll": True}
        if phones:
            assert isinstance(phones, list)
            body["at"] = {"atMobiles": phones}
        url = cls.BASE_URL + access_token
        headers = {"Content-Type": "application/json"}
        result = await AsyncHttpRequests.post(url, data=body, headers=headers)
        logger.info("url:", url, "body:", body, "result:", result, caller=cls)

    @classmethod
    async def send_markdown_msg(cls, access_token, title, text, phones=None, is_at_all=False):
        """ 发送文本消息
        @param access_token 钉钉消息access_token
        @param title 首屏会话透出的展示内容
        @param text markdown格式的消息
        @param phones 需要@提醒的群成员手机号列表
        @param is_at_all 是否需要@所有人，默认为False
        """
        body = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            }
        }
        if is_at_all:
            body["at"] = {"isAtAll": True}
        if phones:
            assert isinstance(phones, list)
            body["at"] = {"atMobiles": phones}
        url = cls.BASE_URL + access_token
        headers = {"Content-Type": "application/json"}
        result = await AsyncHttpRequests.post(url, data=body, headers=headers)
        logger.info("url:", url, "body:", body, "result:", result, caller=cls)
