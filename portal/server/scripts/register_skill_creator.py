"""
注册 skill-creator 核心技能到数据库

运行方式:
cd product-background
python scripts/register_skill_creator.py
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings
from models.skill import Skill

settings = get_settings()

# 构建数据库 URL
db_url = f"mysql+pymysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def register_skill_creator():
    db = SessionLocal()
    try:
        # 检查是否已存在
        existing = db.query(Skill).filter(Skill.name == "skill-creator").first()
        if existing:
            print(f"skill-creator 已存在 (id: {existing.id})")
            # 更新 folder_path 确保指向正确位置
            if existing.folder_path != "skill-creator":
                existing.folder_path = "skill-creator"
                db.commit()
                print(f"已更新 folder_path")
            return existing.id

        # 创建新记录
        skill = Skill(
            id="skill-creator",  # 使用固定 ID
            group_id="skill-creator",
            name="skill-creator",
            description="Create new skills, modify and improve existing skills. Use when users want to create a skill from scratch, edit, or optimize an existing skill.",
            icon="🛠️",
            tags=["system", "create", "skill"],
            folder_path="skill-creator",  # 指向完整的 skill-creator 文件夹
            entry_script=None,
            author="system",
            version="1.0.0",
            status="active",
            output_config={"enabled": False}
        )

        db.add(skill)
        db.commit()
        print(f"skill-creator 注册成功 (id: {skill.id})")
        print(f"folder_path: {skill.folder_path}")
        return skill.id

    except Exception as e:
        print(f"注册失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    register_skill_creator()
