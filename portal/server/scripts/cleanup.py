#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理脚本 - 删除所有已标记删除的数据

使用方式:
    python scripts/cleanup.py

功能:
    - 清理 DataNotes 表中 deleted_at 不为空的记录
    - 清理 Skills 表中 deleted_at 不为空的记录
    - 同时删除本地文件和 MinIO 文件
    - 删除对应的向量索引
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime


def main():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║              数据清理脚本                                 ║
╠══════════════════════════════════════════════════════════╣
║  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                            ║
║  清理: 所有 deleted_at 不为空的数据                       ║
╚══════════════════════════════════════════════════════════╝
""")

    # 执行清理
    from services.cleanup_service import run_cleanup
    asyncio.run(run_cleanup())

    print("\n✓ 清理完成")


if __name__ == "__main__":
    main()
