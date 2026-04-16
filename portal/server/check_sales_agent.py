#!/usr/bin/env python3
"""
检查销售Agent的skills配置是否正确
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from config import get_settings

settings = get_settings()
db_url = f'mysql+pymysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}'
engine = create_engine(db_url)

print("=" * 60)
print("检查 Agents 和 Skills 配置")
print("=" * 60)

with engine.connect() as conn:
    # 1. 查看所有Agent
    print("\n【所有 Agents】")
    result = conn.execute(text('SELECT id, name, skills FROM agents WHERE deleted_at IS NULL'))
    agents = list(result)
    for row in agents:
        print(f"  Name: {row[1]}")
        print(f"    ID: {row[0]}")
        print(f"    Skills: {row[2]}")
        print()

    # 2. 查看所有活跃Skill
    print("\n【所有活跃 Skills】")
    result = conn.execute(text('SELECT id, name, folder_path FROM skills WHERE status="active" AND deleted_at IS NULL'))
    skills = list(result)
    for row in result:
        print(f"  Name: {row[1]}")
        print(f"    ID: {row[0]}")
        print(f"    Folder: {row[2]}")

    # 3. 检查销售相关配置
    print("\n" + "=" * 60)
    print("【销售相关配置检查】")
    print("=" * 60)

    # 查找销售Agent
    sales_agent = None
    for agent in agents:
        if '销售' in agent[1]:
            sales_agent = agent
            print(f"\n销售Agent: {agent[1]}")
            print(f"  ID: {agent[0]}")
            print(f"  Skills配置: {agent[2]}")

    if not sales_agent:
        print("\n⚠️ 未找到销售Agent！")

    # 查找销售Skill
    sales_skill = None
    for skill in skills:
        if '销售' in skill[1]:
            sales_skill = skill
            print(f"\n销售Skill: {skill[1]}")
            print(f"  ID: {skill[0]}")
            print(f"  Folder: {skill[2]}")

    if not sales_skill:
        print("\n⚠️ 未找到销售Skill！")

    # 检查是否正确关联
    if sales_agent and sales_skill:
        agent_skills = sales_agent[2]
        skill_id = sales_skill[0]

        if agent_skills and skill_id in str(agent_skills):
            print("\n✅ 销售Agent已正确配置销售Skill")
        else:
            print("\n❌ 销售Agent未配置销售Skill！")
            print(f"   需要将 skill_id '{skill_id}' 添加到 Agent 的 skills 字段")
            print(f"\n修复SQL：")
            print(f"   UPDATE agents SET skills = JSON_ARRAY('{skill_id}') WHERE id = '{sales_agent[0]}';")

print("\n" + "=" * 60)
