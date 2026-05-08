"""检查数据库中的 skills 状态"""
from app.core.database import SessionLocal
from portal.models.skill import Skill

db = SessionLocal()

# 查看所有 skills
all_skills = db.query(Skill).all()
print(f"总记录数: {len(all_skills)}")

# 查看活跃的 skills
active_skills = db.query(Skill).filter(
    Skill.status == "active",
    Skill.deleted_at.is_(None)
).all()
print(f"活跃记录数: {len(active_skills)}")

# 查看被软删除的 skills
deleted_skills = db.query(Skill).filter(Skill.deleted_at.isnot(None)).all()
print(f"软删除记录数: {len(deleted_skills)}")

# 查看 deprecated 的 skills
deprecated_skills = db.query(Skill).filter(Skill.status == "deprecated").all()
print(f"Deprecated 记录数: {len(deprecated_skills)}")

print("\n所有记录:")
for s in all_skills:
    print(f"  - {s.name}: status={s.status}, deleted_at={s.deleted_at}, folder={s.folder_path}")

db.close()
