from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base

class ConfigChange(Base):
    """配置变更记录模型"""
    __tablename__ = 'config_changes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.userid'), nullable=False, comment='操作用户ID')
    change_type = Column(String(50), nullable=False, comment='变更类型')
    change_content = Column(JSON, nullable=False, comment='变更内容')
    change_time = Column(DateTime, nullable=False, default=datetime.now, comment='变更时间')
    ip_address = Column(String(50), nullable=True, comment='IP地址')
    
    # 关联关系
    user = relationship('User', back_populates='config_changes') 