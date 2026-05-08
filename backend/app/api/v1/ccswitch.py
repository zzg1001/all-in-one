"""
CCSwitch API - Claude 配置管理
支持测试、编辑、启用、复制、导出、导入
使用 MySQL 持久化存储（与 Portal 共享）
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
import uuid

from app.core.database import get_db, Base, engine
from app.models.ccconfig import CCConfig
from sqlalchemy import text

router = APIRouter()

# 自动创建表（如果不存在）
Base.metadata.create_all(bind=engine)

# 自动添加 api_type 列（如果不存在）
def ensure_api_type_column():
    """确保 api_type 列存在"""
    try:
        with engine.connect() as conn:
            # 检查列是否存在
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_name = 'cc_configs' AND column_name = 'api_type'"
            ))
            count = result.scalar()
            if count == 0:
                # 添加 api_type 列
                conn.execute(text(
                    "ALTER TABLE cc_configs ADD COLUMN api_type VARCHAR(20) DEFAULT 'anthropic' "
                    "COMMENT 'API类型: anthropic, openai, litellm' AFTER description"
                ))
                conn.commit()
                print("✅ 已自动添加 api_type 列")
    except Exception as e:
        print(f"⚠️ 检查/添加 api_type 列时出错: {e}")

ensure_api_type_column()


def init_default_config():
    """初始化默认配置（如果不存在）"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        # 检查是否已有配置
        existing = db.query(CCConfig).first()
        if not existing:
            # 创建默认配置（使用当前 Portal 的配置）
            default_config = CCConfig(
                id="default1",
                name="Claude Opus 4.5 (Azure)",
                description="默认配置 - Azure 代理的 Claude Opus 4.5 模型",
                model_id="claude-opus-4-5",
                api_key=os.getenv("AZURE_API_KEY", ""),
                base_url="https://yunqinghu-3344-resource.services.ai.azure.com/anthropic/",
                max_tokens=4096,
                temperature=0.7,
                top_p=1.0,
                system_prompt=None,
                extra_params=None,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(default_config)
            db.commit()
            print("✅ 已创建默认 Claude 配置")
    except Exception as e:
        print(f"⚠️ 初始化默认配置失败: {e}")
        db.rollback()
    finally:
        db.close()


# 启动时初始化默认配置
init_default_config()


# ============ Schemas ============

class CCConfigBase(BaseModel):
    name: str
    description: Optional[str] = None
    api_type: Optional[str] = "claude_sdk"  # Claude Agent SDK
    model_id: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    system_prompt: Optional[str] = None
    extra_params: Optional[dict] = None


class CCConfigCreate(CCConfigBase):
    pass


class CCConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    api_type: Optional[str] = None
    model_id: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    system_prompt: Optional[str] = None
    extra_params: Optional[dict] = None
    is_active: Optional[bool] = None


class CCConfigResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    api_type: Optional[str] = "claude_sdk"
    model_id: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    system_prompt: Optional[str] = None
    extra_params: Optional[dict] = None
    is_active: bool
    created_at: str
    updated_at: str


class TestResult(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[int] = None
    response_preview: Optional[str] = None


# ============ CRUD APIs ============

@router.get("", response_model=List[CCConfigResponse])
async def list_configs(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取所有 Claude 配置"""
    query = db.query(CCConfig)
    if is_active is not None:
        query = query.filter(CCConfig.is_active == is_active)
    configs = query.order_by(CCConfig.created_at.desc()).all()
    return [c.to_dict() for c in configs]


@router.get("/active", response_model=Optional[CCConfigResponse])
async def get_active_config(db: Session = Depends(get_db)):
    """获取当前启用的配置（供 Portal 调用）"""
    config = db.query(CCConfig).filter(CCConfig.is_active == True).first()
    if not config:
        return None
    return config.to_dict()


@router.post("/test-direct", response_model=TestResult)
async def test_config_direct(data: CCConfigCreate):
    """直接测试配置（不需要保存到数据库）"""
    import time
    start = time.time()
    api_type = data.api_type or 'anthropic'

    # 去除首尾空格
    api_key = (data.api_key or '').strip()
    base_url = (data.base_url or '').strip()
    model_id = (data.model_id or '').strip()

    # DEBUG: 打印前端发送的数据
    print(f"[test-direct] ========== 直接测试 ==========")
    print(f"[test-direct] 配置名: {data.name}")
    print(f"[test-direct] API类型: {api_type}")
    print(f"[test-direct] Base URL: {base_url}")
    print(f"[test-direct] 模型: {model_id}")
    print(f"[test-direct] API Key: {api_key[:15]}..." if api_key else "[test-direct] API Key: 空")

    try:
        # Claude Agent SDK - 使用 Anthropic API 格式
        import anthropic

        # 临时清除环境变量，确保使用传入的 api_key
        import os
        old_env_key = os.environ.pop('ANTHROPIC_API_KEY', None)

        try:
            client = anthropic.Anthropic(api_key=api_key, base_url=base_url if base_url else None)
            response = client.messages.create(
                model=model_id,
                max_tokens=50,
                messages=[{"role": "user", "content": "Hi, just testing. Reply with 'OK'."}]
            )
        finally:
            # 恢复环境变量
            if old_env_key:
                os.environ['ANTHROPIC_API_KEY'] = old_env_key

        latency = int((time.time() - start) * 1000)
        # 遍历响应内容，跳过 ThinkingBlock，只提取 text
        preview = ""
        for block in response.content:
            if hasattr(block, 'text'):
                preview += block.text
        preview = preview or "No response"
        return TestResult(success=True, message=f"连接成功 - {model_id}", latency_ms=latency, response_preview=preview[:100])

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        print(f"[test-direct] 错误: {error_msg}")
        if "Connection refused" in error_msg or "Connection error" in error_msg:
            return TestResult(success=False, message="无法连接到服务器，请检查 Base URL")
        elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return TestResult(success=False, message="API Key 无效")
        else:
            return TestResult(success=False, message=f"连接失败: {error_msg[:100]}")


@router.get("/{config_id}", response_model=CCConfigResponse)
async def get_config(config_id: str, db: Session = Depends(get_db)):
    """获取单个配置详情"""
    config = db.query(CCConfig).filter(CCConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config.to_dict()


@router.post("", response_model=CCConfigResponse)
async def create_config(data: CCConfigCreate, db: Session = Depends(get_db)):
    """创建新配置"""
    config = CCConfig(
        id=str(uuid.uuid4())[:8],
        name=data.name,
        description=data.description,
        api_type=data.api_type or "anthropic",
        model_id=data.model_id,
        api_key=data.api_key,
        base_url=data.base_url,
        max_tokens=data.max_tokens or 4096,
        temperature=data.temperature or 0.7,
        top_p=data.top_p or 1.0,
        system_prompt=data.system_prompt,
        extra_params=json.dumps(data.extra_params) if data.extra_params else None,
        is_active=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config.to_dict()


@router.put("/{config_id}", response_model=CCConfigResponse)
async def update_config(
    config_id: str,
    data: CCConfigUpdate,
    db: Session = Depends(get_db)
):
    """更新配置"""
    config = db.query(CCConfig).filter(CCConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "extra_params" and value is not None:
            setattr(config, key, json.dumps(value))
        else:
            setattr(config, key, value)

    config.updated_at = datetime.now()
    db.commit()
    db.refresh(config)
    return config.to_dict()


@router.delete("/{config_id}")
async def delete_config(config_id: str, db: Session = Depends(get_db)):
    """删除配置"""
    config = db.query(CCConfig).filter(CCConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    db.delete(config)
    db.commit()
    return {"message": "删除成功"}


# ============ 特殊操作 APIs ============

@router.post("/{config_id}/test", response_model=TestResult)
async def test_config(config_id: str, db: Session = Depends(get_db)):
    """测试配置连接 - 根据 API 类型调用不同的接口"""
    config = db.query(CCConfig).filter(CCConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    import time
    start = time.time()
    api_type = config.api_type or 'anthropic'

    # DEBUG: 打印配置信息
    print(f"[test_config] ========== 测试配置 ==========")
    print(f"[test_config] Config ID: {config_id}")
    print(f"[test_config] Config Name: {config.name}")
    print(f"[test_config] API Type: {api_type}")
    print(f"[test_config] Model ID: {config.model_id}")
    print(f"[test_config] Base URL: {config.base_url}")
    print(f"[test_config] API Key: {config.api_key[:15]}..." if config.api_key else "[test_config] API Key: None")

    try:
        # Claude Agent SDK - 使用 Anthropic API 格式
        import anthropic

        print(f"[test_config] 使用 Claude Agent SDK，Base URL: {config.base_url or '默认'}")

        # 临时清除环境变量，确保使用数据库中的 api_key
        old_env_key = os.environ.pop('ANTHROPIC_API_KEY', None)

        try:
            client = anthropic.Anthropic(
                api_key=config.api_key,
                base_url=config.base_url if config.base_url else None
            )
            response = client.messages.create(
                model=config.model_id,
                max_tokens=50,
                messages=[{"role": "user", "content": "Hi, just testing. Reply with 'OK'."}]
            )
        finally:
            # 恢复环境变量
            if old_env_key:
                os.environ['ANTHROPIC_API_KEY'] = old_env_key

        latency = int((time.time() - start) * 1000)
        # 遍历响应内容，跳过 ThinkingBlock，只提取 text
        preview = ""
        for block in response.content:
            if hasattr(block, 'text'):
                preview += block.text
        preview = preview or "No response"

        return TestResult(
            success=True,
            message=f"连接成功 - {config.model_id}",
            latency_ms=latency,
            response_preview=preview[:100]
        )

    except Exception as e:
        error_msg = str(e)
        # 简化常见错误信息
        if "Connection refused" in error_msg or "Connection error" in error_msg:
            return TestResult(success=False, message=f"无法连接到服务器，请检查 Base URL 是否正确")
        elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return TestResult(success=False, message="API Key 无效")
        elif "model" in error_msg.lower() and "not found" in error_msg.lower():
            return TestResult(success=False, message=f"模型 {config.model_id} 不存在")
        else:
            return TestResult(success=False, message=f"连接失败: {error_msg[:100]}")


@router.post("/{config_id}/toggle")
async def toggle_config(config_id: str, db: Session = Depends(get_db)):
    """切换配置启用状态（同时只能有一个启用）"""
    config = db.query(CCConfig).filter(CCConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    if not config.is_active:
        # 启用此配置时，禁用其他所有配置
        db.query(CCConfig).filter(CCConfig.id != config_id).update({"is_active": False})

    config.is_active = not config.is_active
    config.updated_at = datetime.now()
    db.commit()

    return {
        "id": config_id,
        "is_active": config.is_active,
        "message": "已启用" if config.is_active else "已禁用"
    }


@router.post("/{config_id}/copy", response_model=CCConfigResponse)
async def copy_config(config_id: str, db: Session = Depends(get_db)):
    """复制配置"""
    source = db.query(CCConfig).filter(CCConfig.id == config_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="配置不存在")

    new_config = CCConfig(
        id=str(uuid.uuid4())[:8],
        name=f"{source.name} (副本)",
        description=source.description,
        api_type=source.api_type or "anthropic",
        model_id=source.model_id,
        api_key=source.api_key,
        base_url=source.base_url,
        max_tokens=source.max_tokens,
        temperature=source.temperature,
        top_p=source.top_p,
        system_prompt=source.system_prompt,
        extra_params=source.extra_params,
        is_active=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config.to_dict()


# ============ 导入导出 APIs ============

@router.get("/{config_id}/export")
async def export_config(config_id: str, db: Session = Depends(get_db)):
    """导出单个配置为 JSON"""
    config = db.query(CCConfig).filter(CCConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    data = config.to_dict()
    data["api_key"] = "***"

    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f"attachment; filename=ccswitch-{config_id}.json"}
    )


@router.get("/export/all")
async def export_all_configs(db: Session = Depends(get_db)):
    """导出所有配置"""
    configs = db.query(CCConfig).all()

    data = []
    for config in configs:
        c = config.to_dict()
        c["api_key"] = "***"
        data.append(c)

    return JSONResponse(
        content={"configs": data, "exported_at": datetime.now().isoformat()},
        headers={"Content-Disposition": "attachment; filename=ccswitch-all.json"}
    )


@router.post("/import")
async def import_configs(data: dict, db: Session = Depends(get_db)):
    """导入配置"""
    imported = []
    errors = []

    configs_data = data.get("configs", [data]) if "configs" in data else [data]

    for config_data in configs_data:
        try:
            if not config_data.get("name") or not config_data.get("model_id"):
                errors.append(f"配置缺少必要字段: {config_data.get('name', 'unknown')}")
                continue

            api_key = config_data.get("api_key", "")
            if api_key == "***":
                api_key = "请填写 API Key"

            new_config = CCConfig(
                id=str(uuid.uuid4())[:8],
                name=config_data.get("name"),
                description=config_data.get("description"),
                api_type=config_data.get("api_type", "anthropic"),
                model_id=config_data.get("model_id"),
                api_key=api_key,
                base_url=config_data.get("base_url"),
                max_tokens=config_data.get("max_tokens", 4096),
                temperature=config_data.get("temperature", 0.7),
                top_p=config_data.get("top_p", 1.0),
                system_prompt=config_data.get("system_prompt"),
                extra_params=json.dumps(config_data.get("extra_params")) if config_data.get("extra_params") else None,
                is_active=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(new_config)
            db.commit()
            imported.append(new_config.name)

        except Exception as e:
            db.rollback()
            errors.append(str(e))

    return {
        "imported": imported,
        "errors": errors,
        "message": f"成功导入 {len(imported)} 个配置"
    }
