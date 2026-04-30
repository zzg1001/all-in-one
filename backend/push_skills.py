#!/usr/bin/env python3
"""
推送本地 Skills 到远程 MinIO

使用方法:
    python push_skills.py              # 推送所有技能
    python push_skills.py <skill_id>   # 推送指定技能
"""
import os
import sys
import asyncio
from pathlib import Path

# === 在导入其他模块之前，先设置本地开发环境 ===
# 强制设置 DB_HOST 为 localhost（本地开发时 docker 容器名无法解析）
os.environ["DB_HOST"] = "localhost"

# 加载 deploy.env 其他配置
deploy_env = Path(__file__).parent.parent / "deploy.env"
if deploy_env.exists():
    with open(deploy_env, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # DB_HOST 已经设置为 localhost，跳过
                if key == "DB_HOST":
                    continue
                os.environ.setdefault(key, value)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings, get_skills_storage_dir
from app.core.database import SessionLocal
from portal.models.skill import Skill
from portal.services.storage.utils import sync_skill_folder_to_minio, is_minio_storage


async def push_skill(skill_id: str) -> dict:
    """推送单个技能到 MinIO"""
    db = SessionLocal()
    try:
        skill = db.query(Skill).filter(
            Skill.id == skill_id,
            Skill.deleted_at.is_(None)
        ).first()

        if not skill:
            return {"success": False, "error": f"技能不存在: {skill_id}"}

        if not skill.folder_path:
            return {"success": False, "error": "技能没有配置文件夹"}

        skills_dir = get_skills_storage_dir()
        skill_folder = skills_dir / skill.folder_path

        if not skill_folder.exists():
            return {"success": False, "error": f"本地文件夹不存在: {skill_folder}"}

        count = await sync_skill_folder_to_minio(skill_folder, skill.folder_path)
        return {
            "success": True,
            "skill_id": skill_id,
            "skill_name": skill.name,
            "uploaded_files": count
        }
    finally:
        db.close()


async def push_all_skills() -> dict:
    """推送所有技能到 MinIO"""
    db = SessionLocal()
    try:
        skills = db.query(Skill).filter(
            Skill.deleted_at.is_(None),
            Skill.folder_path.isnot(None)
        ).all()

        if not skills:
            return {"success": True, "message": "没有需要推送的技能", "total": 0}

        skills_dir = get_skills_storage_dir()
        total_uploaded = 0
        success_count = 0
        results = []

        for skill in skills:
            skill_folder = skills_dir / skill.folder_path
            if skill_folder.exists():
                try:
                    count = await sync_skill_folder_to_minio(skill_folder, skill.folder_path)
                    total_uploaded += count
                    success_count += 1
                    results.append(f"  OK {skill.name}: {count} 个文件")
                except Exception as e:
                    results.append(f"  FAIL {skill.name}: {e}")
            else:
                results.append(f"  SKIP {skill.name}: 本地文件夹不存在")

        return {
            "success": True,
            "total_skills": len(skills),
            "success_count": success_count,
            "total_uploaded": total_uploaded,
            "details": results
        }
    finally:
        db.close()


async def main():
    print("=" * 50)
    print("Skills 推送工具 (本地 → MinIO)")
    print("=" * 50)

    # 检查 MinIO 配置
    if not is_minio_storage("skills"):
        print("\n错误: Skills 未配置 MinIO 存储")
        print("请检查 deploy.env 中的 MINIO_* 配置")
        return

    settings = get_settings()
    print(f"\nMinIO: {settings.minio_endpoint}:{settings.minio_port}")
    print(f"Bucket: {settings.minio_skills_bucket}")

    # 获取命令行参数
    if len(sys.argv) > 1:
        skill_id = sys.argv[1]
        print(f"\n推送技能: {skill_id}")
        result = await push_skill(skill_id)

        if result["success"]:
            print(f"\n成功! 上传 {result['uploaded_files']} 个文件")
            print(f"技能: {result['skill_name']}")
        else:
            print(f"\n失败: {result['error']}")
    else:
        print("\n推送所有技能...")
        result = await push_all_skills()

        print("\n详情:")
        for line in result.get("details", []):
            print(line)

        print(f"\n总计: {result['success_count']}/{result['total_skills']} 个技能成功")
        print(f"上传: {result['total_uploaded']} 个文件")

    print("\n" + "=" * 50)
    print("完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
