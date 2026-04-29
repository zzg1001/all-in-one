#!/usr/bin/env python3
"""测试导入单条语句"""
import pymysql
import re
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv("deploy.env")
load_dotenv(".env")

# 数据库配置
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_agent")

def read_sql_file(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read(4)
    if raw[:2] == b'\xff\xfe':
        encoding = 'utf-16-le'
    else:
        encoding = 'utf-8'
    with open(filepath, 'r', encoding=encoding) as f:
        content = f.read()
    if content.startswith('\ufeff'):
        content = content[1:]
    return content

# 读取文件
content = read_sql_file("backup.sql")

# 提取 agents INSERT 语句
match = re.search(r"INSERT INTO `agents` VALUES \([^;]+\);", content, re.DOTALL)
if match:
    stmt = match.group(0)
    print(f"找到 INSERT 语句，长度: {len(stmt)}")

    # 分析第一条记录
    # 找到第一个 ),( 或 ); 来截取第一条记录
    first_record_end = stmt.find("),(")
    if first_record_end == -1:
        first_record_end = stmt.find(");")
    first_record = stmt[:first_record_end+1] if first_record_end > 0 else stmt[:500]

    # 统计单引号
    quote_count = first_record.count("'")
    print(f"第一条记录中单引号数量: {quote_count}")
    print(f"第一条记录长度: {len(first_record)}")

    # 检查是否有未转义的单引号问题
    # 找出所有字段
    import re
    values_match = re.search(r"VALUES \((.+?)\)(?:,|\);)", stmt[:2000], re.DOTALL)
    if values_match:
        print(f"\n第一条记录内容:")
        print(values_match.group(0)[:500])

    # 尝试执行
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    try:
        # 替换转义引号
        stmt_fixed = stmt.replace('\\"', '"')
        print(f"\n修复后语句长度: {len(stmt_fixed)}")
        cursor.execute(stmt_fixed)
        conn.commit()
        print("执行成功!")
        cursor.execute("SELECT COUNT(*) FROM agents")
        print(f"agents 表行数: {cursor.fetchone()[0]}")
    except Exception as e:
        print(f"\n执行失败: {e}")

    cursor.close()
    conn.close()
else:
    print("未找到 INSERT 语句")
