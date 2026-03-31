"""
Demo: Local vs MinIO storage modes comparison.
"""
import sys
import asyncio
import tempfile
import importlib.util
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SERVER_DIR = Path(__file__).parent
sys.path.insert(0, str(SERVER_DIR))

# Direct import to avoid circular imports in services/__init__.py
def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Import in correct order: base first, then implementations
# Also register parent packages to avoid triggering services/__init__.py
import types
sys.modules['services'] = types.ModuleType('services')
sys.modules['services.storage'] = types.ModuleType('services.storage')

storage_base = import_module("services.storage.base", SERVER_DIR / "services/storage/base.py")
storage_local = import_module("services.storage.local", SERVER_DIR / "services/storage/local.py")
storage_minio = import_module("services.storage.minio_storage", SERVER_DIR / "services/storage/minio_storage.py")

LocalStorage = storage_local.LocalStorage
MinioStorage = storage_minio.MinioStorage

from config import get_settings


async def demo():
    settings = get_settings()

    print("=" * 70)
    print("存储模式对比演示")
    print("=" * 70)

    # 测试数据
    test_file = "demo/test.txt"
    test_content = "Hello, 存储测试！"

    # ==================== 本地模式 ====================
    print("\n" + "=" * 70)
    print("【本地模式】 STORAGE_TYPE=local")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        local = LocalStorage(tmpdir)

        print(f"\n基础路径: {tmpdir}")
        print(f"文件路径: {test_file}")

        # 写入
        result = await local.write_file(test_file, test_content)
        print(f"\n写入文件:")
        print(f"  路径: {result}")
        print(f"  实际存储: 本地磁盘文件")

        # 读取
        content = await local.read_file_text(test_file)
        print(f"\n读取文件:")
        print(f"  内容: {content}")

        # 完整路径
        full_path = local.get_full_path(test_file)
        print(f"\n完整路径:")
        print(f"  {full_path}")

        # 文件信息
        info = await local.get_file_info(test_file)
        print(f"\n文件信息:")
        print(f"  名称: {info.name}")
        print(f"  大小: {info.size} bytes")
        print(f"  类型: {'目录' if info.is_dir else '文件'}")

    # ==================== MinIO 模式 ====================
    print("\n" + "=" * 70)
    print("【MinIO模式】 STORAGE_TYPE=minio (默认)")
    print("=" * 70)

    minio = MinioStorage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket="ai-skills",
        port=settings.minio_port,
        secure=settings.minio_secure
    )

    print(f"\n服务器: {settings.minio_endpoint}:{settings.minio_port}")
    print(f"Bucket: ai-skills")
    print(f"对象路径: {test_file}")

    # 写入
    result = await minio.write_file(test_file, test_content)
    print(f"\n写入文件:")
    print(f"  路径: {result}")
    print(f"  实际存储: MinIO 对象存储")

    # 读取
    content = await minio.read_file_text(test_file)
    print(f"\n读取文件:")
    print(f"  内容: {content}")

    # 完整路径
    full_path = minio.get_full_path(test_file)
    print(f"\n完整路径:")
    print(f"  {full_path}")

    # 预签名URL
    url = await minio.get_presigned_url(test_file)
    print(f"\n预签名URL (可直接访问):")
    print(f"  {url[:100]}...")

    # 公开URL
    public_url = minio.get_public_url(test_file)
    print(f"\n公开URL:")
    print(f"  {public_url}")

    # 文件信息
    info = await minio.get_file_info(test_file)
    print(f"\n文件信息:")
    print(f"  名称: {info.name}")
    print(f"  大小: {info.size} bytes")
    print(f"  类型: {'目录' if info.is_dir else '文件'}")

    # 清理
    await minio.delete_file(test_file)

    # ==================== 配置说明 ====================
    print("\n" + "=" * 70)
    print("配置说明")
    print("=" * 70)
    print("""
在 deploy.env 或 .env 中设置:

【使用本地存储】
  STORAGE_TYPE=local
  OUTPUTS_DIR=/app/outputs
  UPLOADS_DIR=/app/uploads
  SKILLS_STORAGE_DIR=/app/skills_storage

【使用 MinIO 存储】 (默认)
  STORAGE_TYPE=minio
  MINIO_ENDPOINT=8.153.198.194
  MINIO_PORT=8092
  MINIO_ACCESS_KEY=admin
  MINIO_SECRET_KEY=yourpassword123
  MINIO_SKILLS_BUCKET=ai-skills
  MINIO_UPLOADS_BUCKET=ai-uploads
  MINIO_OUTPUTS_BUCKET=ai-outputs
""")


if __name__ == "__main__":
    asyncio.run(demo())
