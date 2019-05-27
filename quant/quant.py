# -*- coding:utf-8 -*-

"""
初始化日志、数据库、消息队列、启动服务器心跳

Author: HuangTao
Date:   2017/04/26
"""

import asyncio

from quant.utils import logger
from quant.config import config


class Quant:
    """ 初始化日志、数据库连接，启动服务器心跳
    """

    def __init__(self):
        """ 初始化
        """
        self.loop = None
        self.event_center = None

    def initialize(self, config_module=None):
        """ 初始化
        @param config_module 配置模块
        """
        self._get_event_loop()
        self._load_settings(config_module)
        self._init_logger()
        self._init_db_instance()
        self._init_event_center()
        self._do_heartbeat()

    def start(self):
        """ 启动
        """
        logger.info("start io loop ...", caller=self)
        self.loop.run_forever()

    def _get_event_loop(self):
        """ 获取主事件io loop
        """
        if not self.loop:
            self.loop = asyncio.get_event_loop()
        return self.loop

    def _load_settings(self, config_module):
        """ 加载配置
        """
        config.loads(config_module)

    def _init_logger(self):
        """ 初始化日志
        """
        console = config.log.get("console", True)  # 是否打印日志到命令行
        level = config.log.get("level", "DEBUG")  # 打印日志的级别
        path = config.log.get("path", "/tmp/logs/Quant")  # 日志文件存放的路径
        name = config.log.get("name", "quant.log")  # 日志文件名
        clear = config.log.get("clear", False)  # 是否清理历史日志
        backup_count = config.log.get("backup_count", 0)  # 保存按天分割的日志文件个数
        if console:
            logger.initLogger(level)
        else:
            logger.initLogger(level, path, name, clear, backup_count)

    def _init_db_instance(self):
        """ 初始化数据库对象
        """
        if config.mongodb:
            from quant.utils.mongo import initMongodb
            initMongodb(**config.mongodb)

    def _init_event_center(self):
        """ 初始化事件中心
        """
        if config.rabbitmq:
            from quant.event import EventCenter
            self.event_center = EventCenter()
            self.loop.run_until_complete(self.event_center.connect())
            config.initialize()  # 订阅配置更新事件

    def _do_heartbeat(self):
        """ 服务器心跳
        """
        from quant.heartbeat import heartbeat
        self.loop.call_later(0.5, heartbeat.ticker)


quant = Quant()
