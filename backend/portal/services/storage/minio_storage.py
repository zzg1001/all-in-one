"""
MinIO/S3 object storage backend.
"""
import io
import mimetypes
from pathlib import Path
from typing import Optional, List, BinaryIO, Union
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from minio import Minio
from minio.error import S3Error

from .base import StorageBackend, FileInfo


class MinioStorage(StorageBackend):
    """
    MinIO/S3 compatible object storage implementation.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        port: Optional[int] = None,
        secure: bool = False,
        region: Optional[str] = None
    ):
        """
        Initialize MinIO storage.

        Args:
            endpoint: MinIO server endpoint (hostname or IP)
            access_key: Access key ID
            secret_key: Secret access key
            bucket: Bucket name to use
            port: Server port (optional, will be appended to endpoint if provided)
            secure: Use HTTPS if True
            region: AWS region (optional)
        """
        # Build endpoint with port if specified
        if port:
            full_endpoint = f"{endpoint}:{port}"
        else:
            full_endpoint = endpoint

        self.client = Minio(
            full_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region
        )
        self.bucket = bucket
        self.endpoint = endpoint
        self.port = port
        self.secure = secure

        # Thread pool for sync operations
        self._executor = ThreadPoolExecutor(max_workers=4)

        # Ensure bucket exists
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            if e.code != "BucketAlreadyOwnedByYou":
                raise

    def _normalize_path(self, path: str) -> str:
        """Normalize path for object storage."""
        if not path:
            return ""
        # Remove leading/trailing slashes and normalize separators
        return path.replace("\\", "/").strip("/")

    def _get_content_type(self, path: str) -> str:
        """Guess content type from path."""
        content_type, _ = mimetypes.guess_type(path)
        return content_type or "application/octet-stream"

    async def _run_in_executor(self, func, *args):
        """Run a blocking function in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, func, *args)

    async def write_file(
        self,
        path: str,
        content: Union[bytes, str, BinaryIO],
        content_type: Optional[str] = None
    ) -> str:
        """Write content to an object."""
        object_name = self._normalize_path(path)
        content_type = content_type or self._get_content_type(path)

        if isinstance(content, str):
            data = content.encode("utf-8")
            stream = io.BytesIO(data)
            length = len(data)
        elif isinstance(content, bytes):
            stream = io.BytesIO(content)
            length = len(content)
        else:
            # File-like object
            content.seek(0, 2)  # Seek to end
            length = content.tell()
            content.seek(0)  # Seek back to start
            stream = content

        def _put():
            self.client.put_object(
                self.bucket,
                object_name,
                stream,
                length,
                content_type=content_type
            )

        await self._run_in_executor(_put)
        return f"{self.bucket}/{object_name}"

    async def read_file(self, path: str) -> bytes:
        """Read object content as bytes."""
        object_name = self._normalize_path(path)

        def _get():
            response = self.client.get_object(self.bucket, object_name)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        try:
            return await self._run_in_executor(_get)
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {path}")
            raise

    async def read_file_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read object content as text."""
        content = await self.read_file(path)
        return content.decode(encoding)

    async def delete_file(self, path: str) -> bool:
        """Delete an object."""
        object_name = self._normalize_path(path)

        def _remove():
            self.client.remove_object(self.bucket, object_name)

        try:
            await self._run_in_executor(_remove)
            return True
        except S3Error:
            return False

    async def exists(self, path: str) -> bool:
        """Check if an object exists."""
        object_name = self._normalize_path(path)

        def _stat():
            try:
                self.client.stat_object(self.bucket, object_name)
                return True
            except S3Error:
                return False

        # First check if it's a file
        if await self._run_in_executor(_stat):
            return True

        # Check if it's a "directory" (prefix with objects under it)
        def _list():
            objects = self.client.list_objects(
                self.bucket,
                prefix=object_name + "/" if object_name else "",
                recursive=False
            )
            return any(True for _ in objects)

        return await self._run_in_executor(_list)

    async def get_file_info(self, path: str) -> Optional[FileInfo]:
        """Get object metadata."""
        object_name = self._normalize_path(path)

        def _stat():
            try:
                stat = self.client.stat_object(self.bucket, object_name)
                return FileInfo(
                    name=Path(object_name).name,
                    path=path,
                    size=stat.size,
                    modified_time=stat.last_modified.replace(tzinfo=None),
                    is_dir=False,
                    content_type=stat.content_type
                )
            except S3Error:
                return None

        return await self._run_in_executor(_stat)

    async def list_files(
        self,
        path: str = "",
        recursive: bool = False,
        pattern: Optional[str] = None
    ) -> List[FileInfo]:
        """List objects in a prefix."""
        prefix = self._normalize_path(path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        def _list():
            results = []
            objects = self.client.list_objects(
                self.bucket,
                prefix=prefix if prefix != "/" else "",
                recursive=recursive
            )

            for obj in objects:
                name = Path(obj.object_name).name
                if obj.is_dir:
                    name = obj.object_name.rstrip("/").split("/")[-1]

                # Apply pattern filter
                if pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(name, pattern):
                        continue

                results.append(FileInfo(
                    name=name,
                    path=obj.object_name.rstrip("/"),
                    size=obj.size or 0,
                    modified_time=obj.last_modified.replace(tzinfo=None) if obj.last_modified else datetime.now(),
                    is_dir=obj.is_dir,
                    content_type=obj.content_type if hasattr(obj, 'content_type') else None
                ))

            return results

        return await self._run_in_executor(_list)

    async def mkdir(self, path: str) -> bool:
        """
        Create a directory (empty object with trailing slash).
        In object storage, directories are virtual - they exist if objects have that prefix.
        """
        # In MinIO/S3, directories are virtual. We just return True.
        # Optionally create an empty object to represent the directory
        object_name = self._normalize_path(path)
        if not object_name.endswith("/"):
            object_name += "/"

        def _put_dir():
            self.client.put_object(
                self.bucket,
                object_name,
                io.BytesIO(b""),
                0,
                content_type="application/x-directory"
            )

        try:
            await self._run_in_executor(_put_dir)
            return True
        except S3Error:
            return False

    async def rmdir(self, path: str) -> bool:
        """Remove all objects with the given prefix."""
        prefix = self._normalize_path(path)
        if not prefix.endswith("/"):
            prefix += "/"

        def _remove_all():
            objects = self.client.list_objects(
                self.bucket,
                prefix=prefix,
                recursive=True
            )
            for obj in objects:
                self.client.remove_object(self.bucket, obj.object_name)

        try:
            await self._run_in_executor(_remove_all)
            return True
        except S3Error:
            return False

    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        """Copy an object within the bucket."""
        src_name = self._normalize_path(src_path)
        dest_name = self._normalize_path(dest_path)

        def _copy():
            from minio.commonconfig import CopySource
            self.client.copy_object(
                self.bucket,
                dest_name,
                CopySource(self.bucket, src_name)
            )

        try:
            await self._run_in_executor(_copy)
            return True
        except S3Error:
            return False

    async def move_file(self, src_path: str, dest_path: str) -> bool:
        """Move an object (copy + delete)."""
        if await self.copy_file(src_path, dest_path):
            return await self.delete_file(src_path)
        return False

    async def copy_dir(self, src_path: str, dest_path: str) -> bool:
        """Copy all objects with src prefix to dest prefix."""
        src_prefix = self._normalize_path(src_path)
        dest_prefix = self._normalize_path(dest_path)

        if not src_prefix.endswith("/"):
            src_prefix += "/"
        if not dest_prefix.endswith("/"):
            dest_prefix += "/"

        def _copy_all():
            from minio.commonconfig import CopySource
            objects = self.client.list_objects(
                self.bucket,
                prefix=src_prefix,
                recursive=True
            )
            for obj in objects:
                if obj.is_dir:
                    continue
                # Calculate new path
                rel_path = obj.object_name[len(src_prefix):]
                new_name = dest_prefix + rel_path
                self.client.copy_object(
                    self.bucket,
                    new_name,
                    CopySource(self.bucket, obj.object_name)
                )

        try:
            await self._run_in_executor(_copy_all)
            return True
        except S3Error:
            return False

    async def move_dir(self, src_path: str, dest_path: str) -> bool:
        """Move all objects (copy + delete)."""
        if await self.copy_dir(src_path, dest_path):
            return await self.rmdir(src_path)
        return False

    def get_full_path(self, path: str) -> str:
        """Get the full object path (bucket/object)."""
        object_name = self._normalize_path(path)
        return f"{self.bucket}/{object_name}"

    def get_relative_path(self, full_path: str) -> str:
        """Convert full path to relative storage path."""
        # Remove bucket prefix if present
        bucket_prefix = f"{self.bucket}/"
        if full_path.startswith(bucket_prefix):
            return full_path[len(bucket_prefix):]
        return full_path

    async def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
        method: str = "GET"
    ) -> str:
        """Get a presigned URL for direct access."""
        object_name = self._normalize_path(path)

        def _presign():
            if method.upper() == "PUT":
                return self.client.presigned_put_object(
                    self.bucket,
                    object_name,
                    expires=timedelta(seconds=expires_in)
                )
            else:
                return self.client.presigned_get_object(
                    self.bucket,
                    object_name,
                    expires=timedelta(seconds=expires_in)
                )

        return await self._run_in_executor(_presign)

    def get_public_url(self, path: str) -> str:
        """Get the public URL for an object (requires public bucket policy)."""
        object_name = self._normalize_path(path)
        protocol = "https" if self.secure else "http"
        if self.port:
            return f"{protocol}://{self.endpoint}:{self.port}/{self.bucket}/{object_name}"
        return f"{protocol}://{self.endpoint}/{self.bucket}/{object_name}"

    # Sync versions for compatibility
    def write_file_sync_direct(
        self,
        path: str,
        content: Union[bytes, str],
        content_type: Optional[str] = None
    ) -> str:
        """Direct synchronous write without asyncio."""
        object_name = self._normalize_path(path)
        content_type = content_type or self._get_content_type(path)

        if isinstance(content, str):
            data = content.encode("utf-8")
        else:
            data = content

        stream = io.BytesIO(data)
        self.client.put_object(
            self.bucket,
            object_name,
            stream,
            len(data),
            content_type=content_type
        )
        return f"{self.bucket}/{object_name}"

    def read_file_sync_direct(self, path: str) -> bytes:
        """Direct synchronous read without asyncio."""
        object_name = self._normalize_path(path)
        try:
            response = self.client.get_object(self.bucket, object_name)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {path}")
            raise

    def read_file_text_sync_direct(self, path: str, encoding: str = "utf-8") -> str:
        """Direct synchronous text read without asyncio."""
        content = self.read_file_sync_direct(path)
        return content.decode(encoding)

    def exists_sync_direct(self, path: str) -> bool:
        """Direct synchronous exists check without asyncio."""
        object_name = self._normalize_path(path)
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            # Check if it's a prefix
            objects = self.client.list_objects(
                self.bucket,
                prefix=object_name + "/" if object_name else "",
                recursive=False
            )
            return any(True for _ in objects)
