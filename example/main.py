# -*- coding:utf-8 -*-

import sys


def initialize():
    from strategy import MyStrategy
    s = MyStrategy()
    s.initialize()


def main():
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = None

    from quant.quant import quant
    quant.initialize(config_file)
    initialize()
    quant.start()


if __name__ == '__main__':
    main()
