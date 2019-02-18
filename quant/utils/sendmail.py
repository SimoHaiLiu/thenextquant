# -*- coding:utf-8 -*-


import email
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from quant.utils import logger


class SendEmail:
    """ 发送邮件
    """

    def __init__(self, host, port, username, password, to_emails, subject, content, timeout=30, tls=True):
        """ 初始化
        @param host 邮件服务端主机
        @param port 邮件服务器端口
        @param username 用户名
        @param password 密码
        @param to_emails 发送到邮箱列表
        @param title 标题
        @param content 内容
        @param timeout 超时时间，默认30秒
        @param tls 是否使用TLS，默认使用
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._to_emails = to_emails
        self._subject = subject
        self._content = content
        self._timeout = timeout
        self._tls = tls

    async def send(self):
        """ 发送邮件
        """
        message = MIMEMultipart('related')
        message['Subject'] = self._subject
        message['From'] = self._username
        message['To'] = ",".join(self._to_emails)
        message['Date'] = email.utils.formatdate()
        message.preamble = 'This is a multi-part message in MIME format.'
        ma = MIMEMultipart('alternative')
        mt = MIMEText(self._content, 'plain', 'GB2312')
        ma.attach(mt)
        message.attach(ma)

        smtp = aiosmtplib.SMTP(hostname=self._host, port=self._port, timeout=self._timeout, use_tls=self._tls)
        await smtp.connect()
        await smtp.login(self._username, self._password)
        await smtp.send_message(message)
        logger.info('send email success! FROM:', self._username, 'TO:', self._to_emails, 'CONTENT:', self._content,
                    caller=self)


if __name__ == "__main__":
    h = 'hwhzsmtp.qiye.163.com'
    p = 994
    u = 'huangtao@ifclover.com'
    pw = '123456'
    t = ['huangtao@ifclover.com']
    s = 'Test Send Email 测试'
    c = "Just a test. \n 测试。"

    sender = SendEmail(h, p, u, pw, t, s, c)
    asyncio.get_event_loop().create_task(sender.send())
    asyncio.get_event_loop().run_forever()
