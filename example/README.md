
## Demo使用示例

#### 推荐创建如下结构的文件及文件夹:
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

#### 策略服务配置

策略服务配置文件为 [config.json](./config.json)，其中:

- platforms `dict` 策略将使用的交易平台配置；
- strategy `string` 策略名称
- symbol `string` 策略运行交易对

> 服务配置文件使用方式: [配置文件](../docs/configure/README.md)


##### 运行

```text
python src/main.py config.json
```
