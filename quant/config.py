# -*- coding:utf-8 -*-

"""
服务配置

Author: HuangTao
Date:   2018/05/03
Update: None
"""

import json

from quant.utils import logger


class Config:
    """ 服务配置
    """

    def __init__(self):
        """ 配置项
            `SERVER_ID`     服务ID
            `RUN_TIME_UPDATE`   是否支持配置动态更新
            `LOG`           日志配置
                `console`   是否打印日志到命令行
                `level`     级别 DEBUG/INFO
                `path`      日志保存路径
                `name`      日志名
                `clear`     重启是否清理历史日志
                `backup_count` 保存按天分割的日志文件个数
            `RABBITMQ`      RabbitMQ配置
            `MONGODB`       mongodb配置
            `REDIS`         redis配置
            `PLATFORMS`     交易所配置
            `HEARTBEAT`     服务心跳配置 {"interval": 0, "broadcast": 0}
        """
        self.server_id = None       # 服务id（manager服务创建）
        self.run_time_update = False  # 是否支持配置动态更新
        self.log = {}               # 日志配置
        self.rabbitmq = {}          # RabbitMQ配置
        self.mongodb = {}           # Mongodb配置
        self.redis = {}             # Redis配置
        self.platforms = {}         # 交易所配置
        self.heartbeat = {}         # 服务心跳配置
        self.service = {}           # 代理服务配置

    def initialize(self):
        """ 初始化
        """
        # 订阅事件 做市参数更新
        if self.run_time_update:
            from quant.event import EventConfig
            EventConfig(self.server_id).subscribe(self.on_event_config, False)

    async def on_event_config(self, event):
        """ 更新参数
        @param event 事件对象
        """
        from quant.event import EventConfig
        event = EventConfig().duplicate(event)
        if event.server_id != self.server_id:
            return
        if not isinstance(event.params, dict):
            logger.error('params format error! params:', event.params, caller=self)
            return

        # 将配置文件中的数据按照dict格式解析并设置成config的属性
        self.update(event.params)
        logger.info('config update success!', caller=self)

    def loads(self, config_file=None):
        """ 加载配置
        @param config_file json配置文件
        """
        configures = {}
        if config_file:
            try:
                with open(config_file) as f:
                    data = f.read()
                    configures = json.loads(data)
            except Exception as e:
                print(e)
                exit(0)
            if not configures:
                print('config json file error!')
                exit(0)
        self.update(configures)

    def update(self, update_fields):
        """ 更新配置
        @param update_fields 更新字段
        """
        self.server_id = update_fields.get('SERVER_ID')             # 服务id
        self.run_time_update = update_fields.get('RUN_TIME_UPDATE', False)  # 是否支持配置动态更新
        self.log = update_fields.get('LOG', {})                     # 日志配置
        self.rabbitmq = update_fields.get('RABBITMQ', None)         # RabbitMQ配置
        self.mongodb = update_fields.get('MONGODB', None)           # mongodb配置
        self.redis = update_fields.get('REDIS', None)               # redis配置
        self.platforms = update_fields.get('PLATFORMS', {})         # 交易所配置
        self.heartbeat = update_fields.get('HEARTBEAT', {})         # 服务心跳配置
        self.service = update_fields.get('SERVICE', {})             # 代理服务配置

        # 将配置文件中的数据按照dict格式解析并设置成config的属性
        for k, v in update_fields.items():
            setattr(self, k, v)


config = Config()
