from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# 使用简单的 Dict 类型，避免复杂的字段别名问题
class WorkflowBase(BaseModel):
    id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = []  # 节点列表
    edges: Optional[List[Dict[str, Any]]] = []  # 边列表


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None


class WorkflowResponse(WorkflowBase):
    input_count: int = 0  # 开头节点的输入数
    output_type: Optional[str] = None  # 结尾节点的输出类型
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
