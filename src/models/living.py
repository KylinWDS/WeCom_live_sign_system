from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum
from datetime import datetime, timedelta
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
    
    # 状态标记
    is_viewer_fetched = Column(Integer, default=0, comment="是否已拉取观看信息(0-否,1-是)")
    is_sign_imported = Column(Integer, default=0, comment="是否已导入签到(0-否,1-是)")
    is_doc_uploaded = Column(Integer, default=0, comment="是否已上传企微文档(0-否,1-是)")
    is_remote_synced = Column(Integer, default=0, comment="是否已远程同步(0-否,1-是)")
    
    # 关联到LiveBooking
    live_booking_id = Column(Integer, ForeignKey('live_bookings.id'), nullable=True)
    live_booking = relationship('LiveBooking', backref='livings')
    
    # 关联到LiveViewer
    viewers = relationship("LiveViewer", back_populates="living", cascade="all, delete-orphan")
    
    # 关联到LiveRewardRecord
    reward_records = relationship("LiveRewardRecord", back_populates="living", cascade="all, delete-orphan")

    def __init__(
        self,
        livingid: str,
        theme: str,
        living_start: datetime,
        living_duration: int,
        anchor_userid: str,
        description: Optional[str] = None,
        status: LivingStatus = LivingStatus.RESERVED,
        type: LivingType = LivingType.GENERAL,
        corpname: str = "",
        agentid: str = "",
        viewer_num: int = 0,
        comment_num: int = 0,
        mic_num: int = 0,
        online_count: int = 0,
        subscribe_count: int = 0,
        is_viewer_fetched: int = 0,
        is_sign_imported: int = 0,
        is_doc_uploaded: int = 0,
        is_remote_synced: int = 0,
        live_booking_id: Optional[int] = None
    ):
        self.livingid = livingid
        self.theme = theme
        self.living_start = living_start
        self.living_duration = living_duration
        self.anchor_userid = anchor_userid
        self.description = description
        self.status = status
        self.type = type
        self.corpname = corpname
        self.agentid = agentid
        self.viewer_num = viewer_num
        self.comment_num = comment_num
        self.mic_num = mic_num
        self.online_count = online_count
        self.subscribe_count = subscribe_count
        self.is_viewer_fetched = is_viewer_fetched
        self.is_sign_imported = is_sign_imported
        self.is_doc_uploaded = is_doc_uploaded
        self.is_remote_synced = is_remote_synced
        self.live_booking_id = live_booking_id
    
    def is_active(self) -> bool:
        """检查直播是否正在进行中
        
        Returns:
            bool: 是否正在进行中
        """
        now = datetime.now()
        end_time = self.living_start + timedelta(seconds=self.living_duration)
        return self.living_start <= now <= end_time
    
    def is_ended(self) -> bool:
        """检查直播是否已结束
        
        Returns:
            bool: 是否已结束
        """
        now = datetime.now()
        end_time = self.living_start + timedelta(seconds=self.living_duration)
        return now > end_time
    
    def get_duration(self) -> int:
        """获取直播时长（分钟）
        
        Returns:
            int: 直播时长
        """
        # 直接使用living_duration（以秒为单位）并转换为分钟
        return int(self.living_duration / 60)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "livingid": self.livingid,
            "theme": self.theme,
            "living_start": self.living_start,
            "living_duration": self.living_duration,
            "anchor_userid": self.anchor_userid,
            "description": self.description,
            "status": self.status,
            "type": self.type,
            "corpname": self.corpname,
            "agentid": self.agentid,
            "viewer_num": self.viewer_num,
            "comment_num": self.comment_num,
            "mic_num": self.mic_num,
            "online_count": self.online_count,
            "subscribe_count": self.subscribe_count,
            "is_viewer_fetched": self.is_viewer_fetched,
            "is_sign_imported": self.is_sign_imported,
            "is_doc_uploaded": self.is_doc_uploaded,
            "is_remote_synced": self.is_remote_synced,
            "live_booking_id": self.live_booking_id
        } 