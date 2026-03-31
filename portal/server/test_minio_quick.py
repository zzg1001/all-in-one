"""
Quick MinIO connection test script.
Run this to verify MinIO is accessible and configured correctly.

Usage:
    python test_minio_quick.py
"""
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from minio import Minio
from minio.error import S3Error

# MinIO 配置 - 与 config.py 中的默认值一致
MINIO_CONFIG = {
    "endpoint": "8.153.198.194:8092",
    "access_key": "admin",
    "secret_key": "yourpassword123",
    "secure": False
}

BUCKETS = ["ai-skills", "ai-skills-temp", "ai-uploads", "ai-outputs"]


def test_connection():
    """Test MinIO connection and basic operations."""
    print("=" * 60)
    print("MinIO Quick Connection Test")
    print("=" * 60)

    print(f"\nConnecting to MinIO at {MINIO_CONFIG['endpoint']}...")

    try:
        client = Minio(
            MINIO_CONFIG["endpoint"],
            access_key=MINIO_CONFIG["access_key"],
            secret_key=MINIO_CONFIG["secret_key"],
            secure=MINIO_CONFIG["secure"]
        )

        # Test 1: List buckets
        print("\n1. Listing existing buckets...")
        buckets = client.list_buckets()
        print(f"   Found {len(buckets)} buckets:")
        for bucket in buckets:
            print(f"   - {bucket.name}")

        # Test 2: Create required buckets
        print("\n2. Creating/verifying required buckets...")
        for bucket_name in BUCKETS:
            if client.bucket_exists(bucket_name):
                print(f"   ✓ Bucket '{bucket_name}' exists")
            else:
                client.make_bucket(bucket_name)
                print(f"   ✓ Created bucket '{bucket_name}'")

        # Test 3: Write test file
        print("\n3. Testing file write...")
        test_bucket = BUCKETS[0]
        test_object = "test/hello.txt"
        test_content = "Hello, MinIO! 你好，MinIO！".encode("utf-8")

        client.put_object(
            test_bucket,
            test_object,
            io.BytesIO(test_content),
            len(test_content),
            content_type="text/plain"
        )
        print(f"   ✓ Wrote '{test_object}' to bucket '{test_bucket}'")

        # Test 4: Read test file
        print("\n4. Testing file read...")
        response = client.get_object(test_bucket, test_object)
        content = response.read()
        response.close()
        response.release_conn()

        assert content == test_content, "Content mismatch!"
        print(f"   ✓ Read content matches: '{content.decode('utf-8')}'")

        # Test 5: Generate presigned URL
        print("\n5. Testing presigned URL...")
        from datetime import timedelta
        url = client.presigned_get_object(
            test_bucket,
            test_object,
            expires=timedelta(hours=1)
        )
        print(f"   ✓ Presigned URL: {url[:80]}...")

        # Test 6: Delete test file
        print("\n6. Cleaning up test file...")
        client.remove_object(test_bucket, test_object)
        print(f"   ✓ Deleted '{test_object}'")

        print("\n" + "=" * 60)
        print("✓ All tests passed! MinIO is working correctly.")
        print("=" * 60)
        return True

    except S3Error as e:
        print(f"\n✗ MinIO S3 Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Connection Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_connection()
    sys.exit(0 if success else 1)
