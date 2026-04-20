"""
Local filesystem storage backend.
"""
import os
import shutil
import mimetypes
from pathlib import Path
from typing import Optional, List, BinaryIO, Union
from datetime import datetime
import fnmatch
import aiofiles
import aiofiles.os

try:
    from .base import StorageBackend, FileInfo
except ImportError:
    from portal.services.storage.base import StorageBackend, FileInfo


class LocalStorage(StorageBackend):
    """
    Local filesystem storage implementation.
    """

    def __init__(self, base_path: str):
        """
        Initialize local storage.

        Args:
            base_path: Base directory for all storage operations
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """Resolve relative path to absolute path within base_path."""
        if not path:
            return self.base_path
        # Normalize path separators and remove leading slashes
        normalized = path.replace("\\", "/").lstrip("/")
        full_path = (self.base_path / normalized).resolve()
        # Security check: ensure path is within base_path
        if not str(full_path).startswith(str(self.base_path)):
            raise ValueError(f"Path '{path}' is outside storage base directory")
        return full_path

    async def write_file(
        self,
        path: str,
        content: Union[bytes, str, BinaryIO],
        content_type: Optional[str] = None
    ) -> str:
        """Write content to a file."""
        full_path = self._resolve_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, str):
            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)
        elif isinstance(content, bytes):
            async with aiofiles.open(full_path, "wb") as f:
                await f.write(content)
        else:
            # File-like object
            async with aiofiles.open(full_path, "wb") as f:
                while chunk := content.read(8192):
                    await f.write(chunk)

        return str(full_path)

    async def read_file(self, path: str) -> bytes:
        """Read file content as bytes."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def read_file_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read file content as text."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        async with aiofiles.open(full_path, "r", encoding=encoding) as f:
            return await f.read()

    async def delete_file(self, path: str) -> bool:
        """Delete a file."""
        full_path = self._resolve_path(path)
        if full_path.exists() and full_path.is_file():
            await aiofiles.os.remove(full_path)
            return True
        return False

    async def exists(self, path: str) -> bool:
        """Check if a file or directory exists."""
        full_path = self._resolve_path(path)
        return full_path.exists()

    async def get_file_info(self, path: str) -> Optional[FileInfo]:
        """Get file metadata."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            return None

        stat = full_path.stat()
        content_type, _ = mimetypes.guess_type(str(full_path))

        return FileInfo(
            name=full_path.name,
            path=path,
            size=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            is_dir=full_path.is_dir(),
            content_type=content_type
        )

    async def list_files(
        self,
        path: str = "",
        recursive: bool = False,
        pattern: Optional[str] = None
    ) -> List[FileInfo]:
        """List files in a directory."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            return []

        results = []
        if recursive:
            items = full_path.rglob("*")
        else:
            items = full_path.iterdir()

        for item in items:
            if pattern and not fnmatch.fnmatch(item.name, pattern):
                continue

            rel_path = str(item.relative_to(self.base_path)).replace("\\", "/")
            stat = item.stat()
            content_type, _ = mimetypes.guess_type(str(item))

            results.append(FileInfo(
                name=item.name,
                path=rel_path,
                size=stat.st_size if item.is_file() else 0,
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                is_dir=item.is_dir(),
                content_type=content_type
            ))

        return results

    async def mkdir(self, path: str) -> bool:
        """Create a directory."""
        full_path = self._resolve_path(path)
        full_path.mkdir(parents=True, exist_ok=True)
        return True

    async def rmdir(self, path: str) -> bool:
        """Remove a directory and all its contents."""
        full_path = self._resolve_path(path)
        if full_path.exists() and full_path.is_dir():
            shutil.rmtree(full_path)
            return True
        return False

    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        """Copy a file within the storage."""
        src_full = self._resolve_path(src_path)
        dest_full = self._resolve_path(dest_path)

        if not src_full.exists() or not src_full.is_file():
            return False

        dest_full.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_full, dest_full)
        return True

    async def move_file(self, src_path: str, dest_path: str) -> bool:
        """Move/rename a file within the storage."""
        src_full = self._resolve_path(src_path)
        dest_full = self._resolve_path(dest_path)

        if not src_full.exists():
            return False

        dest_full.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_full), str(dest_full))
        return True

    async def copy_dir(self, src_path: str, dest_path: str) -> bool:
        """Copy a directory and all its contents."""
        src_full = self._resolve_path(src_path)
        dest_full = self._resolve_path(dest_path)

        if not src_full.exists() or not src_full.is_dir():
            return False

        if dest_full.exists():
            shutil.rmtree(dest_full)
        shutil.copytree(src_full, dest_full)
        return True

    async def move_dir(self, src_path: str, dest_path: str) -> bool:
        """Move/rename a directory."""
        src_full = self._resolve_path(src_path)
        dest_full = self._resolve_path(dest_path)

        if not src_full.exists() or not src_full.is_dir():
            return False

        dest_full.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_full), str(dest_full))
        return True

    def get_full_path(self, path: str) -> str:
        """Get the full filesystem path for a file."""
        return str(self._resolve_path(path))

    def get_relative_path(self, full_path: str) -> str:
        """Convert full path to relative storage path."""
        full = Path(full_path).resolve()
        try:
            return str(full.relative_to(self.base_path)).replace("\\", "/")
        except ValueError:
            return str(full_path)

    async def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
        method: str = "GET"
    ) -> str:
        """For local storage, just return the file path."""
        return str(self._resolve_path(path))

    # Additional convenience methods for local storage

    def get_path_object(self, path: str) -> Path:
        """Get a Path object for the given relative path."""
        return self._resolve_path(path)

    async def write_stream(self, path: str, stream: BinaryIO) -> str:
        """Write from a stream/file-like object."""
        full_path = self._resolve_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            while chunk := stream.read(8192):
                await f.write(chunk)

        return str(full_path)

    def write_file_sync_direct(
        self,
        path: str,
        content: Union[bytes, str],
    ) -> str:
        """Direct synchronous write without asyncio."""
        full_path = self._resolve_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, str):
            full_path.write_text(content, encoding="utf-8")
        else:
            full_path.write_bytes(content)

        return str(full_path)

    def read_file_sync_direct(self, path: str) -> bytes:
        """Direct synchronous read without asyncio."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return full_path.read_bytes()

    def read_file_text_sync_direct(self, path: str, encoding: str = "utf-8") -> str:
        """Direct synchronous text read without asyncio."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return full_path.read_text(encoding=encoding)
