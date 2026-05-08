"""从 skills_storage 文件夹恢复技能到数据库"""
import json
from pathlib import Path
from app.core.database import SessionLocal
from app.core.config import get_skills_storage_dir
from portal.models.skill import Skill

def restore_skills():
    db = SessionLocal()
    skills_dir = get_skills_storage_dir()

    print(f"扫描目录: {skills_dir}")

    restored = 0
    skipped = 0
    errors = 0

    for folder in skills_dir.iterdir():
        if not folder.is_dir():
            continue

        skill_id = folder.name

        # 跳过临时文件夹
        if skill_id.startswith("temp_") or skill_id.startswith("upload_"):
            continue

        # 检查数据库中是否已存在
        existing = db.query(Skill).filter(Skill.id == skill_id).first()
        if existing:
            print(f"跳过 (已存在): {skill_id}")
            skipped += 1
            continue

        # 读取 config.json
        config_path = folder / "config.json"
        skill_md_path = folder / "SKILL.md"

        name = skill_id
        description = ""
        icon = "⚡"
        tags = []
        entry_script = "main.py"
        version = "1.0.0"
        author = "restored"

        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                name = config.get("name", skill_id)
                description = config.get("description", "")
                icon = config.get("icon", "⚡")
                tags = config.get("tags", [])
                entry_script = config.get("entry_script", "main.py")
                version = config.get("version", "1.0.0")
                author = config.get("author", "restored")
            except Exception as e:
                print(f"读取 config.json 失败 ({skill_id}): {e}")
        elif skill_md_path.exists():
            # 从 SKILL.md 提取名称
            try:
                content = skill_md_path.read_text(encoding="utf-8")
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("# "):
                        name = line[2:].strip()
                        break
            except:
                pass

        # 检查入口脚本是否存在
        if entry_script and not (folder / entry_script).exists():
            # 尝试找其他 .py 文件
            py_files = list(folder.glob("*.py"))
            if py_files:
                entry_script = py_files[0].name
            else:
                entry_script = None

        try:
            skill = Skill(
                id=skill_id,
                group_id=skill_id,
                name=name,
                description=description,
                icon=icon,
                tags=tags if isinstance(tags, list) else [],
                folder_path=skill_id,
                entry_script=entry_script,
                author=author,
                version=version,
                status="active",
                minio_synced=False
            )
            db.add(skill)
            db.commit()
            print(f"恢复成功: {name} ({skill_id})")
            restored += 1
        except Exception as e:
            db.rollback()
            print(f"恢复失败 ({skill_id}): {e}")
            errors += 1

    db.close()
    print(f"\n完成! 恢复: {restored}, 跳过: {skipped}, 错误: {errors}")

if __name__ == "__main__":
    restore_skills()
