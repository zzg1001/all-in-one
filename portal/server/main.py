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
from config import get_outputs_dir, get_uploads_dir

# 使用配置的路径（目录会自动创建）
OUTPUTS_DIR = get_outputs_dir()
UPLOADS_DIR = get_uploads_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    setup_log_handler()
    sys_ready()
    yield
    pass


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

# 静态文件服务 - 输出文件下载
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
# 静态文件服务 - 上传文件访问
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


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
