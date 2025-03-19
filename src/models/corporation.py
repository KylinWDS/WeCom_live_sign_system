from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.sql import func
from .base import Base

class Corporation(Base):
    """企业信息表"""
    __tablename__ = 'corporation'

    # 主键ID
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    # 企业名称
    name = Column(String(100), unique=True, nullable=False, comment='企业名称')
    # 企业ID
    corp_id = Column(String(100), unique=True, nullable=False, comment='企业ID')
    # 企业应用Secret
    corp_secret = Column(String(100), nullable=False, comment='企业应用Secret')
    # 应用ID
    agent_id = Column(String(100), nullable=False, comment='应用ID')
    # 企业状态
    status = Column(Boolean, default=True, comment='企业状态')
    # 创建时间
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    # 更新时间
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    def __repr__(self):
        return f'<Corporation {self.name}>' 