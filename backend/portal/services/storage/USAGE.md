# Storage Abstraction Usage Guide

## Overview

The storage abstraction provides a unified interface for file operations that works with both:
- **Local Filesystem** - Traditional file storage
- **MinIO/S3** - Object storage (default)

## Configuration

In `.env` or `deploy.env`:

```env
# Storage type: "local" or "minio"
STORAGE_TYPE=minio

# MinIO configuration
MINIO_ENDPOINT=8.153.198.194
MINIO_PORT=8092
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=yourpassword123
MINIO_SECURE=false

# Buckets for different categories
MINIO_SKILLS_BUCKET=ai-skills
MINIO_UPLOADS_BUCKET=ai-uploads
MINIO_OUTPUTS_BUCKET=ai-outputs
```

## Quick Start

```python
from services.storage import (
    get_storage,
    get_skills_storage,
    get_uploads_storage,
    get_outputs_storage,
)

# Get default storage
storage = get_storage()

# Get category-specific storage
skills = get_skills_storage()
uploads = get_uploads_storage()
outputs = get_outputs_storage()
```

## Basic Operations

### Async API (Recommended)

```python
import asyncio

async def example():
    storage = get_storage()

    # Write file
    await storage.write_file("path/to/file.txt", "Hello, World!")
    await storage.write_file("path/to/data.bin", b"\x00\x01\x02")

    # Read file
    content = await storage.read_file_text("path/to/file.txt")
    binary = await storage.read_file("path/to/data.bin")

    # Check existence
    exists = await storage.exists("path/to/file.txt")

    # List files
    files = await storage.list_files("path/to", recursive=True)
    for f in files:
        print(f"{f.name}: {f.size} bytes")

    # Delete
    await storage.delete_file("path/to/file.txt")

    # Directory operations
    await storage.mkdir("new/directory")
    await storage.rmdir("old/directory")

    # Copy/Move
    await storage.copy_file("src.txt", "dest.txt")
    await storage.move_file("old.txt", "new.txt")
    await storage.copy_dir("src_dir", "dest_dir")
    await storage.move_dir("old_dir", "new_dir")

asyncio.run(example())
```

### Sync API (For compatibility)

```python
storage = get_storage()

# Using _sync_direct methods (no event loop needed)
storage.write_file_sync_direct("file.txt", "content")
content = storage.read_file_text_sync_direct("file.txt")

# Using _sync methods (needs event loop)
storage.write_file_sync("file.txt", "content")
content = storage.read_file_sync("file.txt")
```

## Migration Examples

### Before (Local filesystem)

```python
from pathlib import Path
from config import get_skills_storage_dir

def save_skill(skill_id: str, code: str):
    skill_dir = get_skills_storage_dir() / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "main.py").write_text(code)

def read_skill(skill_id: str) -> str:
    skill_dir = get_skills_storage_dir() / skill_id
    return (skill_dir / "main.py").read_text()
```

### After (Storage abstraction)

```python
from services.storage import get_skills_storage

async def save_skill(skill_id: str, code: str):
    storage = get_skills_storage()
    await storage.write_file(f"{skill_id}/main.py", code)

async def read_skill(skill_id: str) -> str:
    storage = get_skills_storage()
    return await storage.read_file_text(f"{skill_id}/main.py")
```

## Full Path Access

For cases where you need the full path (e.g., for subprocess):

```python
storage = get_storage()

# Get full path/URL
full_path = storage.get_full_path("skill/main.py")

# For MinIO, get presigned URL for external access
url = await storage.get_presigned_url("file.txt", expires_in=3600)
```

## Testing

```bash
# Quick MinIO connection test
python test_minio_quick.py

# Full storage abstraction test
python test_storage.py
```

## Storage Categories

| Category | Bucket | Description |
|----------|--------|-------------|
| skills | ai-skills | Skill code and metadata |
| skills_temp | ai-skills-temp | Temporary skill testing |
| uploads | ai-uploads | User uploaded files |
| outputs | ai-outputs | Generated output files |
