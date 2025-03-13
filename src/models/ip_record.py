from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from src.models.base import Base

class IPRecord(Base):
    """IP记录模型"""
    
    __tablename__ = 'ip_records'
    
    id = Column(Integer, primary_key=True)
    ip = Column(String(45), nullable=False, unique=True)
    source = Column(String(20), nullable=False)  # 'manual' 或 'error'
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<IPRecord(ip='{self.ip}', source='{self.source}')>" 