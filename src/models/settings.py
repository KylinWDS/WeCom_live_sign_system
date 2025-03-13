from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from src.models.base import BaseModel

class Settings(BaseModel):
    """系统设置模型"""
    
    __tablename__ = "settings"
    
    # 基本信息
    name = Column(String(100), nullable=False, unique=True, comment="设置名称")
    value = Column(Text, nullable=True, comment="设置值")
    type = Column(String(50), nullable=False, comment="设置类型")
    description = Column(String(500), nullable=True, comment="设置描述")
    
    # 配置信息
    config = Column(JSON, nullable=True, comment="配置信息")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "value": self.value,
            "type": self.type,
            "description": self.description,
            "config": self.config
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """从字典创建设置"""
        return cls(**data) 