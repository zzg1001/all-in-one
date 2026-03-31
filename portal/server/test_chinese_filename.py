"""
Test Chinese filename handling in MinIO storage.
"""
import sys
import asyncio
import importlib.util
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SERVER_DIR = Path(__file__).parent
sys.path.insert(0, str(SERVER_DIR))

# Direct import
import types
sys.modules['services'] = types.ModuleType('services')
sys.modules['services.storage'] = types.ModuleType('services.storage')

def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

storage_base = import_module("services.storage.base", SERVER_DIR / "services/storage/base.py")
storage_minio = import_module("services.storage.minio_storage", SERVER_DIR / "services/storage/minio_storage.py")

MinioStorage = storage_minio.MinioStorage
from config import get_settings


async def test_chinese_filename():
    settings = get_settings()

    print("=" * 70)
    print("测试 MinIO 中文文件名")
    print("=" * 70)

    minio = MinioStorage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket="ai-outputs",
        port=settings.minio_port,
        secure=settings.minio_secure
    )

    # 模拟 HR 报告的文件名
    test_cases = [
        "人力资源分析报告_202603.pdf",
        "财务月报_2026年3月.pdf",
        "测试文件.txt",
        "入离职分析报告_202603.pdf",
    ]

    for filename in test_cases:
        print(f"\n{'='*50}")
        print(f"测试文件名: {filename}")
        print(f"{'='*50}")

        path = f"test/{filename}"
        content = f"Test content for {filename}"

        try:
            # 写入
            print(f"\n1. 写入文件...")
            result = await minio.write_file(path, content)
            print(f"   写入成功: {result}")

            # 检查存在
            print(f"\n2. 检查文件存在...")
            exists = await minio.exists(path)
            print(f"   exists('{path}'): {exists}")

            # 读取
            print(f"\n3. 读取文件...")
            read_content = await minio.read_file_text(path)
            print(f"   读取内容: {read_content}")

            # URL
            print(f"\n4. 生成URL...")
            url = await minio.get_presigned_url(path)
            print(f"   预签名URL: {url[:100]}...")

            public_url = minio.get_public_url(path)
            print(f"   公开URL: {public_url}")

            # 列出文件
            print(f"\n5. 列出目录文件...")
            files = await minio.list_files("test/")
            for f in files:
                print(f"   - {f.name}")

            # 清理
            await minio.delete_file(path)
            print(f"\n✓ 测试通过!")

        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()

    # 清理测试目录
    await minio.rmdir("test/")


if __name__ == "__main__":
    asyncio.run(test_chinese_filename())
