"""
Storage abstraction test script.
Tests both local and MinIO storage backends.
"""
import asyncio
import sys
import importlib.util
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent to path
SERVER_DIR = Path(__file__).parent
sys.path.insert(0, str(SERVER_DIR))

# Import storage modules directly to avoid circular imports in services/__init__.py
def import_module_directly(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Import storage modules
storage_base = import_module_directly(
    "services.storage.base",
    SERVER_DIR / "services" / "storage" / "base.py"
)
storage_local = import_module_directly(
    "services.storage.local",
    SERVER_DIR / "services" / "storage" / "local.py"
)
storage_minio = import_module_directly(
    "services.storage.minio_storage",
    SERVER_DIR / "services" / "storage" / "minio_storage.py"
)

# Now import config (no circular issues)
from config import get_settings

# Get classes from modules
StorageBackend = storage_base.StorageBackend
FileInfo = storage_base.FileInfo
LocalStorage = storage_local.LocalStorage
MinioStorage = storage_minio.MinioStorage


async def test_storage_backend(storage, name: str):
    """Test a storage backend."""
    print(f"\n{'='*50}")
    print(f"Testing {name} storage")
    print(f"{'='*50}")

    test_dir = "test_storage_dir"
    test_file = f"{test_dir}/test_file.txt"
    test_content = "Hello, Storage! 你好，存储！"

    try:
        # Test 1: Create directory
        print("\n1. Testing mkdir...")
        result = await storage.mkdir(test_dir)
        print(f"   mkdir('{test_dir}'): {result}")

        # Test 2: Write file
        print("\n2. Testing write_file...")
        result = await storage.write_file(test_file, test_content)
        print(f"   write_file('{test_file}'): {result}")

        # Test 3: Check exists
        print("\n3. Testing exists...")
        result = await storage.exists(test_file)
        print(f"   exists('{test_file}'): {result}")

        # Test 4: Read file
        print("\n4. Testing read_file_text...")
        content = await storage.read_file_text(test_file)
        print(f"   read_file_text('{test_file}'): '{content}'")
        assert content == test_content, f"Content mismatch: expected '{test_content}', got '{content}'"
        print("   ✓ Content matches!")

        # Test 5: Get file info
        print("\n5. Testing get_file_info...")
        info = await storage.get_file_info(test_file)
        if info:
            print(f"   File info: name={info.name}, size={info.size}, is_dir={info.is_dir}")
        else:
            print("   File info: None")

        # Test 6: List files
        print("\n6. Testing list_files...")
        files = await storage.list_files(test_dir)
        print(f"   list_files('{test_dir}'): {[f.name for f in files]}")

        # Test 7: Copy file
        print("\n7. Testing copy_file...")
        copy_path = f"{test_dir}/test_file_copy.txt"
        result = await storage.copy_file(test_file, copy_path)
        print(f"   copy_file('{test_file}', '{copy_path}'): {result}")

        # Verify copy
        copy_content = await storage.read_file_text(copy_path)
        assert copy_content == test_content, "Copy content mismatch"
        print("   ✓ Copy content matches!")

        # Test 8: Binary file
        print("\n8. Testing binary file...")
        binary_file = f"{test_dir}/test_binary.bin"
        binary_content = b"\x00\x01\x02\x03\x04\x05"
        await storage.write_file(binary_file, binary_content)
        read_binary = await storage.read_file(binary_file)
        assert read_binary == binary_content, "Binary content mismatch"
        print("   ✓ Binary content matches!")

        # Test 9: Delete file
        print("\n9. Testing delete_file...")
        result = await storage.delete_file(test_file)
        print(f"   delete_file('{test_file}'): {result}")
        exists_after = await storage.exists(test_file)
        print(f"   exists after delete: {exists_after}")

        # Test 10: Remove directory
        print("\n10. Testing rmdir...")
        result = await storage.rmdir(test_dir)
        print(f"   rmdir('{test_dir}'): {result}")

        # Test 11: Presigned URL (MinIO only)
        if isinstance(storage, MinioStorage):
            print("\n11. Testing presigned URL...")
            # Create a test file first
            await storage.mkdir(test_dir)
            await storage.write_file(test_file, test_content)
            url = await storage.get_presigned_url(test_file)
            print(f"   presigned_url: {url[:80]}...")
            # Cleanup
            await storage.rmdir(test_dir)

        print(f"\n✓ All tests passed for {name} storage!")
        return True

    except Exception as e:
        print(f"\n✗ Error testing {name} storage: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup on error
        try:
            await storage.rmdir(test_dir)
        except:
            pass
        return False


async def test_local_storage():
    """Test local filesystem storage."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(tmpdir)
        return await test_storage_backend(storage, "Local Filesystem")


async def test_minio_storage():
    """Test MinIO object storage."""
    settings = get_settings()

    print("\nMinIO Configuration:")
    print(f"  Endpoint: {settings.minio_endpoint}:{settings.minio_port}")
    print(f"  Access Key: {settings.minio_access_key}")
    print(f"  Secure: {settings.minio_secure}")
    print(f"  Default Bucket: {settings.minio_default_bucket}")

    try:
        storage = MinioStorage(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_default_bucket,
            port=settings.minio_port,
            secure=settings.minio_secure
        )
        return await test_storage_backend(storage, "MinIO")
    except Exception as e:
        print(f"\n✗ Failed to connect to MinIO: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_configured_storage():
    """Test the configured storage backend based on settings."""
    settings = get_settings()
    print(f"\nConfigured storage type: {settings.storage_type}")

    # Create storage based on config (without using factory to avoid circular imports)
    if settings.storage_type == "minio":
        storage = MinioStorage(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_default_bucket,
            port=settings.minio_port,
            secure=settings.minio_secure
        )
        print(f"  Created MinioStorage for bucket: {settings.minio_default_bucket}")
    else:
        storage = LocalStorage(settings.local_storage_base_path)
        print(f"  Created LocalStorage at: {settings.local_storage_base_path}")

    return await test_storage_backend(storage, f"Configured ({settings.storage_type})")


async def main():
    """Run all tests."""
    print("="*60)
    print("Storage Abstraction Test Suite")
    print("="*60)

    results = {}

    # Test 1: Local storage
    print("\n" + "="*60)
    print("TEST 1: Local Filesystem Storage")
    print("="*60)
    results["local"] = await test_local_storage()

    # Test 2: MinIO storage
    print("\n" + "="*60)
    print("TEST 2: MinIO Object Storage")
    print("="*60)
    results["minio"] = await test_minio_storage()

    # Test 3: Configured storage
    print("\n" + "="*60)
    print("TEST 3: Configured Storage Backend")
    print("="*60)
    results["configured"] = await test_configured_storage()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {name}: {status}")

    all_passed = all(results.values())
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed!"))
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
