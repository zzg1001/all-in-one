"""
模块管理 API - 管理 Agent 模块配置和状态
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from portal.models.agent import Agent as AgentModel
from portal.modules import (
    MODULE_DEFINITIONS,
    ModuleDefinition,
    get_module_definition,
    get_config_class,
    ModuleStatus,
    ModuleMetrics,
    registry,
)

router = APIRouter(prefix="/api/modules", tags=["modules"])


# ============ Pydantic 模型 ============

class ModuleStatusResponse(BaseModel):
    """模块状态响应"""
    module_type: str
    status: str
    enabled: bool
    config: Dict[str, Any]


class ModuleConfigUpdate(BaseModel):
    """模块配置更新"""
    enabled: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class ModuleMetricsResponse(BaseModel):
    """模块指标响应"""
    module_type: str
    status: str
    total_calls: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    last_activity: Optional[str] = None
    started_at: Optional[str] = None
    extra: Dict[str, Any] = {}


class AgentModulesResponse(BaseModel):
    """Agent 模块配置响应"""
    agent_id: str
    modules: Dict[str, ModuleStatusResponse]


# ============ API 路由 ============

@router.get("", response_model=List[ModuleDefinition])
async def list_module_definitions():
    """获取所有模块定义"""
    return MODULE_DEFINITIONS


@router.get("/core", response_model=List[ModuleDefinition])
async def list_core_modules():
    """获取核心模块定义（单Agent组件）"""
    return [m for m in MODULE_DEFINITIONS if m.category == "core"]


@router.get("/multi", response_model=List[ModuleDefinition])
async def list_multi_modules():
    """获取多Agent模块定义"""
    return [m for m in MODULE_DEFINITIONS if m.category == "multi"]


@router.get("/{module_type}", response_model=ModuleDefinition)
async def get_module_def(module_type: str):
    """获取单个模块定义"""
    defn = get_module_definition(module_type)
    if not defn:
        raise HTTPException(status_code=404, detail=f"模块类型 {module_type} 不存在")
    return defn


@router.get("/{module_type}/schema")
async def get_module_config_schema(module_type: str):
    """获取模块配置 JSON Schema"""
    config_class = get_config_class(module_type)
    return config_class.model_json_schema()


# ============ Agent 模块管理 ============

@router.get("/agents/{agent_id}", response_model=AgentModulesResponse)
async def get_agent_modules(agent_id: str, db: Session = Depends(get_db)):
    """获取 Agent 的所有模块配置"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    module_configs = agent_db.module_configs or {}

    # 构建每个模块的状态
    modules = {}
    for defn in MODULE_DEFINITIONS:
        module_type = defn.type
        config = module_configs.get(module_type, defn.default_config)
        enabled = config.get("enabled", True) if isinstance(config, dict) else True

        modules[module_type] = ModuleStatusResponse(
            module_type=module_type,
            status="active" if enabled else "inactive",
            enabled=enabled,
            config=config,
        )

    return AgentModulesResponse(agent_id=agent_id, modules=modules)


@router.get("/agents/{agent_id}/{module_type}", response_model=ModuleStatusResponse)
async def get_agent_module(agent_id: str, module_type: str, db: Session = Depends(get_db)):
    """获取 Agent 的单个模块配置"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    defn = get_module_definition(module_type)
    if not defn:
        raise HTTPException(status_code=404, detail=f"模块类型 {module_type} 不存在")

    module_configs = agent_db.module_configs or {}
    config = module_configs.get(module_type, defn.default_config)
    enabled = config.get("enabled", True) if isinstance(config, dict) else True

    return ModuleStatusResponse(
        module_type=module_type,
        status="active" if enabled else "inactive",
        enabled=enabled,
        config=config,
    )


@router.put("/agents/{agent_id}/{module_type}", response_model=ModuleStatusResponse)
async def update_agent_module(
    agent_id: str,
    module_type: str,
    data: ModuleConfigUpdate,
    db: Session = Depends(get_db)
):
    """更新 Agent 的模块配置"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    defn = get_module_definition(module_type)
    if not defn:
        raise HTTPException(status_code=404, detail=f"模块类型 {module_type} 不存在")

    # 获取当前配置
    module_configs = agent_db.module_configs or {}
    current_config = module_configs.get(module_type, defn.default_config.copy())

    # 更新配置
    if data.enabled is not None:
        current_config["enabled"] = data.enabled
    if data.settings:
        current_config.update(data.settings)

    # 验证配置
    config_class = get_config_class(module_type)
    try:
        validated = config_class(**current_config)
        current_config = validated.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置验证失败: {str(e)}")

    # 保存
    module_configs[module_type] = current_config
    agent_db.module_configs = module_configs
    db.commit()

    enabled = current_config.get("enabled", True)
    return ModuleStatusResponse(
        module_type=module_type,
        status="active" if enabled else "inactive",
        enabled=enabled,
        config=current_config,
    )


@router.get("/agents/{agent_id}/{module_type}/metrics", response_model=ModuleMetricsResponse)
async def get_agent_module_metrics(agent_id: str, module_type: str, db: Session = Depends(get_db)):
    """获取 Agent 模块的运行指标"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    defn = get_module_definition(module_type)
    if not defn:
        raise HTTPException(status_code=404, detail=f"模块类型 {module_type} 不存在")

    # 尝试从注册表获取实际指标
    module = registry.get_module(module_type, agent_id)
    if module:
        metrics = module.get_metrics()
        return ModuleMetricsResponse(
            module_type=module_type,
            status=metrics.status.value,
            total_calls=metrics.total_calls,
            success_count=metrics.success_count,
            error_count=metrics.error_count,
            avg_latency_ms=metrics.avg_latency_ms,
            max_latency_ms=metrics.max_latency_ms,
            last_activity=metrics.last_activity.isoformat() if metrics.last_activity else None,
            started_at=metrics.started_at.isoformat() if metrics.started_at else None,
            extra=metrics.extra,
        )

    # 返回空指标（模块未运行）
    module_configs = agent_db.module_configs or {}
    config = module_configs.get(module_type, {})
    enabled = config.get("enabled", True)

    return ModuleMetricsResponse(
        module_type=module_type,
        status="inactive" if not enabled else "idle",
        total_calls=0,
        success_count=0,
        error_count=0,
        avg_latency_ms=0.0,
        max_latency_ms=0.0,
        last_activity=None,
        started_at=None,
        extra={},
    )


@router.post("/agents/{agent_id}/{module_type}/enable")
async def enable_agent_module(agent_id: str, module_type: str, db: Session = Depends(get_db)):
    """启用 Agent 模块"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    defn = get_module_definition(module_type)
    if not defn:
        raise HTTPException(status_code=404, detail=f"模块类型 {module_type} 不存在")

    module_configs = agent_db.module_configs or {}
    config = module_configs.get(module_type, defn.default_config.copy())
    config["enabled"] = True
    module_configs[module_type] = config
    agent_db.module_configs = module_configs
    db.commit()

    return {"status": "success", "message": f"模块 {module_type} 已启用"}


@router.post("/agents/{agent_id}/{module_type}/disable")
async def disable_agent_module(agent_id: str, module_type: str, db: Session = Depends(get_db)):
    """禁用 Agent 模块"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    defn = get_module_definition(module_type)
    if not defn:
        raise HTTPException(status_code=404, detail=f"模块类型 {module_type} 不存在")

    module_configs = agent_db.module_configs or {}
    config = module_configs.get(module_type, defn.default_config.copy())
    config["enabled"] = False
    module_configs[module_type] = config
    agent_db.module_configs = module_configs
    db.commit()

    return {"status": "success", "message": f"模块 {module_type} 已禁用"}


@router.post("/agents/{agent_id}/{module_type}/reset")
async def reset_agent_module(agent_id: str, module_type: str, db: Session = Depends(get_db)):
    """重置模块配置为默认值"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    defn = get_module_definition(module_type)
    if not defn:
        raise HTTPException(status_code=404, detail=f"模块类型 {module_type} 不存在")

    module_configs = agent_db.module_configs or {}
    module_configs[module_type] = defn.default_config.copy()
    agent_db.module_configs = module_configs
    db.commit()

    return {"status": "success", "message": f"模块 {module_type} 已重置"}
