#!/usr/bin/env python3
"""
数据库初始化脚本
执行 init_db.sql 初始化数据库表和默认数据

会自动从 deploy.env 读取数据库配置
"""
import pymysql
from pymysql.constants import CLIENT
import os
from pathlib import Path


def load_config():
    """从 deploy.env 加载数据库配置"""
    config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': 'root123456',
        'database': 'ai_agent'
    }

    deploy_env = Path(__file__).parent.parent / "deploy.env"
    if deploy_env.exists():
        with open(deploy_env, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()

                    if key == "DB_HOST":
                        # mysql 是 docker 容器名，本地用 localhost
                        config['host'] = "127.0.0.1" if value == "mysql" else value
                    elif key == "DB_PORT":
                        config['port'] = int(value)
                    elif key == "DB_USER":
                        config['user'] = value
                    elif key == "DB_PASSWORD":
                        config['password'] = value
                    elif key == "DB_NAME":
                        config['database'] = value

    return config


DB_CONFIG = load_config()


def init_database():
    print("=" * 50)
    print("数据库初始化脚本")
    print(f"目标: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print("=" * 50)

    # 读取 SQL 文件
    sql_file = os.path.join(os.path.dirname(__file__), 'init_db.sql')
    print(f"\n[1/3] 读取 SQL 文件: {sql_file}")

    if not os.path.exists(sql_file):
        print(f"错误: 找不到 {sql_file}")
        return False

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 连接数据库（不指定 database，先创建库）
    print("\n[2/3] 连接数据库...")
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset='utf8mb4',
            client_flag=CLIENT.MULTI_STATEMENTS
        )
        cursor = conn.cursor()
        print("连接成功！")
    except Exception as e:
        print(f"连接失败: {e}")
        return False

    # 创建数据库
    print(f"\n创建数据库 {DB_CONFIG['database']}（如果不存在）...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE `{DB_CONFIG['database']}`")
    conn.commit()

    # 执行 SQL
    print("\n[3/3] 执行初始化 SQL...")
    try:
        # 分割 SQL 语句执行
        statements = sql_content.split(';')
        success = 0
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    cursor.execute(stmt)
                    conn.commit()
                    success += 1
                except Exception as e:
                    # 忽略一些可预期的错误
                    if 'already exists' not in str(e).lower():
                        print(f"警告: {str(e)[:80]}")

        print(f"执行了 {success} 条语句")
    except Exception as e:
        print(f"执行 SQL 错误: {e}")
        return False

    # 验证
    print("\n验证初始化结果...")
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM agents")
    agent_count = cursor.fetchone()[0]

    print(f"  - 用户表: {user_count} 条记录")
    print(f"  - Agent表: {agent_count} 条记录")

    conn.close()

    print("\n" + "=" * 50)
    print("初始化完成！")
    print("=" * 50)
    print("\n默认账号:")
    print("  - admin / admin123 (管理员)")
    print("  - boss / boss123 (领导)")
    print("  - test / test123 (测试用户)")
    return True


if __name__ == "__main__":
    init_database()
