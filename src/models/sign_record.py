from datetime import datetime
from typing import Optional, Dict
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from src.utils.logger import get_logger
from src.models.base import BaseModel

logger = get_logger(__name__)

class SignRecord(BaseModel):
    """签到记录模型"""
    
    __tablename__ = "sign_records"
    
    # 基本信息
    name = Column(String(50), nullable=False, comment="签到用户名称")
    department = Column(String(200), nullable=True, comment="所在部门")
    sign_time = Column(DateTime, nullable=False, comment="签到时间")
    user_type = Column(Integer, default=1, comment="用户类型：1-微信用户，2-企业微信用户")
    
    # 关联
    living_id = Column(Integer, ForeignKey("livings.id"), nullable=False)
    living = relationship("Living", back_populates="sign_records")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "department": self.department,
            "sign_time": int(self.sign_time.timestamp()) if self.sign_time else None,
            "living_id": self.living_id,
            "user_type": self.user_type
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
                    data["sign_time"] = datetime.strptime(data["sign_time"], "%Y.%m.%d %H:%M")
            
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
    
    @classmethod
    def from_excel(cls, excel_data: dict, live_booking_id: int) -> "SignRecord":
        """从Excel数据创建签到记录"""
        try:
            sign_time = datetime.strptime(excel_data["签到发起时间"], "%Y.%m.%d %H:%M")
            name = cls.process_wechat_name(excel_data["已签到成员"])
            department = excel_data.get("所在部门", "-")
            
            # 根据名字是否包含@微信来判断用户类型
            user_type = 1 if excel_data["已签到成员"].endswith("@微信") else 2
            
            return cls(
                name=name,
                department=department,
                sign_time=sign_time,
                living_id=live_booking_id,
                user_type=user_type
            )
            
        except Exception as e:
            logger.error(f"从Excel创建签到记录失败: {str(e)}")
            raise
            
    @classmethod
    def get_sign_statistics(cls, live_booking_id: int) -> Dict[str, any]:
        """获取签到统计信息
        
        Args:
            live_booking_id: 直播预约ID
            
        Returns:
            Dict[str, any]: 统计信息，包含签到时间和签到人数
        """
        try:
            from src.core.database import DatabaseManager
            # 修复数据库连接获取方式
            db_manager = DatabaseManager()  # 直接创建实例
            
            with db_manager.get_session() as session:
                # 获取最早的签到时间
                first_sign = session.query(cls).filter_by(living_id=live_booking_id).order_by(cls.sign_time.asc()).first()
                sign_time = first_sign.sign_time if first_sign else None
                
                # 获取签到人数
                sign_count = session.query(func.count(cls.id)).filter_by(living_id=live_booking_id).scalar()
                
                # 获取去重后的签到人员数量
                unique_signers = session.query(func.count(func.distinct(cls.name))).filter_by(living_id=live_booking_id).scalar()
            
            return {
                "sign_time": sign_time.strftime("%Y.%m.%d %H:%M") if sign_time else None,
                "sign_count": sign_count,  # 总签到次数
                "unique_signers": unique_signers  # 不同的签到人数
            }
            
        except Exception as e:
            logger.error(f"获取签到统计信息失败: {str(e)}")
            return {
                "sign_time": None,
                "sign_count": 0,
                "unique_signers": 0
            } 