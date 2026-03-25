"""
AI Skills Admin API
后台管理系统 API 服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1 import dashboard, models, tokens, users, logs, permissions, ccswitch

settings = get_settings()

app = FastAPI(
    title="AI Skills Admin API",
    description="后台管理系统 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(models.router, prefix="/api/models", tags=["Models"])
app.include_router(tokens.router, prefix="/api/tokens", tags=["Tokens"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(permissions.router, prefix="/api/permissions", tags=["Permissions"])
app.include_router(ccswitch.router, prefix="/api/ccswitch", tags=["CCSwitch"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "admin-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )
