# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Product Background API - a FastAPI-based REST API service.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (with auto-reload, exclude storage folders)
uvicorn main:app --reload --reload-exclude "skills_storage/*" --reload-exclude "skills_storage_temp/*" --reload-exclude "file_manage/*" --reload-exclude "uploads/*" --reload-exclude "outputs/*"

# Run production server
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Architecture

Single-file FastAPI application (`main.py`) with:
- FastAPI app instance with CORS middleware enabled
- API docs available at `/docs` (Swagger UI) and `/redoc`
- Health check endpoint at `/health`

## Tech Stack

- **Framework**: FastAPI
- **Server**: Uvicorn
- **Validation**: Pydantic v2
