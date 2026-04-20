"""
Storage abstraction base class.
Defines the interface for all storage backends.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, BinaryIO, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileInfo:
    """File metadata information."""
    name: str
    path: str
    size: int
    modified_time: datetime
    is_dir: bool
    content_type: Optional[str] = None


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.
    Supports both local filesystem and object storage (MinIO/S3).
    """

    @abstractmethod
    async def write_file(
        self,
        path: str,
        content: Union[bytes, str, BinaryIO],
        content_type: Optional[str] = None
    ) -> str:
        """
        Write content to a file.

        Args:
            path: Relative path within the storage (e.g., "skills/uuid/main.py")
            content: File content (bytes, string, or file-like object)
            content_type: MIME type of the content

        Returns:
            The full path/URL to the stored file
        """
        pass

    @abstractmethod
    async def read_file(self, path: str) -> bytes:
        """
        Read file content.

        Args:
            path: Relative path within the storage

        Returns:
            File content as bytes
        """
        pass

    @abstractmethod
    async def read_file_text(self, path: str, encoding: str = "utf-8") -> str:
        """
        Read file content as text.

        Args:
            path: Relative path within the storage
            encoding: Text encoding

        Returns:
            File content as string
        """
        pass

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """
        Delete a file.

        Args:
            path: Relative path within the storage

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        Check if a file or directory exists.

        Args:
            path: Relative path within the storage

        Returns:
            True if exists
        """
        pass

    @abstractmethod
    async def get_file_info(self, path: str) -> Optional[FileInfo]:
        """
        Get file metadata.

        Args:
            path: Relative path within the storage

        Returns:
            FileInfo object or None if not exists
        """
        pass

    @abstractmethod
    async def list_files(
        self,
        path: str = "",
        recursive: bool = False,
        pattern: Optional[str] = None
    ) -> List[FileInfo]:
        """
        List files in a directory.

        Args:
            path: Directory path
            recursive: Whether to list recursively
            pattern: Glob pattern to filter files

        Returns:
            List of FileInfo objects
        """
        pass

    @abstractmethod
    async def mkdir(self, path: str) -> bool:
        """
        Create a directory (for local storage) or prefix (for object storage).

        Args:
            path: Directory path

        Returns:
            True if created successfully
        """
        pass

    @abstractmethod
    async def rmdir(self, path: str) -> bool:
        """
        Remove a directory and all its contents.

        Args:
            path: Directory path

        Returns:
            True if removed successfully
        """
        pass

    @abstractmethod
    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        """
        Copy a file within the storage.

        Args:
            src_path: Source path
            dest_path: Destination path

        Returns:
            True if copied successfully
        """
        pass

    @abstractmethod
    async def move_file(self, src_path: str, dest_path: str) -> bool:
        """
        Move/rename a file within the storage.

        Args:
            src_path: Source path
            dest_path: Destination path

        Returns:
            True if moved successfully
        """
        pass

    @abstractmethod
    async def copy_dir(self, src_path: str, dest_path: str) -> bool:
        """
        Copy a directory and all its contents.

        Args:
            src_path: Source directory path
            dest_path: Destination directory path

        Returns:
            True if copied successfully
        """
        pass

    @abstractmethod
    async def move_dir(self, src_path: str, dest_path: str) -> bool:
        """
        Move/rename a directory.

        Args:
            src_path: Source directory path
            dest_path: Destination directory path

        Returns:
            True if moved successfully
        """
        pass

    @abstractmethod
    def get_full_path(self, path: str) -> str:
        """
        Get the full path/URL for a file.

        Args:
            path: Relative path within the storage

        Returns:
            Full filesystem path or URL
        """
        pass

    @abstractmethod
    def get_relative_path(self, full_path: str) -> str:
        """
        Convert full path/URL to relative storage path.

        Args:
            full_path: Full filesystem path or URL

        Returns:
            Relative path within the storage
        """
        pass

    @abstractmethod
    async def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
        method: str = "GET"
    ) -> str:
        """
        Get a presigned URL for direct access (for object storage).
        For local storage, returns the file path.

        Args:
            path: Relative path within the storage
            expires_in: URL expiration time in seconds
            method: HTTP method (GET for download, PUT for upload)

        Returns:
            Presigned URL or file path
        """
        pass

    # Sync versions for compatibility with existing code
    def write_file_sync(
        self,
        path: str,
        content: Union[bytes, str, BinaryIO],
        content_type: Optional[str] = None
    ) -> str:
        """Synchronous version of write_file."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.write_file(path, content, content_type)
        )

    def read_file_sync(self, path: str) -> bytes:
        """Synchronous version of read_file."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.read_file(path))

    def read_file_text_sync(self, path: str, encoding: str = "utf-8") -> str:
        """Synchronous version of read_file_text."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.read_file_text(path, encoding)
        )

    def exists_sync(self, path: str) -> bool:
        """Synchronous version of exists."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.exists(path))

    def delete_file_sync(self, path: str) -> bool:
        """Synchronous version of delete_file."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.delete_file(path))

    def list_files_sync(
        self,
        path: str = "",
        recursive: bool = False,
        pattern: Optional[str] = None
    ) -> List[FileInfo]:
        """Synchronous version of list_files."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.list_files(path, recursive, pattern)
        )

    def mkdir_sync(self, path: str) -> bool:
        """Synchronous version of mkdir."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.mkdir(path))

    def rmdir_sync(self, path: str) -> bool:
        """Synchronous version of rmdir."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.rmdir(path))

    def copy_file_sync(self, src_path: str, dest_path: str) -> bool:
        """Synchronous version of copy_file."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.copy_file(src_path, dest_path)
        )

    def move_file_sync(self, src_path: str, dest_path: str) -> bool:
        """Synchronous version of move_file."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.move_file(src_path, dest_path)
        )

    def copy_dir_sync(self, src_path: str, dest_path: str) -> bool:
        """Synchronous version of copy_dir."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.copy_dir(src_path, dest_path)
        )

    def move_dir_sync(self, src_path: str, dest_path: str) -> bool:
        """Synchronous version of move_dir."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.move_dir(src_path, dest_path)
        )
