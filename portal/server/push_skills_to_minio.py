#!/usr/bin/env python
"""
Push Local Skills to MinIO

将本地 skills_storage 目录的文件推送到远程 MinIO 存储

用法:
    # 推送所有 skills
    python push_skills_to_minio.py

    # 推送指定 skill（通过 skill_id）
    python push_skills_to_minio.py 064ae307-55b2-4585-8dda-98376c62201c

    # 只检查不上传（dry-run）
    python push_skills_to_minio.py --dry-run

    # 强制覆盖远程文件
    python push_skills_to_minio.py --force
"""
import sys
import io
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set
import argparse
import mimetypes

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings, get_skills_storage_dir


def get_minio_client():
    """获取 MinIO 客户端"""
    from minio import Minio

    settings = get_settings()
    endpoint = f"{settings.minio_endpoint}:{settings.minio_port}" if settings.minio_port else settings.minio_endpoint

    client = Minio(
        endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure
    )
    return client, settings.minio_skills_bucket


def ensure_bucket(client, bucket: str):
    """确保 bucket 存在"""
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"[INFO] 创建 bucket: {bucket}")
    except Exception as e:
        print(f"[WARN] 检查 bucket 失败: {e}")


def get_remote_files(client, bucket: str, prefix: str = "") -> Set[str]:
    """获取 MinIO 中的所有文件路径"""
    files = set()
    try:
        objects = client.list_objects(bucket, prefix=prefix + "/" if prefix else "", recursive=True)
        for obj in objects:
            if not obj.is_dir:
                files.add(obj.object_name.rstrip("/"))
    except Exception:
        pass
    return files


def push_skill_folder(
    client,
    bucket: str,
    local_folder: Path,
    folder_name: str,
    force: bool = False,
    dry_run: bool = False
) -> dict:
    """
    将本地 skill 文件夹推送到 MinIO

    Args:
        client: MinIO 客户端
        bucket: bucket 名称
        local_folder: 本地文件夹路径
        folder_name: MinIO 中的文件夹名（skill_id）
        force: 强制覆盖远程文件
        dry_run: 只检查不上传

    Returns:
        统计信息 {uploaded: int, skipped: int, failed: int}
    """
    stats = {"uploaded": 0, "skipped": 0, "failed": 0, "files": []}

    if not local_folder.exists():
        print(f"  [SKIP] 本地文件夹不存在: {local_folder}")
        return stats

    # 获取远程已有文件（用于判断是否需要覆盖）
    remote_files = set()
    if not force:
        remote_files = get_remote_files(client, bucket, folder_name)

    # 排除的文件/目录
    exclude_patterns = {"__pycache__", ".pyc", ".pyo", ".git", ".DS_Store"}

    for file_path in local_folder.rglob("*"):
        if file_path.is_file():
            # 跳过排除的文件
            if any(p in str(file_path) for p in exclude_patterns):
                continue

            # 计算相对路径
            rel_path = file_path.relative_to(local_folder)
            minio_path = f"{folder_name}/{rel_path}".replace("\\", "/")

            # 检查是否已存在
            if minio_path in remote_files and not force:
                stats["skipped"] += 1
                continue

            if dry_run:
                print(f"  [DRY-RUN] 将上传: {minio_path}")
                stats["uploaded"] += 1
                stats["files"].append(minio_path)
                continue

            try:
                content = file_path.read_bytes()
                content_type, _ = mimetypes.guess_type(str(file_path))
                content_type = content_type or "application/octet-stream"

                client.put_object(
                    bucket,
                    minio_path,
                    io.BytesIO(content),
                    len(content),
                    content_type=content_type
                )
                stats["uploaded"] += 1
                stats["files"].append(minio_path)
                print(f"  [OK] {minio_path}")
            except Exception as e:
                stats["failed"] += 1
                print(f"  [FAIL] {minio_path}: {e}")

    return stats


def push_all_skills(
    skill_ids: Optional[List[str]] = None,
    force: bool = False,
    dry_run: bool = False
):
    """
    推送所有（或指定的）skill 到 MinIO

    Args:
        skill_ids: 指定的 skill_id 列表，None 表示所有
        force: 强制覆盖
        dry_run: 只检查不上传
    """
    settings = get_settings()

    if settings.get_storage_type_for("skills") != "minio":
        print("[ERROR] Skills 未配置 MinIO 存储，请检查配置")
        print("  需要在 deploy.env 或 .env 中设置: skills_storage_type=minio")
        return

    # 初始化 MinIO 客户端
    try:
        client, bucket = get_minio_client()
        ensure_bucket(client, bucket)
    except Exception as e:
        print(f"[ERROR] MinIO 连接失败: {e}")
        return

    skills_dir = get_skills_storage_dir()
    print(f"\n{'='*60}")
    print(f"[Push Skills to MinIO]")
    print(f"本地目录: {skills_dir}")
    print(f"MinIO: {settings.minio_endpoint}:{settings.minio_port}/{bucket}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模式: {'DRY-RUN (不实际上传)' if dry_run else ('强制覆盖' if force else '增量上传')}")
    print(f"{'='*60}\n")

    # 获取要处理的 skill 文件夹
    if skill_ids:
        folders = [(skills_dir / sid) for sid in skill_ids]
    else:
        # 获取所有子目录（排除隐藏目录）
        folders = [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

    if not folders:
        print("[INFO] 没有找到 skill 文件夹")
        return

    print(f"找到 {len(folders)} 个 skill 文件夹\n")

    total_stats = {"uploaded": 0, "skipped": 0, "failed": 0}

    for folder in folders:
        skill_id = folder.name
        print(f"[{skill_id}]")

        if not folder.exists():
            print(f"  [SKIP] 文件夹不存在\n")
            continue

        stats = push_skill_folder(client, bucket, folder, skill_id, force=force, dry_run=dry_run)

        total_stats["uploaded"] += stats["uploaded"]
        total_stats["skipped"] += stats["skipped"]
        total_stats["failed"] += stats["failed"]

        if stats["uploaded"] == 0 and stats["skipped"] > 0:
            print(f"  已跳过 {stats['skipped']} 个文件（远程已存在）")
        print()

    # 打印总结
    print(f"{'='*60}")
    print(f"[完成]")
    print(f"  上传: {total_stats['uploaded']} 个文件")
    print(f"  跳过: {total_stats['skipped']} 个文件（已存在）")
    print(f"  失败: {total_stats['failed']} 个文件")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="将本地 skill 文件推送到 MinIO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python push_skills_to_minio.py                    # 推送所有 skills
  python push_skills_to_minio.py abc123             # 推送指定 skill
  python push_skills_to_minio.py --dry-run          # 只检查不上传
  python push_skills_to_minio.py --force            # 强制覆盖远程
  python push_skills_to_minio.py abc123 def456      # 推送多个 skills
        """
    )
    parser.add_argument(
        "skill_ids",
        nargs="*",
        help="要推送的 skill_id（不指定则推送所有）"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制覆盖远程已存在的文件"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="只检查不实际上传"
    )

    args = parser.parse_args()

    skill_ids = args.skill_ids if args.skill_ids else None

    push_all_skills(
        skill_ids=skill_ids,
        force=args.force,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
