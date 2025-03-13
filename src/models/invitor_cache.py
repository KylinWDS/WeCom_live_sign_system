from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.models.base import BaseModel
from src.utils.logger import get_logger

logger = get_logger(__name__)

class InvitorCache(BaseModel):
    """邀请人缓存表"""
    __tablename__ = "invitor_cache"
    
    id = Column(Integer, primary_key=True)
    invitor_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now) 