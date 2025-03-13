from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.utils.logger import get_logger
from src.models.base import BaseModel

logger = get_logger(__name__)

class LiveStatus:
    """直播状态 (企业微信官方文档定义)"""
    RESERVING = 0  # 预约中
    LIVING = 1     # 直播中
    ENDED = 2      # 已结束
    EXPIRED = 3    # 已过期
    CANCELLED = 4  # 已取消

class LiveType:
    """直播类型 (企业微信官方文档定义)"""
    GENERAL = 0    # 通用直播
    SMALL = 1      # 小班课
    LARGE = 2      # 大班课
    TRAINING = 3   # 企业培训
    EVENT = 4      # 活动直播

class LiveBooking(BaseModel):
    """直播预约模型"""
    
    __tablename__ = "live_bookings"
    
    # 基本信息
    livingid = Column(String(50), unique=True, nullable=False, comment="直播ID")
    theme = Column(String(100), nullable=False, comment="直播主题")
    living_start = Column(DateTime, nullable=False, comment="直播开始时间")
    living_duration = Column(Integer, nullable=False, comment="直播时长(秒)")
    anchor_userid = Column(String(50), nullable=False, comment="主播用户ID")
    description = Column(Text, nullable=True, comment="直播描述")
    type = Column(Integer, nullable=False, default=LiveType.TRAINING, comment="直播类型")
    status = Column(Integer, nullable=False, default=LiveStatus.RESERVING, comment="直播状态")
    
    # 企业信息
    corpname = Column(String(100), nullable=False, comment="所属企业名称")
    agentid = Column(String(50), nullable=False, comment="应用ID")
    
    # 统计数据
    viewer_num = Column(Integer, default=0, comment="观看总人数")
    comment_num = Column(Integer, default=0, comment="评论数")
    mic_num = Column(Integer, default=0, comment="连麦发言人数")
    online_count = Column(Integer, default=0, comment="当前在线人数")
    subscribe_count = Column(Integer, default=0, comment="预约人数")
    main_department = Column(Integer, nullable=True, comment="主播所在主部门id")
    open_replay = Column(Integer, default=0, comment="是否开启回放，1表示开启，0表示关闭")
    replay_status = Column(Integer, nullable=True, comment="回放状态：0-生成成功，1-生成中，2-已删除，3-生成失败")
    push_stream_url = Column(String(500), nullable=True, comment="推流地址")
    
    # 关联
    viewers = relationship("LiveViewer", back_populates="live_booking", lazy="dynamic", cascade="all, delete-orphan")
    sign_records = relationship("SignRecord", back_populates="live_booking", lazy="dynamic", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "livingid": self.livingid,
            "theme": self.theme,
            "living_start": int(self.living_start.timestamp()) if self.living_start else None,  # 转换为时间戳
            "living_duration": self.living_duration,
            "anchor_userid": self.anchor_userid,
            "description": self.description,
            "type": self.type,
            "status": self.status,
            "corpname": self.corpname,
            "agentid": self.agentid,
            "viewer_num": self.viewer_num,
            "comment_num": self.comment_num,
            "mic_num": self.mic_num,
            "online_count": self.online_count,
            "subscribe_count": self.subscribe_count,
            "main_department": self.main_department,
            "open_replay": self.open_replay,
            "replay_status": self.replay_status,
            "push_stream_url": self.push_stream_url
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> "LiveBooking":
        """从字典创建直播预约"""
        try:
            # 转换时间戳为datetime对象
            if "living_start" in data and isinstance(data["living_start"], (int, float)):
                data["living_start"] = datetime.fromtimestamp(data["living_start"])
            elif "living_start" in data and isinstance(data["living_start"], str):
                data["living_start"] = datetime.strptime(data["living_start"], "%Y-%m-%d %H:%M:%S")
            
            return cls(**data)
            
        except Exception as e:
            logger.error(f"从字典创建直播预约失败: {str(e)}")
            raise
    
    def is_active(self) -> bool:
        """检查直播是否正在进行中"""
        return self.status == LiveStatus.LIVING
    
    def is_ended(self) -> bool:
        """检查直播是否已结束"""
        return self.status in [LiveStatus.ENDED, LiveStatus.EXPIRED, LiveStatus.CANCELLED]
    
    def update_from_api(self, api_data: dict):
        """从企业微信API返回数据更新直播信息"""
        try:
            self.theme = api_data.get("theme", self.theme)
            self.living_start = datetime.fromtimestamp(api_data["living_start"]) if "living_start" in api_data else self.living_start
            self.living_duration = api_data.get("living_duration", self.living_duration)
            self.anchor_userid = api_data.get("anchor_userid", self.anchor_userid)
            self.description = api_data.get("description", self.description)
            self.type = api_data.get("type", self.type)
            self.status = api_data.get("status", self.status)
            self.viewer_num = api_data.get("viewer_num", self.viewer_num)
            self.comment_num = api_data.get("comment_num", self.comment_num)
            self.mic_num = api_data.get("mic_num", self.mic_num)
            self.online_count = api_data.get("online_count", self.online_count)
            self.subscribe_count = api_data.get("subscribe_count", self.subscribe_count)
            self.main_department = api_data.get("main_department", self.main_department)
            self.open_replay = api_data.get("open_replay", self.open_replay)
            self.replay_status = api_data.get("replay_status", self.replay_status)
            self.push_stream_url = api_data.get("push_stream_url", self.push_stream_url)
            
        except Exception as e:
            logger.error(f"更新直播信息失败: {str(e)}")
            raise 