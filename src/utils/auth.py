import hashlib
import os
from typing import Optional, Dict, Any, Tuple
from src.utils.logger import get_logger
from src.core.database import DatabaseManager
from src.models.user import User, UserRole

logger = get_logger(__name__)

class AuthManager:
    """认证管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """初始化认证管理器
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
    
    def generate_salt(self) -> str:
        """生成盐值"""
        return os.urandom(16).hex()
    
    def hash_password(self, password: str, salt: str) -> str:
        """哈希密码"""
        try:
            # 确保参数都是字符串
            password_str = str(password) if password is not None else ""
            salt_str = str(salt) if salt is not None else ""
            
            # 如果任一参数为空，返回空字符串
            if not password_str or not salt_str:
                return ""
                
            # 计算哈希值
            combined = (password_str + salt_str).encode('utf-8')
            return hashlib.sha256(combined).hexdigest()
            
        except Exception as e:
            logger.error(f"密码哈希失败: {str(e)}")
            return ""
    
    def verify_password(self, password: str, salt: str, hashed: str) -> bool:
        """验证密码"""
        try:
            # 如果是首次登录（密码未设置）
            if not password or not salt or not hashed:
                return True
                
            # 确保所有参数都是字符串
            password_str = str(password) if password else ""
            salt_str = str(salt) if salt else ""
            hashed_str = str(hashed) if hashed else ""
            
            # 计算哈希值并比较
            current_hash = self.hash_password(password_str, salt_str)
            return current_hash == hashed_str
            
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False
    
    def create_user(self, username: str, password: str, role: UserRole, 
                   corpname: Optional[str] = None, userid: Optional[str] = None) -> Optional[User]:
        """创建用户"""
        session = self.db_manager.get_session()
        try:
            # 检查用户名是否已存在
            if session.query(User).filter_by(username=username).first():
                logger.warning(f"用户名 {username} 已存在")
                return None
            
            # 生成盐值和哈希密码
            salt = self.generate_salt()
            hashed = self.hash_password(password, salt)
            
            # 创建用户
            user = User(
                username=username,
                password=hashed,
                role=role,
                corpname=corpname,
                userid=userid,
                is_active=True
            )
            
            session.add(user)
            session.commit()
            
            logger.info(f"用户 {username} 创建成功")
            return user
            
        except Exception as e:
            session.rollback()
            logger.error(f"创建用户失败: {str(e)}")
            return None
        finally:
            session.close()
    
    def login(self, username: str, password: str, corpname: str = None) -> Tuple[bool, str]:
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            corpname: 企业名称（可选）
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 获取用户信息
            user = self.db_manager.query_one(
                "SELECT password_hash, salt, role, corpname FROM users WHERE login_name = ?",
                (username,)
            )
            if not user:
                return False, "用户不存在"
                
            # 验证密码
            if not self.verify_password(password, user[1], user[0]):
                return False, "密码错误"
                
            # 检查用户状态
            if not self.db_manager.query_one(
                "SELECT is_active FROM users WHERE login_name = ?",
                (username,)
            )[0]:
                return False, "用户已被禁用"
                
            # 验证用户和企业的关联
            if corpname:
                # 超级管理员不需要验证企业关联
                if user[2] != UserRole.ROOT_ADMIN.value:
                    if not user[3] or user[3] != corpname:
                        return False, "该用户不属于所选企业"
            
            logger.info(f"用户 {username} 登录成功")
            return True, "登录成功"
            
        except Exception as e:
            logger.error(f"用户登录失败: {str(e)}")
            return False, "登录失败"
    
    def register(self, username: str, password: str, role: str = UserRole.NORMAL.value) -> bool:
        """用户注册"""
        try:
            # 检查用户是否已存在
            if self.db_manager.get_user(username):
                logger.warning(f"用户已存在: {username}")
                return False
            
            # 生成盐值和哈希密码
            salt = self.generate_salt()
            hashed = self.hash_password(password, salt)
            
            # 创建用户
            if self.db_manager.create_user(username, hashed, salt, role):
                logger.info(f"用户注册成功: {username}")
                return True
            else:
                logger.error(f"用户注册失败: {username}")
                return False
            
        except Exception as e:
            logger.error(f"用户注册失败: {str(e)}")
            return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            # 获取用户信息
            user = self.db_manager.get_user(username)
            if not user:
                logger.warning(f"用户不存在: {username}")
                return False
            
            # 验证旧密码
            if not self.verify_password(old_password, user["salt"], user["password"]):
                logger.warning(f"旧密码错误: {username}")
                return False
            
            # 生成新的盐值和哈希密码
            salt = self.generate_salt()
            hashed = self.hash_password(new_password, salt)
            
            # 更新密码
            if self.db_manager.update_user(username, password=hashed, salt=salt):
                logger.info(f"密码修改成功: {username}")
                return True
            else:
                logger.error(f"密码修改失败: {username}")
                return False
            
        except Exception as e:
            logger.error(f"密码修改失败: {str(e)}")
            return False
    
    def reset_password(self, username: str) -> bool:
        """重置密码"""
        try:
            # 获取用户信息
            user = self.db_manager.get_user(username)
            if not user:
                logger.warning(f"用户不存在: {username}")
                return False
            
            # 生成新的盐值和哈希密码
            salt = self.generate_salt()
            hashed = self.hash_password("123456", salt)  # 默认密码
            
            # 更新密码
            if self.db_manager.update_user(username, password=hashed, salt=salt):
                logger.info(f"密码重置成功: {username}")
                return True
            else:
                logger.error(f"密码重置失败: {username}")
                return False
            
        except Exception as e:
            logger.error(f"密码重置失败: {str(e)}")
            return False 