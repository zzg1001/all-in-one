#!/usr/bin/env python3
"""从远程数据库同步到本地 Docker MySQL"""
import pymysql
from pymysql.constants import CLIENT
import subprocess
import sys

# 远程数据库配置
REMOTE = {
    'host': '8.153.198.194',
    'port': 63306,
    'user': 'ai_agent',
    'password': 'GhENrpKhfTw5HJkC',
    'database': 'ai_agent'
}

# 本地数据库配置
LOCAL = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'root123456',
    'database': 'ai_agent'
}

def test_connection(config, name):
    """测试数据库连接"""
    try:
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4',
            connect_timeout=10
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", (config['database'],))
        count = cursor.fetchone()[0]
        conn.close()
        print(f"  {name}: 连接成功，{count} 个表")
        return True
    except Exception as e:
        print(f"  {name}: 连接失败 - {e}")
        return False

def get_tables(conn):
    """获取所有表"""
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_create_table(conn, table):
    """获取建表语句"""
    cursor = conn.cursor()
    cursor.execute(f"SHOW CREATE TABLE `{table}`")
    result = cursor.fetchone()
    cursor.close()
    return result[1] if result else None

def get_table_data(conn, table):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `{table}`")
    rows = cursor.fetchall()

    # 获取列信息
    cursor.execute(f"DESCRIBE `{table}`")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns, rows

def sync_database():
    print("=== 数据库同步工具 ===\n")

    # 测试连接
    print("1. 测试连接...")
    if not test_connection(REMOTE, "远程数据库"):
        print("\n无法连接远程数据库，退出")
        return False
    if not test_connection(LOCAL, "本地数据库"):
        print("\n无法连接本地数据库，请确保 Docker MySQL 正在运行")
        return False

    # 连接数据库
    print("\n2. 连接数据库...")
    remote_conn = pymysql.connect(
        host=REMOTE['host'],
        port=REMOTE['port'],
        user=REMOTE['user'],
        password=REMOTE['password'],
        database=REMOTE['database'],
        charset='utf8mb4'
    )

    local_conn = pymysql.connect(
        host=LOCAL['host'],
        port=LOCAL['port'],
        user=LOCAL['user'],
        password=LOCAL['password'],
        database=LOCAL['database'],
        charset='utf8mb4',
        client_flag=CLIENT.MULTI_STATEMENTS
    )
    local_cursor = local_conn.cursor()

    # 禁用外键检查
    local_cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    # 获取远程表
    print("\n3. 获取表结构...")
    tables = get_tables(remote_conn)
    print(f"   找到 {len(tables)} 个表: {', '.join(tables[:10])}{'...' if len(tables) > 10 else ''}")

    # 同步每个表
    print("\n4. 同步数据...")
    success_tables = 0
    total_rows = 0

    for table in tables:
        try:
            # 删除本地表（如果存在）
            local_cursor.execute(f"DROP TABLE IF EXISTS `{table}`")

            # 创建表
            create_sql = get_create_table(remote_conn, table)
            if create_sql:
                local_cursor.execute(create_sql)

            # 复制数据
            columns, rows = get_table_data(remote_conn, table)
            if rows:
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join([f'`{c}`' for c in columns])
                insert_sql = f"INSERT INTO `{table}` ({column_names}) VALUES ({placeholders})"

                for row in rows:
                    try:
                        local_cursor.execute(insert_sql, row)
                    except Exception as e:
                        print(f"   警告: {table} 插入数据失败: {str(e)[:50]}")

                total_rows += len(rows)

            local_conn.commit()
            success_tables += 1
            print(f"   OK {table}: {len(rows)} rows")

        except Exception as e:
            print(f"   FAIL {table}: {e}")

    # 启用外键检查
    local_cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    local_conn.commit()

    # 关闭连接
    remote_conn.close()
    local_conn.close()

    print(f"\n=== 同步完成 ===")
    print(f"成功: {success_tables}/{len(tables)} 个表")
    print(f"总计: {total_rows} 行数据")
    return True

if __name__ == "__main__":
    sync_database()
