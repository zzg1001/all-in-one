"""
Test storage integration - upload to MinIO and access via API.
"""
import sys
import asyncio
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings, get_outputs_dir


async def test_integration():
    settings = get_settings()

    print("=" * 70)
    print("存储集成测试")
    print("=" * 70)
    print(f"\n当前存储类型: {settings.storage_type}")

    # 1. 创建本地测试文件
    outputs_dir = get_outputs_dir()
    test_file = outputs_dir / "测试报告_202603.pdf"
    test_content = "%PDF-1.4 Test PDF content with Chinese: 中文测试".encode('utf-8')

    print(f"\n1. 创建本地测试文件: {test_file}")
    test_file.write_bytes(test_content)
    print(f"   文件大小: {test_file.stat().st_size} bytes")

    # 2. 使用 _create_output_file_info 函数
    print("\n2. 调用 _create_output_file_info...")

    # Import the helper function
    import types
    sys.modules['services'] = types.ModuleType('services')
    sys.modules['services.storage'] = types.ModuleType('services.storage')

    import importlib.util
    def import_module(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    SERVER_DIR = Path(__file__).parent
    storage_base = import_module("services.storage.base", SERVER_DIR / "services/storage/base.py")
    storage_minio = import_module("services.storage.minio_storage", SERVER_DIR / "services/storage/minio_storage.py")
    storage_utils = import_module("services.storage.utils", SERVER_DIR / "services/storage/utils.py")

    try:
        result = await storage_utils.upload_local_file_to_storage(test_file)
        print(f"   结果: {result}")

        if settings.storage_type == "minio":
            print(f"\n   ✓ 文件已上传到 MinIO")
            print(f"   URL: {result.get('url')}")

            # 3. 验证可以从 MinIO 读取
            print("\n3. 验证从 MinIO 读取...")
            storage = storage_utils.get_storage_backend()
            content = await storage.read_file(test_file.name)
            print(f"   读取成功: {len(content)} bytes")

            # 4. 清理 MinIO
            print("\n4. 清理 MinIO 文件...")
            await storage.delete_file(test_file.name)
            print("   ✓ 已删除")
        else:
            print(f"\n   本地存储模式，文件保留在: {result.get('path')}")

    except Exception as e:
        print(f"\n   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    # 5. 清理本地文件
    print("\n5. 清理本地测试文件...")
    test_file.unlink(missing_ok=True)
    print("   ✓ 已删除")

    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)

    print("""
使用说明:
--------
1. 当 STORAGE_TYPE=minio 时:
   - 技能生成的文件会自动上传到 MinIO
   - 前端通过 /storage/outputs/{filename} 访问文件
   - MinIO 会处理中文文件名

2. 当 STORAGE_TYPE=local 时:
   - 文件保留在本地 outputs/ 目录
   - 前端通过 /outputs/{filename} 访问文件
""")


if __name__ == "__main__":
    asyncio.run(test_integration())
