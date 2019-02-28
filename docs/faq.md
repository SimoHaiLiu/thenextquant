## FAQ

##### 1. 运行程序报SSL的错
```text
SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1056)')
``` 

- 解决方法
```text
aiohttp在python3.7里可能有兼容性问题，需要做一下简单的处理。

MAC电脑执行以下两条命令:
cd /Applications/Python\ 3.7/
./Install\ Certificates.command
```
