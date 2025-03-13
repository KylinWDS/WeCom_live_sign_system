from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum
from datetime import datetime
from typing import Optional

class LivingStatus(enum.Enum):
    """直播状态"""
    RESERVED = 0  # 预约中
    LIVING = 1    # 直播中
    ENDED = 2     # 已结束
    EXPIRED = 3   # 已过期
    CANCELLED = 4 # 已取消

class LivingType(enum.Enum):
    """直播类型"""
    GENERAL = 0   # 通用直播
    SMALL = 1     # 小班课
    LARGE = 2     # 大班课
    TRAINING = 3  # 企业培训
    EVENT = 4     # 活动直播

class Living(BaseModel):
    """直播模型"""
    __tablename__ = "livings"
    
    livingid = Column(String(50), unique=True, nullable=False, comment="直播ID")
    theme = Column(String(100), nullable=False, comment="直播主题")
    living_start = Column(DateTime, nullable=False, comment="直播开始时间")
    living_duration = Column(Integer, nullable=False, comment="直播时长(秒)")
    anchor_userid = Column(String(50), nullable=False, comment="主播用户ID")
    description = Column(Text, nullable=True, comment="直播描述")
    type = Column(Enum(LivingType), nullable=False, default=LivingType.GENERAL, comment="直播类型")
    status = Column(Enum(LivingStatus), nullable=False, default=LivingStatus.RESERVED, comment="直播状态")
    corpname = Column(String(100), nullable=False, comment="所属企业名称")
    agentid = Column(String(50), nullable=False, comment="应用ID")
    
    # 统计数据
    viewer_num = Column(Integer, default=0, comment="观看总人数")
    comment_num = Column(Integer, default=0, comment="评论数")
    mic_num = Column(Integer, default=0, comment="连麦发言人数")
    online_count = Column(Integer, default=0, comment="当前在线人数")
    subscribe_count = Column(Integer, default=0, comment="预约人数")
    
    # 关联
    watch_stats = relationship("WatchStat", back_populates="living")
    sign_records = relationship("SignRecord", back_populates="living")

    def __init__(
        self,
        id: int,
        name: str,
        start_time: str,
        end_time: str,
        status: str,
        created_at: str,
        updated_at: str
    ):
        self.id = id
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
    
    def is_active(self) -> bool:
        """检查直播是否正在进行中
        
        Returns:
            bool: 是否正在进行中
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.start_time <= now <= self.end_time
    
    def is_ended(self) -> bool:
        """检查直播是否已结束
        
        Returns:
            bool: 是否已结束
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return now > self.end_time
    
    def get_duration(self) -> int:
        """获取直播时长（分钟）
        
        Returns:
            int: 直播时长
        """
        start = datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")
        return int((end - start).total_seconds() / 60)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class WatchStat(BaseModel):
    """观看统计模型"""
    __tablename__ = "watch_stats"
    
    living_id = Column(Integer, ForeignKey("livings.id"), nullable=False)
    userid = Column(String(50), nullable=False, comment="用户ID")
    name = Column(String(50), nullable=False, comment="用户名称")
    watch_time = Column(Integer, default=0, comment="观看时长(秒)")
    is_comment = Column(Integer, default=0, comment="是否评论")
    is_mic = Column(Integer, default=0, comment="是否连麦")
    invitor_userid = Column(String(50), nullable=True, comment="邀请人ID")
    invitor_name = Column(String(50), nullable=True, comment="邀请人名称")
    user_type = Column(Integer, default=1, comment="用户类型：1-微信用户，2-企业微信用户")
    ip = Column(String(50), nullable=True, comment="用户IP")
    location = Column(JSON, nullable=True, comment="用户地理位置")
    device_info = Column(JSON, nullable=True, comment="设备信息")
    
    # 关联
    living = relationship("Living", back_populates="watch_stats")

class SignRecord(BaseModel):
    """签到记录模型"""
    __tablename__ = "sign_records"
    
    living_id = Column(Integer, ForeignKey("livings.id"), nullable=False)
    userid = Column(String(50), nullable=False, comment="用户ID")
    name = Column(String(50), nullable=False, comment="用户名称")
    sign_time = Column(DateTime, nullable=False, comment="签到时间")
    sign_type = Column(Integer, default=1, comment="签到类型：1-正常签到，2-补签")
    answer_content = Column(Text, nullable=True, comment="签到答题内容")
    invite_code = Column(String(50), nullable=True, comment="签到邀请码")
    
    # 关联
    living = relationship("Living", back_populates="sign_records") 