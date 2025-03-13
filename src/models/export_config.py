from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.models.base import Base

class ExportConfig(Base):
    __tablename__ = 'export_configs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), ForeignKey('users.user_id'), nullable=False)
    config_name = Column(String(128), nullable=False)
    config_type = Column(String(32), nullable=False)  # 例如：'live_viewer', 'live_booking' 等
    selected_fields = Column(JSON, nullable=False)  # 存储选中的字段列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ExportConfig(user_id='{self.user_id}', config_name='{self.config_name}', config_type='{self.config_type}')>" 