
## TheNextQuant
异步事件驱动的量化交易/做市系统。


### 框架依赖

- 运行环境
	- python 3.5.3 或以上版本

- 依赖python三方包
	- aioamqp>=0.10.0
	- aiohttp>=3.2.1 `可选`
	- motor>=1.2.1 `可选`


### 安装
使用 `pip` 可以简单方便安装:
```text
pip install -e git+https://github.com/Demon-Hunter/TheNextQuant.git#egg=thenextquant
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
