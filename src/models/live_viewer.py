from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
from .living import Living
from ..utils.logger import get_logger
import enum

logger = get_logger(__name__)

class UserSource(enum.Enum):
    """用户来源"""
    INTERNAL = "users"          # 内部企业成员
    EXTERNAL = "external_users" # 外部联系人

class LiveViewer(BaseModel):
    """直播参与者模型
    
    整合了观看统计(WatchStat)、观众(LiveViewer)和签到记录(SignRecord)的功能
    """
    __tablename__ = "live_viewers"
    __table_args__ = {'extend_existing': True}  # 允许表重复定义
    
    # 关联直播
    living_id = Column(Integer, ForeignKey("livings.id"), nullable=False, index=True)
    
    # 用户基本信息
    userid = Column(String(50), nullable=False, index=True, comment="用户ID")
    name = Column(String(100), nullable=False, comment="用户名称")
    user_source = Column(Enum(UserSource), nullable=False, comment="用户来源(内部/外部)")
    user_type = Column(Integer, default=1, comment="用户类型：1-微信用户，2-企业微信用户")
    department = Column(String(100), nullable=True, comment="部门名称")
    department_id = Column(String(50), nullable=True, comment="部门ID")
    
    # 观看信息
    watch_time = Column(Integer, default=0, comment="观看时长(秒)")
    is_comment = Column(Integer, default=0, comment="是否评论(0-否,1-是)")
    is_mic = Column(Integer, default=0, comment="是否连麦(0-否,1-是)")
    access_channel = Column(String(50), nullable=True, comment="访问渠道")
    
    # 签到信息
    is_signed = Column(Boolean, default=False, comment="是否已签到")
    sign_time = Column(DateTime, nullable=True, comment="签到时间")
    sign_type = Column(String(20), nullable=True, comment="签到类型(自动/手动/导入)")
    sign_location = Column(JSON, nullable=True, comment="签到地点")
    sign_count = Column(Integer, default=0, comment="签到次数")
    
    # 邀请关系
    invitor_userid = Column(String(50), nullable=True, comment="邀请人ID")
    invitor_name = Column(String(50), nullable=True, comment="邀请人名称")
    
    # 设备和IP信息
    ip = Column(String(50), nullable=True, comment="用户IP")
    location = Column(JSON, nullable=True, comment="用户地理位置")
    device_info = Column(JSON, nullable=True, comment="设备信息")
    
    # 奖励信息
    is_reward_eligible = Column(Boolean, default=False, comment="是否符合奖励条件")
    reward_amount = Column(Float, default=0.0, comment="红包奖励金额")
    reward_status = Column(String(20), nullable=True, comment="奖励发放状态")
    
    # 关联
    living = relationship("Living", back_populates="viewers")
    
    # 兼容旧版关系
    live_booking_id = Column(Integer, ForeignKey("live_bookings.id"), nullable=True)
    live_booking = relationship("LiveBooking", foreign_keys=[live_booking_id], backref="viewers_old")
    
    def __init__(
        self,
        living_id: int,
        userid: str,
        name: str,
        user_source: UserSource,
        user_type: int = 1,
        department: Optional[str] = None,
        department_id: Optional[str] = None,
        watch_time: int = 0,
        is_comment: int = 0,
        is_mic: int = 0,
        access_channel: Optional[str] = None,
        is_signed: bool = False,
        sign_time: Optional[datetime] = None,
        sign_type: Optional[str] = None,
        sign_location: Optional[Dict[str, Any]] = None,
        sign_count: int = 0,
        invitor_userid: Optional[str] = None,
        invitor_name: Optional[str] = None,
        ip: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        device_info: Optional[Dict[str, Any]] = None,
        is_reward_eligible: bool = False,
        reward_amount: float = 0.0,
        reward_status: Optional[str] = None
    ):
        self.living_id = living_id
        self.userid = userid
        self.name = name
        self.user_source = user_source
        self.user_type = user_type
        self.department = department
        self.department_id = department_id
        self.watch_time = watch_time
        self.is_comment = is_comment
        self.is_mic = is_mic
        self.access_channel = access_channel
        self.is_signed = is_signed
        self.sign_time = sign_time
        self.sign_type = sign_type
        self.sign_location = sign_location
        self.sign_count = sign_count
        self.invitor_userid = invitor_userid
        self.invitor_name = invitor_name
        self.ip = ip
        self.location = location
        self.device_info = device_info
        self.is_reward_eligible = is_reward_eligible
        self.reward_amount = reward_amount
        self.reward_status = reward_status
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LiveViewer':
        """从字典创建实例"""
        return cls(**data)
    
    @classmethod
    def from_api_data(cls, living_id: int, user_data: Dict[str, Any], source: UserSource) -> 'LiveViewer':
        """从API数据创建实例
        
        Args:
            living_id: 直播ID
            user_data: 用户数据
            source: 用户来源
            
        Returns:
            LiveViewer: 新创建的实例
        """
        # 根据不同的用户来源处理不同的字段
        if source == UserSource.INTERNAL:
            # 内部成员
            return cls(
                living_id=living_id,
                userid=user_data.get("userid", ""),
                name=user_data.get("name", ""),
                user_source=source,
                user_type=2,  # 企业微信用户
                department=user_data.get("department_name", ""),
                department_id=str(user_data.get("department_id", "")),
                watch_time=user_data.get("watch_time", 0),
                is_comment=1 if user_data.get("is_comment") else 0,
                is_mic=1 if user_data.get("is_mic") else 0
            )
        else:
            # 外部联系人
            return cls(
                living_id=living_id,
                userid=user_data.get("userid", ""),
                name=user_data.get("name", ""),
                user_source=source,
                user_type=1,  # 微信用户
                watch_time=user_data.get("watch_time", 0),
                is_comment=1 if user_data.get("is_comment") else 0,
                is_mic=1 if user_data.get("is_mic") else 0
            )
    
    def update_watch_stats(self, watch_time: int, is_comment: int = None, is_mic: int = None) -> None:
        """更新观看统计信息
        
        Args:
            watch_time: 观看时长
            is_comment: 是否评论
            is_mic: 是否连麦
        """
        self.watch_time = watch_time
        
        if is_comment is not None:
            self.is_comment = is_comment
            
        if is_mic is not None:
            self.is_mic = is_mic
            
        # 检查是否符合奖励条件
        self.check_reward_criteria()
    
    def record_sign(
        self, 
        sign_time: datetime = None, 
        sign_type: str = "auto", 
        location: Dict[str, Any] = None
    ) -> None:
        """记录签到
        
        Args:
            sign_time: 签到时间，默认为当前时间
            sign_type: 签到类型，默认为自动签到
            location: 签到地点信息
        """
        self.is_signed = True
        self.sign_time = sign_time or datetime.now()
        self.sign_type = sign_type
        self.sign_count += 1
        
        if location:
            self.sign_location = location
            
        # 检查是否符合奖励条件
        self.check_reward_criteria()
    
    @staticmethod
    def process_wechat_name(name: str) -> str:
        """处理微信用户名（去除@微信后缀）"""
        if name and name.endswith("@微信"):
            return name[:-3]
        return name

    def record_invitation(self, invitor_userid: str, invitor_name: str) -> None:
        """记录邀请关系
        
        Args:
            invitor_userid: 邀请人用户ID
            invitor_name: 邀请人名称
        """
        self.invitor_userid = invitor_userid
        self.invitor_name = invitor_name
    
    def update_device_info(self, ip: str = None, location: Dict[str, Any] = None, device_info: Dict[str, Any] = None) -> None:
        """更新设备信息
        
        Args:
            ip: IP地址
            location: 地理位置信息
            device_info: 设备信息
        """
        if ip:
            self.ip = ip
            
        if location:
            self.location = location
            
        if device_info:
            self.device_info = device_info
    
    def check_reward_criteria(self) -> bool:
        """检查是否符合奖励条件
        
        默认条件:
        1. 观看时长 >= 5分钟 (300秒)
        2. 已签到
        
        Returns:
            bool: 是否符合条件
        """
        # 检查条件：观看时长大于5分钟且已签到
        is_eligible = self.watch_time >= 300 and self.is_signed
        
        # 更新奖励状态
        self.is_reward_eligible = is_eligible
        
        # 如果符合条件但奖励金额为0，设置默认奖励金额
        if is_eligible and self.reward_amount == 0:
            self.reward_amount = 5.0  # 默认奖励金额
        
        return is_eligible
    
    def set_reward_amount(self, amount: float, status: str = None) -> None:
        """设置奖励金额
        
        Args:
            amount: 奖励金额
            status: 奖励状态
        """
        self.reward_amount = amount
        
        if status:
            self.reward_status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "living_id": self.living_id,
            "userid": self.userid,
            "name": self.name,
            "user_source": self.user_source.value,
            "user_type": self.user_type,
            "department": self.department,
            "department_id": self.department_id,
            "watch_time": self.watch_time,
            "is_comment": self.is_comment,
            "is_mic": self.is_mic,
            "access_channel": self.access_channel,
            "is_signed": self.is_signed,
            "sign_time": self.sign_time,
            "sign_type": self.sign_type,
            "sign_location": self.sign_location,
            "invitor_userid": self.invitor_userid,
            "invitor_name": self.invitor_name,
            "ip": self.ip,
            "location": self.location,
            "device_info": self.device_info,
            "is_reward_eligible": self.is_reward_eligible,
            "reward_amount": self.reward_amount,
            "reward_status": self.reward_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_watch_stat(cls, watch_stat):
        """从WatchStat对象创建LiveViewer对象（用于数据迁移）
        
        已弃用: 此方法仅用于数据迁移，将在未来版本中移除
        """
        import warnings
        warnings.warn("此方法已弃用，仅用于数据迁移", DeprecationWarning, stacklevel=2)
        
        # 无法确定用户来源，默认设为外部用户
        user_source = UserSource.EXTERNAL
        if hasattr(watch_stat, 'user_type') and watch_stat.user_type == 2:
            user_source = UserSource.INTERNAL
            
        return cls(
            living_id=watch_stat.living_id,
            userid=watch_stat.userid,
            name=watch_stat.name,
            user_source=user_source,
            user_type=watch_stat.user_type,
            watch_time=watch_stat.watch_time,
            is_comment=bool(watch_stat.is_comment),
            is_mic=bool(watch_stat.is_mic),
            invitor_userid=watch_stat.invitor_userid,
            invitor_name=watch_stat.invitor_name,
            ip=watch_stat.ip,
            location=watch_stat.location,
            device_info=watch_stat.device_info
        )
        
    @classmethod
    def from_sign_record(cls, sign_record):
        """从SignRecord对象创建LiveViewer对象（用于数据迁移）
        
        已弃用: 此方法仅用于数据迁移，将在未来版本中移除
        """
        import warnings
        warnings.warn("此方法已弃用，仅用于数据迁移", DeprecationWarning, stacklevel=2)
        
        # 无法确定用户来源，默认设为外部用户
        user_source = UserSource.EXTERNAL
        if hasattr(sign_record, 'user_type') and sign_record.user_type == 2:
            user_source = UserSource.INTERNAL
            
        return cls(
            living_id=sign_record.living_id,
            userid=sign_record.userid if hasattr(sign_record, 'userid') else "",
            name=sign_record.user_name if hasattr(sign_record, 'user_name') else sign_record.name,
            user_source=user_source,
            user_type=sign_record.user_type if hasattr(sign_record, 'user_type') else 1,
            department=sign_record.department if hasattr(sign_record, 'department') else None,
            is_signed=True,
            sign_time=sign_record.sign_time,
            sign_type=sign_record.sign_type if hasattr(sign_record, 'sign_type') else "manual",
            sign_location=sign_record.sign_location if hasattr(sign_record, 'sign_location') else None
        ) 