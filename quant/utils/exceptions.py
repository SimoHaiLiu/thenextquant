# -*- coding:utf-8 -*-

"""
错误类型定义
Author: HuangTao
Date:   2018/04/26
Update: None
"""


class CustomException(Exception):
    """ 通用异常类型错误
    """
    default_msg = 'A server error occurred.'
    default_data = None
    default_code = 500

    def __init__(self, msg=None, code=None, data=None):
        self.msg = msg if msg is not None else self.default_msg
        self.code = code if code is not None else self.default_code
        self.data = data

    def __str__(self):
        str_msg = '[{code}] {msg}'.format(code=self.code, msg=self.msg)
        return str_msg


class GlobalLockerException(CustomException):
    """ 全局锁超时异常
    """
    default_msg = 'Global Locker Timeout'
