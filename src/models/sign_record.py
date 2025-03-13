from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.utils.logger import get_logger
from src.models.base import BaseModel

logger = get_logger(__name__)

class SignStatus:
    """签到状态"""
    NORMAL = 1  # 正常签到
    LATE = 2    # 迟到签到
    EARLY_LEAVE = 3  # 早退
    MAKEUP = 4  # 补签

class SignRecord(BaseModel):
    """签到记录模型"""
    
    __tablename__ = "sign_records"
    
    # 用户信息
    userid = Column(String(50), nullable=True, comment="企业成员userid")
    external_userid = Column(String(50), nullable=True, comment="外部成员userid")
    name = Column(String(50), nullable=False, comment="签到用户名称")
    department = Column(String(200), nullable=True, comment="所在部门")
    
    # 签到信息
    sign_time = Column(DateTime, nullable=False, comment="签到时间")
    sign_count = Column(Integer, default=1, comment="签到次数")
    status = Column(Integer, nullable=False, default=SignStatus.NORMAL, comment="签到状态")
    is_makeup = Column(Boolean, default=False, comment="是否补签")
    makeup_reason = Column(Text, nullable=True, comment="补签原因")
    
    # 签到码信息
    enter_code = Column(String(50), nullable=True, comment="进入直播间邀请码")
    sign_code = Column(String(50), nullable=True, comment="签到邀请码")
    
    # 答题信息
    has_quiz = Column(Boolean, default=False, comment="是否有答题")
    quiz_score = Column(Integer, nullable=True, comment="答题得分")
    quiz_answers = Column(Text, nullable=True, comment="答题答案")
    
    # 地理位置信息
    city = Column(String(50), nullable=True, comment="签到城市")
    latitude = Column(String(20), nullable=True, comment="纬度")
    longitude = Column(String(20), nullable=True, comment="经度")
    ip = Column(String(50), nullable=True, comment="IP地址")
    
    # 关联
    live_booking_id = Column(Integer, ForeignKey("live_bookings.id"), nullable=False)
    live_booking = relationship("LiveBooking", back_populates="sign_records")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "userid": self.userid,
            "external_userid": self.external_userid,
            "name": self.name,
            "department": self.department,
            "sign_time": int(self.sign_time.timestamp()) if self.sign_time else None,
            "sign_count": self.sign_count,
            "status": self.status,
            "is_makeup": self.is_makeup,
            "makeup_reason": self.makeup_reason,
            "enter_code": self.enter_code,
            "sign_code": self.sign_code,
            "has_quiz": self.has_quiz,
            "quiz_score": self.quiz_score,
            "quiz_answers": self.quiz_answers,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "ip": self.ip,
            "live_booking_id": self.live_booking_id
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> "SignRecord":
        """从字典创建签到记录"""
        try:
            # 处理微信用户名后缀
            if "name" in data and isinstance(data["name"], str):
                data["name"] = cls.process_wechat_name(data["name"])
            
            # 转换时间戳为datetime对象
            if "sign_time" in data:
                if isinstance(data["sign_time"], (int, float)):
                    data["sign_time"] = datetime.fromtimestamp(data["sign_time"])
                elif isinstance(data["sign_time"], str):
                    data["sign_time"] = datetime.strptime(data["sign_time"], "%Y-%m-%d %H:%M:%S")
            
            return cls(**data)
            
        except Exception as e:
            logger.error(f"从字典创建签到记录失败: {str(e)}")
            raise
    
    @staticmethod
    def process_wechat_name(name: str) -> str:
        """处理微信用户名（去除@微信后缀）"""
        if name and name.endswith("@微信"):
            return name[:-3]
        return name
    
    def increment_sign_count(self):
        """增加签到次数"""
        try:
            self.sign_count += 1
            self.sign_time = datetime.now()
        except Exception as e:
            logger.error(f"增加签到次数失败: {str(e)}")
            raise
    
    def is_late(self) -> bool:
        """检查是否迟到"""
        try:
            if not self.live_booking or not self.live_booking.living_start:
                return False
                
            return self.sign_time > self.live_booking.living_start
            
        except Exception as e:
            logger.error(f"检查是否迟到失败: {str(e)}")
            return False
    
    def is_early_leave(self) -> bool:
        """检查是否早退"""
        try:
            if not self.live_booking or not self.live_booking.living_start or not self.live_booking.living_duration:
                return False
                
            end_time = self.live_booking.living_start + timedelta(seconds=self.live_booking.living_duration)
            return self.sign_time < end_time
            
        except Exception as e:
            logger.error(f"检查是否早退失败: {str(e)}")
            return False
    
    def update_status(self):
        """更新签到状态"""
        try:
            if self.is_late():
                self.status = SignStatus.LATE
            elif self.is_early_leave():
                self.status = SignStatus.EARLY_LEAVE
            elif self.is_makeup:
                self.status = SignStatus.MAKEUP
            else:
                self.status = SignStatus.NORMAL
                
        except Exception as e:
            logger.error(f"更新签到状态失败: {str(e)}")
            raise
    
    @classmethod
    def from_excel(cls, excel_data: dict, live_booking_id: int) -> "SignRecord":
        """从Excel数据创建签到记录"""
        try:
            sign_time = datetime.strptime(excel_data["签到发起时间"], "%Y.%m.%d %H:%M")
            name = cls.process_wechat_name(excel_data["已签到成员"])
            department = excel_data.get("所在部门", "-")
            
            return cls(
                name=name,
                department=department,
                sign_time=sign_time,
                live_booking_id=live_booking_id
            )
            
        except Exception as e:
            logger.error(f"从Excel创建签到记录失败: {str(e)}")
            raise 