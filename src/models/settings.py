from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from src.models.base import BaseModel

class Settings(BaseModel):
    """系统设置模型"""
    
    __tablename__ = "settings"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 基本信息
    name = Column(String(100), nullable=False, unique=True, comment="设置名称")
    value = Column(Text, nullable=True, comment="设置值")
    type = Column(String(50), nullable=False, comment="设置类型")
    description = Column(String(500), nullable=True, comment="设置描述")
    
    # 配置信息
    config = Column(JSON, nullable=True, comment="配置信息")
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "type": self.type,
            "description": self.description,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """从字典创建设置"""
        return cls(**data) 