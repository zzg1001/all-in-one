"""
Storage abstraction module.

Provides a unified interface for file storage operations,
supporting both local filesystem and MinIO/S3 object storage.

Usage:
    from portal.services.storage import get_storage, StorageType

    # Get configured storage instance
    storage = get_storage()

    # Or specify storage type
    storage = get_storage(StorageType.MINIO)

    # Use storage
    await storage.write_file("skills/uuid/main.py", code_content)
    content = await storage.read_file("skills/uuid/main.py")
"""
from enum import Enum
from typing import Optional
from functools import lru_cache

from .base import StorageBackend, FileInfo
from .local import LocalStorage
from .minio_storage import MinioStorage


class StorageType(str, Enum):
    """Supported storage backend types."""
    LOCAL = "local"
    MINIO = "minio"


# Singleton storage instances
_storage_instances: dict[str, StorageBackend] = {}


def get_storage(
    storage_type: Optional[StorageType] = None,
    category: str = "default"
) -> StorageBackend:
    """
    Get a storage backend instance.

    Args:
        storage_type: Type of storage backend. If None, uses config default.
        category: Storage category (skills, uploads, outputs, etc.)
                  Each category can have different configuration.

    Returns:
        StorageBackend instance
    """
    from app.core.config import get_settings

    settings = get_settings()

    # Determine storage type
    if storage_type is None:
        storage_type = StorageType(settings.storage_type)

    # Create cache key
    cache_key = f"{storage_type.value}:{category}"

    if cache_key not in _storage_instances:
        if storage_type == StorageType.LOCAL:
            _storage_instances[cache_key] = _create_local_storage(settings, category)
        elif storage_type == StorageType.MINIO:
            _storage_instances[cache_key] = _create_minio_storage(settings, category)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")

    return _storage_instances[cache_key]


def _create_local_storage(settings, category: str) -> LocalStorage:
    """Create local storage instance for a category."""
    from pathlib import Path

    # Get base path from settings
    base_path = Path(settings.local_storage_base_path)

    # Category-specific paths (for backwards compatibility)
    category_paths = {
        "skills": settings.skills_storage_dir or base_path / "skills_storage",
        "skills_temp": settings.skills_storage_temp_dir or base_path / "skills_storage_temp",
        "uploads": settings.uploads_dir or base_path / "uploads",
        "outputs": settings.outputs_dir or base_path / "outputs",
        "default": base_path,
    }

    path = category_paths.get(category, base_path / category)
    return LocalStorage(str(path))


def _create_minio_storage(settings, category: str) -> MinioStorage:
    """Create MinIO storage instance for a category."""
    # Map categories to buckets
    bucket_mapping = {
        "skills": settings.minio_skills_bucket,
        "skills_temp": settings.minio_skills_temp_bucket,
        "uploads": settings.minio_uploads_bucket,
        "outputs": settings.minio_outputs_bucket,
        "default": settings.minio_default_bucket,
    }

    bucket = bucket_mapping.get(category, settings.minio_default_bucket)

    return MinioStorage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=bucket,
        port=settings.minio_port,
        secure=settings.minio_secure,
        region=settings.minio_region
    )


def get_skills_storage() -> StorageBackend:
    """Get storage for skills."""
    return get_storage(category="skills")


def get_skills_temp_storage() -> StorageBackend:
    """Get storage for temporary skills."""
    return get_storage(category="skills_temp")


def get_uploads_storage() -> StorageBackend:
    """Get storage for uploads."""
    return get_storage(category="uploads")


def get_outputs_storage() -> StorageBackend:
    """Get storage for outputs."""
    return get_storage(category="outputs")


def clear_storage_cache():
    """Clear cached storage instances (useful for testing)."""
    global _storage_instances
    _storage_instances = {}


# Export main classes and functions
__all__ = [
    "StorageBackend",
    "FileInfo",
    "LocalStorage",
    "MinioStorage",
    "StorageType",
    "get_storage",
    "get_skills_storage",
    "get_skills_temp_storage",
    "get_uploads_storage",
    "get_outputs_storage",
    "clear_storage_cache",
]
