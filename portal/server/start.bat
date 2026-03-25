@echo off
REM Portal Server 启动脚本 - 端口 8000
uvicorn main:app --reload --host 127.0.0.1 --port 8000 --reload-exclude "skills_storage/*" --reload-exclude "skills_storage_temp/*"
