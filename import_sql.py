#!/usr/bin/env python3
"""直接通过 PyMySQL 导入 SQL 备份文件"""
import pymysql
from pymysql.constants import CLIENT
import sys


def read_sql_file(filepath):
    """读取 SQL 文件，自动检测编码"""
    with open(filepath, 'rb') as f:
        raw = f.read(4)

    if raw[:2] == b'\xff\xfe':
        encoding = 'utf-16-le'
    elif raw[:2] == b'\xfe\xff':
        encoding = 'utf-16-be'
    else:
        with open(filepath, 'rb') as f:
            sample = f.read(100)
        zero_count = sum(1 for i in range(1, len(sample), 2) if sample[i] == 0)
        encoding = 'utf-16-le' if zero_count > 40 else 'utf-8'

    print(f"检测到编码: {encoding}")

    with open(filepath, 'r', encoding=encoding) as f:
        content = f.read()

    # 移除 BOM
    if content.startswith('\ufeff'):
        content = content[1:]

    return content


def main():
    sql_file = sys.argv[1] if len(sys.argv) > 1 else "backup.sql"
    print(f"=== SQL 导入工具 ===")
    print(f"文件: {sql_file}")

    # 连接数据库（启用多语句模式）
    print("连接数据库...")
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='root123456',
        database='ai_agent',
        charset='utf8mb4',
        autocommit=True,
        client_flag=CLIENT.MULTI_STATEMENTS
    )
    cursor = conn.cursor()

    # 读取 SQL 文件
    print("读取 SQL 文件...")
    sql_content = read_sql_file(sql_file)
    print(f"文件大小: {len(sql_content)} 字符")

    # 直接执行整个文件
    print("执行 SQL...")
    try:
        cursor.execute(sql_content)
        # 处理多结果集
        while True:
            try:
                cursor.nextset()
            except:
                break
        print("\n=== 导入成功！ ===")
    except pymysql.Error as e:
        print(f"\n导入出错: {e}")
        print("\n尝试逐条执行...")

        # 回退到逐条执行
        conn.close()
        conn = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='root123456',
            database='ai_agent',
            charset='utf8mb4',
            autocommit=True
        )
        cursor = conn.cursor()

        # 用分号分割（简单方式）
        statements = sql_content.split(';\n')
        success = 0
        failed = 0

        for idx, stmt in enumerate(statements):
            stmt = stmt.strip()
            if not stmt or stmt.startswith('--'):
                continue
            stmt = stmt + ';'

            try:
                cursor.execute(stmt)
                success += 1
            except pymysql.Error as e:
                if e.args[0] not in (1050, 1062, 1065):  # 表存在、重复键、空查询
                    if idx < 100 or failed < 10:  # 只显示前100条或前10个错误
                        print(f"  语句 {idx + 1} 失败: {str(e)[:100]}")
                    failed += 1

            if (idx + 1) % 100 == 0:
                print(f"  进度: {idx + 1}/{len(statements)}")

        print(f"\n=== 导入完成 ===")
        print(f"成功: {success} 条")
        print(f"失败: {failed} 条")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
