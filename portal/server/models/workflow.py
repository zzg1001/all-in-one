from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
from sqlalchemy.sql import func
from database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    nodes = Column(JSON, nullable=True, default=list)
    edges = Column(JSON, nullable=True, default=list)
    input_count = Column(Integer, default=0)  # 开头节点的输入数
    output_type = Column(String(50), nullable=True)  # 结尾节点的输出类型
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
