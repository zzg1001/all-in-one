"""
Agent 管理 API - 管理 Agent 配置和元数据
使用数据库存储
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models.agent import Agent as AgentModel

router = APIRouter(prefix="/agents", tags=["agents"])


# ============ Pydantic 模型 ============

class MemoryConfig(BaseModel):
    enabled: bool = True
    type: str = "conversation"
    max_history: int = 20


class ReasoningConfig(BaseModel):
    enabled: bool = True
    style: str = "step-by-step"


class AgentBase(BaseModel):
    name: str = Field(..., description="Agent 名称")
    description: str = Field(default="", description="Agent 描述")
    icon: str = Field(default="🤖", description="图标")
    category: str = Field(default="通用助手", description="分类")
    system_prompt: str = Field(default="", description="系统提示词")
    model: str = Field(default="claude-opus-4-5", description="模型")
    temperature: float = Field(default=0.7, ge=0, le=1, description="温度")
    max_tokens: int = Field(default=4096, ge=256, le=32000, description="最大 Token")
    tools: List[str] = Field(default_factory=list, description="启用的工具")
    skills: List[str] = Field(default_factory=list, description="启用的技能")
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    reasoning: ReasoningConfig = Field(default_factory=ReasoningConfig)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    memory: Optional[MemoryConfig] = None
    reasoning: Optional[ReasoningConfig] = None
    status: Optional[str] = None


class Agent(AgentBase):
    id: str
    status: str = "draft"
    author: str = "System"
    version: str = "1.0.0"
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    agents: List[Agent]
    total: int


# ============ 辅助函数 ============

def _db_to_response(db_agent: AgentModel) -> Agent:
    """将数据库模型转换为响应模型"""
    module_configs = db_agent.module_configs or {}

    return Agent(
        id=db_agent.id,
        name=db_agent.name,
        description=db_agent.description or "",
        icon=db_agent.icon or "🤖",
        category=db_agent.category or "通用助手",
        system_prompt=db_agent.system_prompt or "",
        model=db_agent.model,
        temperature=db_agent.temperature,
        max_tokens=db_agent.max_tokens,
        tools=db_agent.tools or [],
        skills=db_agent.skills or [],
        memory=MemoryConfig(**(module_configs.get("memory", {}))),
        reasoning=ReasoningConfig(**(module_configs.get("reasoning", {}))),
        status=db_agent.status,
        author=db_agent.author or "User",
        version=db_agent.version or "1.0.0",
        usage_count=db_agent.usage_count,
        created_at=db_agent.created_at,
        updated_at=db_agent.updated_at,
    )


def _init_sample_agents(db: Session):
    """初始化示例数据（如果数据库为空）"""
    existing = db.query(AgentModel).first()
    if existing:
        return

    samples = [
        {
            "id": str(uuid.uuid4()),
            "name": "智能写作助手",
            "description": "帮助撰写各类文档、邮件、报告，支持多种风格和格式",
            "icon": "✍️",
            "category": "通用助手",
            "system_prompt": "你是一个专业的写作助手...",
            "model": "claude-opus-4-5",
            "tools": ["write", "read"],
            "skills": [],
            "status": "active",
            "author": "System",
            "version": "1.0.0",
            "usage_count": 1520,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "数据分析专家",
            "description": "分析 Excel、CSV 数据，生成可视化图表和分析报告",
            "icon": "📊",
            "category": "数据处理",
            "system_prompt": "你是一个数据分析专家...",
            "model": "claude-opus-4-5",
            "tools": ["read", "code_exec"],
            "skills": ["excel-to-json", "json-to-excel"],
            "status": "active",
            "author": "System",
            "version": "1.2.0",
            "usage_count": 892,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "代码生成器",
            "description": "根据需求描述生成代码，支持多种编程语言",
            "icon": "💻",
            "category": "代码生成",
            "system_prompt": "你是一个代码生成专家...",
            "model": "claude-opus-4-5",
            "tools": ["bash", "code_exec", "read", "write"],
            "skills": [],
            "status": "active",
            "author": "System",
            "version": "2.0.0",
            "usage_count": 2341,
        },
    ]

    for sample in samples:
        agent = AgentModel(
            **sample,
            temperature=0.7,
            max_tokens=4096,
            module_configs={
                "memory": {"enabled": True, "type": "conversation", "max_history": 20},
                "reasoning": {"enabled": True, "style": "step-by-step"},
            }
        )
        db.add(agent)

    db.commit()


# ============ API 路由 ============

@router.get("", response_model=AgentListResponse)
async def list_agents(
    category: Optional[str] = Query(None, description="按分类筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取 Agent 列表"""
    # 初始化示例数据
    _init_sample_agents(db)

    query = db.query(AgentModel)

    # 筛选
    if category:
        query = query.filter(AgentModel.category == category)
    if status:
        query = query.filter(AgentModel.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (AgentModel.name.ilike(search_pattern)) |
            (AgentModel.description.ilike(search_pattern))
        )

    total = query.count()
    agents_db = query.offset(skip).limit(limit).all()
    agents = [_db_to_response(a) for a in agents_db]

    return AgentListResponse(agents=agents, total=total)


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """获取单个 Agent 详情"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return _db_to_response(agent_db)


@router.post("", response_model=Agent)
async def create_agent(data: AgentCreate, db: Session = Depends(get_db)):
    """创建新 Agent"""
    agent_id = str(uuid.uuid4())

    agent_db = AgentModel(
        id=agent_id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        category=data.category,
        system_prompt=data.system_prompt,
        model=data.model,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        tools=data.tools,
        skills=data.skills,
        module_configs={
            "memory": data.memory.model_dump(),
            "reasoning": data.reasoning.model_dump(),
        },
        status="draft",
        author="User",
        version="1.0.0",
        usage_count=0,
    )

    db.add(agent_db)
    db.commit()
    db.refresh(agent_db)

    return _db_to_response(agent_db)


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, data: AgentUpdate, db: Session = Depends(get_db)):
    """更新 Agent"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    update_data = data.model_dump(exclude_unset=True)

    # 处理 memory 和 reasoning 配置
    if "memory" in update_data:
        module_configs = agent_db.module_configs or {}
        module_configs["memory"] = update_data.pop("memory")
        agent_db.module_configs = module_configs
    if "reasoning" in update_data:
        module_configs = agent_db.module_configs or {}
        module_configs["reasoning"] = update_data.pop("reasoning")
        agent_db.module_configs = module_configs

    # 更新其他字段
    for key, value in update_data.items():
        if hasattr(agent_db, key):
            setattr(agent_db, key, value)

    db.commit()
    db.refresh(agent_db)

    return _db_to_response(agent_db)


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """删除 Agent"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    db.delete(agent_db)
    db.commit()

    return {"status": "success", "message": "Agent 已删除"}


@router.post("/{agent_id}/publish")
async def publish_agent(agent_id: str, db: Session = Depends(get_db)):
    """发布 Agent"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    agent_db.status = "active"
    db.commit()

    return {"status": "success", "message": "Agent 已发布"}


@router.post("/{agent_id}/deprecate")
async def deprecate_agent(agent_id: str, db: Session = Depends(get_db)):
    """弃用 Agent"""
    agent_db = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    agent_db.status = "deprecated"
    db.commit()

    return {"status": "success", "message": "Agent 已弃用"}


# ============ AI 生成相关 ============

class PromptGenerateRequest(BaseModel):
    name: str
    description: str
    category: Optional[str] = None


class ToolRecommendRequest(BaseModel):
    description: str
    category: Optional[str] = None


@router.post("/generate/prompt")
async def generate_prompt(data: PromptGenerateRequest):
    """AI 生成系统提示词（占位符，后续对接真实 AI）"""
    # TODO: 调用 Claude API 生成提示词
    prompt = f"""你是{data.name}，一个专业的 AI 助手。

## 角色定位
{data.description}

## 工作原则
1. 始终保持专业、友好的态度
2. 给出清晰、结构化的回答
3. 在不确定时主动询问澄清
4. 注重用户隐私和数据安全

## 输出格式
- 使用清晰的标题和列表
- 代码使用合适的语法高亮
- 复杂内容分步骤说明

## 限制
- 不处理违法违规内容
- 不提供医疗、法律等专业建议
- 对不确定的信息保持谨慎"""

    return {"status": "success", "prompt": prompt}


@router.post("/generate/tools")
async def recommend_tools(data: ToolRecommendRequest):
    """AI 推荐工具（占位符，后续对接真实 AI）"""
    # 简单的关键词匹配
    tools = []
    desc = data.description.lower()

    if "文件" in desc or "文档" in desc:
        tools.extend(["read", "write"])
    if "代码" in desc or "编程" in desc:
        tools.extend(["bash", "code_exec"])
    if "搜索" in desc or "网络" in desc:
        tools.extend(["web_search", "web_fetch"])
    if "图像" in desc or "图片" in desc:
        tools.append("image_read")

    if not tools:
        tools = ["read"]  # 默认

    return {"status": "success", "tools": list(set(tools))}


@router.post("/generate/description")
async def generate_description(name: str = Query(...)):
    """AI 生成描述（占位符）"""
    description = f"一个基于 {name} 的智能助手，能够帮助用户高效完成相关任务，提供专业的建议和解决方案。"
    return {"status": "success", "description": description}
