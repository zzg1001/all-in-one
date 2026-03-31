#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键词商机筛选器 - 入口脚本
从上传的Excel文件中按关键词筛选商机，输出Excel

使用方式：
    Agent 配置中提供 keywords 参数，如：["消防", "灭火", "火灾"]
"""

from scripts.filter_fire_opportunities import main as _main


def main(params=None):
    """
    入口函数

    params:
        - file_path: Excel文件路径
        - keywords: 筛选关键词列表（由Agent配置提供）
    """
    return _main(params)


if __name__ == '__main__':
    import json
    result = main()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
