from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..utils.logger import get_logger
from .base import BaseModel
from .live_booking import LiveBooking

logger = get_logger(__name__)

class LiveViewer(BaseModel):
    """直播观众模型"""
    __tablename__ = 'live_viewers'
    __table_args__ = {'extend_existing': True}  # 允许表重复定义
    
    # 用户信息
    userid = Column(String(50), nullable=True, comment="企业成员userid")
    external_userid = Column(String(50), nullable=True, comment="外部成员userid")
    name = Column(String(50), nullable=False, comment="观看者名称")
    type = Column(Integer, nullable=False, default=1, comment="观看者类型：1-微信用户，2-企业微信用户")
    department = Column(String(200), nullable=True, comment="所在部门")
    
    # 观看信息
    watch_time = Column(Integer, default=0, comment="观看时长(秒)")
    first_enter_time = Column(DateTime, nullable=True, comment="首次进入时间")
    last_enter_time = Column(DateTime, nullable=True, comment="最后进入时间")
    is_comment = Column(Boolean, default=False, comment="是否评论")
    is_mic = Column(Boolean, default=False, comment="是否连麦")
    
    # 邀请信息
    invitor_userid = Column(String(50), nullable=True, comment="邀请人userid")
    invitor_external_userid = Column(String(50), nullable=True, comment="邀请人external_userid")
    invitor_name = Column(String(50), nullable=True, comment="邀请人名称")
    
    # 地理位置
    city = Column(String(50), nullable=True, comment="城市")
    latitude = Column(String(20), nullable=True, comment="纬度")
    longitude = Column(String(20), nullable=True, comment="经度")
    ip = Column(String(50), nullable=True, comment="IP地址")
    
    # 访问渠道
    access_channel = Column(String(50), nullable=True, comment="访问渠道")
    
    # 关联
    live_booking_id = Column(Integer, ForeignKey("live_bookings.id"), nullable=False)
    live_booking = relationship(LiveBooking, back_populates="viewers", foreign_keys=[live_booking_id])
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "userid": self.userid,
            "external_userid": self.external_userid,
            "name": self.name,
            "type": self.type,
            "department": self.department,
            "watch_time": self.watch_time,
            "first_enter_time": int(self.first_enter_time.timestamp()) if self.first_enter_time else None,
            "last_enter_time": int(self.last_enter_time.timestamp()) if self.last_enter_time else None,
            "is_comment": 1 if self.is_comment else 0,  # 转换为企业微信API格式
            "is_mic": 1 if self.is_mic else 0,  # 转换为企业微信API格式
            "invitor_userid": self.invitor_userid,
            "invitor_external_userid": self.invitor_external_userid,
            "invitor_name": self.invitor_name,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "ip": self.ip,
            "access_channel": self.access_channel,
            "live_booking_id": self.live_booking_id
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> "LiveViewer":
        """从字典创建观看者记录"""
        try:
            # 处理微信用户名后缀
            if "name" in data and isinstance(data["name"], str):
                data["name"] = cls.process_wechat_name(data["name"])
            
            # 转换布尔值
            if "is_comment" in data:
                data["is_comment"] = bool(data["is_comment"])
            if "is_mic" in data:
                data["is_mic"] = bool(data["is_mic"])
            
            # 转换时间戳为datetime对象
            for field in ["first_enter_time", "last_enter_time"]:
                if field in data:
                    if isinstance(data[field], (int, float)):
                        data[field] = datetime.fromtimestamp(data[field])
                    elif isinstance(data[field], str):
                        data[field] = datetime.strptime(data[field], "%Y-%m-%d %H:%M:%S")
            
            return cls(**data)
            
        except Exception as e:
            logger.error(f"从字典创建观看者记录失败: {str(e)}")
            raise
    
    @staticmethod
    def process_wechat_name(name: str) -> str:
        """处理微信用户名（去除@微信后缀）"""
        if name and name.endswith("@微信"):
            return name[:-3]
        return name
    
    def update_from_api(self, api_data: dict):
        """从企业微信API返回数据更新观看者信息"""
        try:
            self.name = self.process_wechat_name(api_data.get("name", self.name))
            self.type = api_data.get("type", self.type)
            self.watch_time = api_data.get("watch_time", self.watch_time)
            self.is_comment = bool(api_data.get("is_comment", self.is_comment))
            self.is_mic = bool(api_data.get("is_mic", self.is_mic))
            self.invitor_userid = api_data.get("invitor_userid", self.invitor_userid)
            self.invitor_external_userid = api_data.get("invitor_external_userid", self.invitor_external_userid)
            
            # 更新最后进入时间
            self.last_enter_time = datetime.now()
            if not self.first_enter_time:
                self.first_enter_time = self.last_enter_time
                
        except Exception as e:
            logger.error(f"更新观看者信息失败: {str(e)}")
            raise
    
    def update_watch_time(self, duration: int):
        """更新观看时长"""
        try:
            self.watch_time += duration
            self.last_enter_time = datetime.now()
            if not self.first_enter_time:
                self.first_enter_time = datetime.now()
                
        except Exception as e:
            logger.error(f"更新观看时长失败: {str(e)}")
            raise 