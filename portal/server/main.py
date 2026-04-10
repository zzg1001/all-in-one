from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from database import init_db
# 导入 models 确保表被创建
import models  # noqa: F401
from routers import skills_router, workflows_router, agent_router, executions_router, data_notes_router, chat_router
from routers.favorites import router as favorites_router
from routers.logs import router as logs_router, setup_log_handler, sys_ready
from routers.agents import router as agents_router
from routers.agent_modules import router as agent_modules_router
from routers.storage import router as storage_router  # 存储访问
from routers.cleanup import router as cleanup_router  # 清理任务
from config import get_outputs_dir, get_uploads_dir, get_file_manage_dir

# 使用配置的路径（目录会自动创建）
OUTPUTS_DIR = get_outputs_dir()
UPLOADS_DIR = get_uploads_dir()
FILE_MANAGE_DIR = get_file_manage_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    setup_log_handler()
    sys_ready()

    # 启动时从 MinIO 同步文件到本地缓存（预热）
    from services.storage_sync_service import sync_all_on_startup
    await sync_all_on_startup()

    # 启动清理调度器（配置在 deploy.env: CLEANUP_INTERVAL_HOURS, CLEANUP_RETENTION_DAYS）
    from services.cleanup_service import start_cleanup_scheduler, stop_cleanup_scheduler
    await start_cleanup_scheduler()  # 使用配置文件的值

    yield

    # Shutdown
    stop_cleanup_scheduler()


app = FastAPI(
    title="Product Background API",
    description="Backend API for AI Skills Platform - supports skill management, workflow management, and AI agent chat",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(skills_router)
app.include_router(workflows_router)
app.include_router(agent_router)
app.include_router(executions_router)
app.include_router(favorites_router)
app.include_router(data_notes_router)
app.include_router(logs_router)
app.include_router(chat_router)
app.include_router(agents_router)
app.include_router(agent_modules_router)
app.include_router(storage_router)  # 存储 API (支持 MinIO)
app.include_router(cleanup_router)  # 清理任务 API

# 静态文件服务 - 输出文件下载
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
# 静态文件服务 - 上传文件访问
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
# 静态文件服务 - File Manage 文件访问
app.mount("/file-manage", StaticFiles(directory=str(FILE_MANAGE_DIR)), name="file-manage")


@app.get("/")
async def root():
    return {"message": "Product Background API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    from config import get_settings
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )
