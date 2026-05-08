"""修复 skills 表中的 tags 字段"""
from app.core.database import SessionLocal
from portal.models.skill import Skill

db = SessionLocal()

all_skills = db.query(Skill).all()
print(f"检查 {len(all_skills)} 条记录...")

count = 0
for skill in all_skills:
    if not isinstance(skill.tags, list):
        print(f"  修复: {skill.name}, tags={skill.tags} -> []")
        skill.tags = []
        count += 1

db.commit()
db.close()

print(f"\n完成! 修复了 {count} 条记录")
