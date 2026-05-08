"""修复 skills 表中的记录状态"""
from app.core.database import SessionLocal
from portal.models.skill import Skill

db = SessionLocal()

# 查看所有记录的状态
all_skills = db.query(Skill).all()
print(f"总记录数: {len(all_skills)}")

for s in all_skills:
    print(f"  {s.name}: status={s.status}, deleted_at={s.deleted_at}")

# 修复：将所有记录设为 active 且清除 deleted_at
print("\n修复中...")
count = 0
for skill in all_skills:
    changed = False
    if skill.status != "active":
        skill.status = "active"
        changed = True
    if skill.deleted_at is not None:
        skill.deleted_at = None
        changed = True
    if changed:
        count += 1
        print(f"  修复: {skill.name}")

db.commit()
db.close()

print(f"\n完成! 修复了 {count} 条记录")
