from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from src.utils.logger import get_logger
from src.models.base import BaseModel

logger = get_logger(__name__)

class UserRole:
    """用户角色"""
    ROOT_ADMIN = "ROOT_ADMIN"     # 超级管理员（root-admin）
    WECOM_ADMIN = "WECOM_ADMIN"   # 企业微信管理员
    NORMAL = "NORMAL"             # 普通用户

class User(BaseModel):
    """用户模型"""
    
    __tablename__ = "users"
    
    # 基本信息
    userid = Column(String(50), unique=True, nullable=False, comment="用户ID")
    name = Column(String(50), nullable=False, comment="用户名称")
    role = Column(String(20), nullable=False, default=UserRole.NORMAL, comment="用户角色")
    
    # 企业信息
    corpname = Column(String(100), nullable=True, comment="所属企业名称")
    corpid = Column(String(50), nullable=True, comment="企业ID")
    corpsecret = Column(String(100), nullable=True, comment="企业应用Secret")
    agentid = Column(String(50), nullable=True, comment="应用ID")
    
    # 管理员信息
    is_admin = Column(Boolean, default=False, comment="是否为管理员")
    password_hash = Column(String(100), nullable=True, comment="密码哈希")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "userid": self.userid,
            "name": self.name,
            "role": self.role,
            "corpname": self.corpname,
            "corpid": self.corpid,
            "corpsecret": self.corpsecret,
            "agentid": self.agentid,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S") if self.last_login else None
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """从字典创建用户"""
        try:
            # 转换时间字符串为datetime对象
            if "last_login" in data and isinstance(data["last_login"], str):
                data["last_login"] = datetime.strptime(data["last_login"], "%Y-%m-%d %H:%M:%S")
            
            return cls(**data)
            
        except Exception as e:
            logger.error(f"从字典创建用户失败: {str(e)}")
            raise
    
    def is_root_admin(self) -> bool:
        """是否为超级管理员"""
        return self.userid == "root-admin" and self.role == UserRole.ROOT_ADMIN
    
    def is_wecom_admin(self) -> bool:
        """是否为企业微信管理员"""
        return self.role == UserRole.WECOM_ADMIN
    
    def is_normal_user(self) -> bool:
        """是否为普通用户"""
        return self.role == UserRole.NORMAL
    
    def set_password(self, password: str):
        """设置密码"""
        try:
            # TODO: 实现密码加密
            self.password_hash = password
        except Exception as e:
            logger.error(f"设置密码失败: {str(e)}")
            raise
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        try:
            # TODO: 实现密码验证
            return self.password_hash == password
        except Exception as e:
            logger.error(f"验证密码失败: {str(e)}")
            return False
    
    def update_last_login(self):
        """更新最后登录时间"""
        try:
            self.last_login = datetime.now()
            
        except Exception as e:
            logger.error(f"更新最后登录时间失败: {str(e)}")
            raise 