from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel


class LiveSignRecord(BaseModel):
    """直播签到记录明细模型
    
    用于记录用户的每次签到详情，支持多次签到
    """
    __tablename__ = "live_sign_records"
    
    viewer_id = Column(Integer, ForeignKey("live_viewers.id"), nullable=False, index=True, comment="关联的观众ID")
    living_id = Column(String(50), nullable=False, index=True, comment="直播ID，对应livings表的livingid字段")
    sign_time = Column(DateTime, nullable=False, comment="签到时间")
    sign_type = Column(String(20), nullable=False, comment="签到类型(自动/手动/导入)")
    sign_location = Column(JSON, nullable=True, comment="签到地点")
    sign_remark = Column(String(200), nullable=True, comment="签到备注")
    is_valid = Column(Boolean, default=True, comment="签到是否有效")
    sign_sequence = Column(Integer, default=1, comment="第几次签到，对应导入签到文件的sheet顺序")
    sheet_name = Column(String(100), nullable=True, comment="签到sheet页名称，对应导入时的sheet页名称")
    
    # 关联到LiveViewer
    viewer = relationship("LiveViewer", back_populates="sign_records")
    
    def __init__(
        self,
        viewer_id: int,
        sign_time: datetime,
        sign_type: str,
        living_id: str,
        sign_location: Optional[Dict[str, Any]] = None,
        sign_remark: Optional[str] = None,
        is_valid: bool = True,
        sign_sequence: int = 1,
        sheet_name: Optional[str] = None
    ):
        self.viewer_id = viewer_id
        self.sign_time = sign_time
        self.sign_type = sign_type
        self.living_id = living_id
        self.sign_location = sign_location
        self.sign_remark = sign_remark
        self.is_valid = is_valid
        self.sign_sequence = sign_sequence
        self.sheet_name = sheet_name
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "viewer_id": self.viewer_id,
            "living_id": self.living_id,
            "sign_time": self.sign_time,
            "sign_type": self.sign_type,
            "sign_location": self.sign_location,
            "sign_remark": self.sign_remark,
            "is_valid": self.is_valid,
            "sign_sequence": self.sign_sequence,
            "sheet_name": self.sheet_name,
            "create_time": self.create_time,
            "update_time": self.update_time
        } 