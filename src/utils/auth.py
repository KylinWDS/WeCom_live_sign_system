import hashlib
import os
from typing import Optional, Dict, Any
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
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def verify_password(self, password: str, salt: str, hashed: str) -> bool:
        """验证密码"""
        return self.hash_password(password, salt) == hashed
    
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
    
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户登录"""
        try:
            # 获取用户信息
            user = self.db_manager.get_user(username)
            if not user:
                logger.warning(f"用户不存在: {username}")
                return None
            
            # 特殊处理root-admin用户
            if user["userid"] == "root-admin":
                # 如果是首次登录（密码为空）
                if not user["password"]:
                    if not password:
                        logger.info("root-admin用户首次登录，需要设置密码")
                        return {"user": user, "need_set_password": True}
                    else:
                        # 设置新密码
                        salt = self.generate_salt()
                        hashed = self.hash_password(password, salt)
                        self.db_manager.update_user(
                            username,
                            password=hashed,
                            salt=salt
                        )
                        logger.info("root-admin用户密码设置成功")
                        return {"user": user, "need_set_password": False}
                else:
                    # 验证密码
                    if not self.verify_password(password, user["salt"], user["password"]):
                        logger.warning("root-admin用户密码错误")
                        return None
            
            # 普通用户登录验证
            if not self.verify_password(password, user["salt"], user["password"]):
                logger.warning(f"密码错误: {username}")
                return None
            
            # 检查用户状态
            if not user["is_active"]:
                logger.warning(f"用户已禁用: {username}")
                return None
            
            # 更新最后登录时间
            self.db_manager.update_user(username, last_login="datetime('now')")
            
            logger.info(f"用户登录成功: {username}")
            return {"user": user, "need_set_password": False}
            
        except Exception as e:
            logger.error(f"用户登录失败: {str(e)}")
            return None
    
    def register(self, username: str, password: str, role: str = "USER") -> bool:
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