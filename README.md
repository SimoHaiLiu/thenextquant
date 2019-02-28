
## TheNextQuant
异步事件驱动的量化交易/做市系统。


### 框架依赖

- 运行环境
	- python 3.5.3 或以上版本

- 依赖python三方包
	- aiohttp>=3.2.1


### 安装
使用 `pip` 可以简单方便安装:
```text
pip install -e git+https://github.com/TheNextQuant/thenextquant.git#egg=thenextquant
```

or

```text
pip install thenextquant
```

### Demo使用示例

- 推荐创建如下结构的文件及文件夹:
```text
ProjectName
    |----- docs
    |       |----- README.md
    |----- scripts
    |       |----- run.sh
    |----- config.json
    |----- src
    |       |----- main.py
    |       |----- strategy
    |               |----- strategy1.py
    |               |----- strategy2.py
    |               |----- ...
    |----- .gitignore
    |----- README.md
```

- 快速体验示例
    [Demo](example)


- 运行
```text
python src/main.py config.json
```


### 使用文档

本框架使用的是Python原生异步库(asyncio)实现异步事件驱动，所以在使用之前，需要先了解 [Python Asyncio](https://docs.python.org/3/library/asyncio.html)。

- [服务配置](docs/configure/README.md)
- [日志打印](docs/others/logger.md)
- [行情](docs/market.md)
- [交易](docs/trade.md)
- [定时任务 & 服务器心跳](docs/others/tasks.md)


### FAQ
- [FAQ](docs/faq.md)
