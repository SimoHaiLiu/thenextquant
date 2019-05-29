# -*- coding:utf-8 -*-

from distutils.core import setup


setup(
    name="thenextquant",
    version="0.0.4",
    packages=["quant",
              "quant.utils",
              "quant.platform",
              ],
    description="Quant Trader Framework",
    url="https://github.com/TheNextQuant/thenextquant",
    author="huangtao",
    author_email="huangtao@ifclover.com",
    license="MIT",
    keywords=["thenextquant", "quant"],
    install_requires=[
        "aiohttp==3.2.1",
    ],
)
