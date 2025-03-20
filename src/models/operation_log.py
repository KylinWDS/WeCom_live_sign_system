from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship

from .base import Base

class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = 'operation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.userid'), nullable=False, comment='操作用户ID')
    operation_type = Column(String(50), nullable=False, comment='操作类型')
    operation_desc = Column(Text, nullable=False, comment='操作描述')
    operation_time = Column(DateTime, nullable=False, default=datetime.now, comment='操作时间')
    ip_address = Column(String(50), nullable=True, comment='IP地址')
    request_data = Column(JSON, nullable=True, comment='请求数据')
    response_data = Column(JSON, nullable=True, comment='响应数据')
    
    # 关联关系
    user = relationship('User', back_populates='operation_logs') 