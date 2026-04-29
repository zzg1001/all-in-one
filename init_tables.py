#!/usr/bin/env python3
"""初始化数据库表结构"""
import os
import sys

# 设置环境变量
os.environ['DB_HOST'] = '127.0.0.1'
os.environ['DB_PORT'] = '3306'
os.environ['DB_USER'] = 'root'
os.environ['DB_PASSWORD'] = 'root123456'
os.environ['DB_NAME'] = 'ai_agent'

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import init_db

print("初始化数据库表...")
init_db()
print("完成!")
