from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExtractRecordCreate(BaseModel):
    """保存一条企业信息提取记录"""
    company_name: Optional[str] = None
    credit_code: Optional[str] = None
    data: Dict[str, Any]


class ExtractRecordUpdate(BaseModel):
    """更新记录（编辑后保存）"""
    company_name: Optional[str] = None
    credit_code: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ExtractRecordResponse(BaseModel):
    """记录响应"""
    id: str
    company_name: Optional[str] = None
    credit_code: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchDeleteRequest(BaseModel):
    """批量删除"""
    ids: List[str]
