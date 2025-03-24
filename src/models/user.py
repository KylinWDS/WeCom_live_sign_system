from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from ..utils.logger import get_logger
from .base import Base
from enum import Enum as PyEnum
import os
import hashlib

logger = get_logger(__name__)

class UserRole(PyEnum):
    """用户角色"""
    ROOT_ADMIN = "ROOT_ADMIN"     # 超级管理员（root-admin）
    WECOM_ADMIN = "WECOM_ADMIN"   # 企业微信管理员
    NORMAL = "NORMAL"             # 普通用户

class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    # 基本信息
    userid = Column(Integer, primary_key=True, autoincrement=True)
    login_name = Column(String(50), unique=True, nullable=False, comment="登录名")
    name = Column(String(50), nullable=False, comment="用户名")
    role = Column(String(11), nullable=False, default=UserRole.NORMAL.value)
    
    # 企业信息
    corpname = Column(String(100), nullable=True, comment="企业名称")
    corpid = Column(String(50), nullable=True, comment="企业ID")
    corpsecret = Column(String(100), nullable=True, comment="企业应用Secret")
    agentid = Column(String(50), nullable=True, comment="应用ID")
    
    # 企业微信账号code
    wecom_code = Column(String(100), nullable=True, comment='企业微信账号code')
    
    # 管理员信息
    is_admin = Column(Boolean, default=False, comment="是否为管理员")
    password_hash = Column(String(128), nullable=True, comment="密码哈希")
    salt = Column(String(32), nullable=True, comment="密码盐值")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    last_active_time = Column(DateTime, nullable=True, comment="最后活跃时间")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联关系
    config_changes = relationship('ConfigChange', back_populates='user')
    operation_logs = relationship('OperationLog', back_populates='user')
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "userid": self.userid,
            "login_name": self.login_name,
            "name": self.name,
            "role": self.role,
            "corpname": self.corpname,
            "corpid": self.corpid,
            "corpsecret": self.corpsecret,
            "agentid": self.agentid,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S") if self.last_login else None,
            "last_active_time": self.last_active_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_active_time else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """从字典创建用户"""
        try:
            # 转换时间字符串为datetime对象
            for field in ["last_login", "created_at", "updated_at"]:
                if field in data and isinstance(data[field], str):
                    data[field] = datetime.strptime(data[field], "%Y-%m-%d %H:%M:%S")
            
            return cls(**data)
            
        except Exception as e:
            logger.error(f"从字典创建用户失败: {str(e)}")
            raise
    
    def is_root_admin(self) -> bool:
        """是否为超级管理员"""
        return self.role == UserRole.ROOT_ADMIN
    
    def is_wecom_admin(self) -> bool:
        """是否为企业微信管理员"""
        return self.role == UserRole.WECOM_ADMIN
    
    def is_normal_user(self) -> bool:
        """是否为普通用户"""
        return self.role == UserRole.NORMAL
    
    def set_password(self, password: str):
        """设置密码
        
        Args:
            password: 原始密码
        """
        try:
            # 生成随机盐值
            self.salt = os.urandom(16).hex()
            
            # 使用PBKDF2进行密码哈希
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                self.salt.encode(),
                100000  # 迭代次数
            ).hex()
            
            self.password_hash = key
            logger.info(f"用户 {self.login_name} 密码设置成功")
            
        except Exception as e:
            logger.error(f"设置密码失败: {str(e)}")
            raise
    
    def verify_password(self, password: str) -> bool:
        """验证密码
        
        Args:
            password: 待验证的密码
            
        Returns:
            bool: 是否验证通过
        """
        try:
            # 如果是首次登录（密码未设置）
            if not self.password_hash or not self.salt:
                return True
            
            # 使用相同的盐值和哈希算法计算密码哈希
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                self.salt.encode(),
                100000  # 迭代次数
            ).hex()
            
            return key == self.password_hash
            
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
    
    def update_last_active_time(self):
        """更新最后活跃时间"""
        try:
            self.last_active_time = datetime.now()
        except Exception as e:
            logger.error(f"更新最后活跃时间失败: {str(e)}")
            raise 