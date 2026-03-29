#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
消防商机筛选器 - 入口脚本
"""

from scripts.filter_fire_opportunities import main as _main


def main(params=None):
    """入口函数，直接调用核心逻辑"""
    return _main(params)


if __name__ == '__main__':
    import json
    result = main()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
