# -*- coding:utf-8 -*-

"""
twilio打电话接口

Author: HuangTao
Date:   2018/12/04
"""

from quant.utils import logger
from quant.utils.http_client import AsyncHttpRequests


class Twilio:
    """ twilio打电话接口
    """
    BASE_URL = "https://api.twilio.com"

    @classmethod
    async def call_phone(cls, account_sid, token, _from, to, proxy=None):
        """ 发送文本消息
        @param account_sid Twilio的Account Sid
        @param token Twilio的Auth Token
        @param _from 拨打出去的电话号码 eg: +17173666644
        @param to 被拨的电话号码 eg: +8513123456789
        @param proxy HTTP代理
        """
        url = "https://{account_sid}:{token}@api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json".format(
            account_sid=account_sid,
            token=token
        )
        data = {
            "Url": "http://demo.twilio.com/docs/voice.xml",
            "To": to,
            "From": _from
        }
        result = await AsyncHttpRequests.fetch("POST", url, body=data, proxy=proxy)
        logger.info("url:", url, "result:", result, caller=cls)
