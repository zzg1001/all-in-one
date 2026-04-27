"""
AI Skills Platform API - 统一服务
合并 Admin + Portal API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import get_settings, get_outputs_dir, get_uploads_dir, get_file_manage_dir
from app.core.database import init_db

# Admin API
from app.api.v1 import dashboard, models, tokens, users, logs, permissions, ccswitch, auth

# Portal API
from portal.routers import skills_router, workflows_router, agent_router, executions_router, data_notes_router, chat_router
from portal.routers.favorites import router as favorites_router
from portal.routers.logs import router as logs_router, setup_log_handler, sys_ready
from portal.routers.agents import router as agents_router
from portal.routers.agent_modules import router as agent_modules_router
from portal.routers.storage import router as storage_router
from portal.routers.cleanup import router as cleanup_router

# Portal models (确保表被创建)
import portal.models  # noqa: F401

settings = get_settings()

# 使用配置的路径
OUTPUTS_DIR = get_outputs_dir()
UPLOADS_DIR = get_uploads_dir()
FILE_MANAGE_DIR = get_file_manage_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    setup_log_handler()
    sys_ready()

    # 启动时从 MinIO 同步文件到本地缓存
    from portal.services.storage_sync_service import sync_all_on_startup
    await sync_all_on_startup()

    # 启动清理调度器
    from portal.services.cleanup_service import start_cleanup_scheduler, stop_cleanup_scheduler
    await start_cleanup_scheduler()

    yield

    # Shutdown
    stop_cleanup_scheduler()


app = FastAPI(
    title="AI Skills Platform API",
    description="统一 API 服务 - 合并 Admin + Portal",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Admin API Routers ==========
app.include_router(auth.router, prefix="/api/auth", tags=["Admin - Auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Admin - Dashboard"])
app.include_router(models.router, prefix="/api/models", tags=["Admin - Models"])
app.include_router(tokens.router, prefix="/api/tokens", tags=["Admin - Tokens"])
app.include_router(users.router, prefix="/api/users", tags=["Admin - Users"])
app.include_router(logs.router, prefix="/api/logs", tags=["Admin - Logs"])
app.include_router(permissions.router, prefix="/api/permissions", tags=["Admin - Permissions"])
app.include_router(ccswitch.router, prefix="/api/ccswitch", tags=["Admin - CCSwitch"])

# ========== Portal API Routers ==========
app.include_router(skills_router, tags=["Portal - Skills"])
app.include_router(workflows_router, tags=["Portal - Workflows"])
app.include_router(agent_router, tags=["Portal - Agent"])
app.include_router(executions_router, tags=["Portal - Executions"])
app.include_router(favorites_router, tags=["Portal - Favorites"])
app.include_router(data_notes_router, tags=["Portal - DataNotes"])
app.include_router(logs_router, tags=["Portal - Logs"])
app.include_router(chat_router, tags=["Portal - Chat"])
app.include_router(agents_router, tags=["Portal - Agents"])
app.include_router(agent_modules_router, tags=["Portal - AgentModules"])
app.include_router(storage_router, tags=["Portal - Storage"])
app.include_router(cleanup_router, tags=["Portal - Cleanup"])

# 静态文件服务
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/file-manage", StaticFiles(directory=str(FILE_MANAGE_DIR)), name="file-manage")


@app.get("/")
async def root():
    return {"message": "AI Skills Platform API is running", "service": "unified"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "unified-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )
