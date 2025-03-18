from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import hashlib
import json
import os
from utils.logger import get_logger
from src.core.database import DatabaseManager
from src.utils.security import (
    hash_password,
    verify_password,
    check_password_strength,
    verify_admin_token
)
from src.models.user import UserRole, User

logger = get_logger(__name__)

class AuthManager:
    """用户权限管理类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.users = {}
        self.roles = {
            UserRole.ROOT_ADMIN.value: {
                "name": "超级管理员",
                "permissions": ["*"]  # 所有权限
            },
            UserRole.WECOM_ADMIN.value: {
                "name": "企业微信管理员",
                "permissions": [
                    "manage_live",
                    "view_live",
                    "manage_users",
                    "view_stats"
                ]
            },
            UserRole.NORMAL.value: {
                "name": "普通用户",
                "permissions": [
                    "view_live",
                    "view_stats"
                ]
            }
        }
        
    def create_root_admin(self, username: str, password: str) -> bool:
        """设置超级管理员密码
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("开始设置超级管理员密码...")
            
            # 验证用户名
            if username != "root-admin":
                logger.error("超级管理员用户名必须为 root-admin")
                return False
                
            # 生成密码哈希和盐值
            salt = os.urandom(16).hex()  # 生成32位的十六进制盐值
            password_hash = self.hash_password(password, salt)
            
            # 更新数据库中的root-admin用户
            with self.db.get_session() as session:
                user = session.query(User).filter_by(login_name=username).first()
                if not user:
                    logger.error("未找到root-admin用户，请先初始化数据库")
                    return False
                    
                # 更新密码和盐值
                user.password_hash = password_hash
                user.salt = salt
                user.updated_at = datetime.now()
                
                session.commit()
                logger.info("超级管理员密码设置成功")
                return True
                
        except Exception as e:
            logger.error(f"设置超级管理员密码失败: {str(e)}")
            return False
            
    def create_corp_admin(self, username: str, password: str, corp_name: str) -> bool:
        """创建企业管理员账号
        
        Args:
            username: 用户名
            password: 密码
            corp_name: 企业名称
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info(f"开始创建企业管理员账号: {username}...")
            
            # 生成密码哈希和盐值
            salt = os.urandom(16).hex()
            password_hash = self.hash_password(password, salt)
            
            # 创建企业管理员用户
            with self.db.get_session() as session:
                # 检查用户名是否已存在
                if session.query(User).filter_by(login_name=username).first():
                    logger.error(f"用户名已存在: {username}")
                    return False
                
                # 创建用户
                user = User(
                    login_name=username,
                    name=f"{corp_name}管理员",
                    role=UserRole.WECOM_ADMIN.value,
                    corpname=corp_name,
                    password_hash=password_hash,
                    salt=salt,
                    is_active=True,
                    is_admin=True  # 设置为管理员
                )
                session.add(user)
                session.commit()
                
                logger.info(f"企业管理员账号创建成功: {username}")
                return True
                
        except Exception as e:
            logger.error(f"创建企业管理员账号失败: {str(e)}")
            return False
            
    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            Optional[Dict[str, Any]]: 用户信息
        """
        try:
            # 获取用户信息
            user = self.db.query_one(
                "SELECT password_hash, salt, role, is_active FROM users WHERE userid = ?",
                (username,)
            )
            if not user:
                return None
                
            # 验证密码
            if not verify_password(password, user[0], user[1]):
                return None
                
            # 检查用户状态
            if not user[3]:
                return None
                
            return {
                "userid": username,
                "role": user[2],
                "is_active": user[3]
            }
            
        except Exception as e:
            logger.error(f"验证用户失败: {str(e)}")
            return None
            
    def get_user_role(self, username: str) -> Optional[str]:
        """获取用户角色
        
        Args:
            username: 用户名
            
        Returns:
            Optional[str]: 角色名称
        """
        try:
            user = self.users.get(username)
            if not user:
                return None
                
            return user["role"]
            
        except Exception as e:
            logger.error(f"获取用户角色失败: {str(e)}")
            return None
            
    def get_role_permissions(self, role: str) -> List[str]:
        """获取角色权限
        
        Args:
            role: 角色名称
            
        Returns:
            List[str]: 权限列表
        """
        try:
            role_info = self.roles.get(role)
            if not role_info:
                return []
                
            return role_info["permissions"]
            
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            return []
            
    def has_permission(self, username: str, permission: str) -> bool:
        """检查用户是否有权限
        
        Args:
            username: 用户名
            permission: 权限名称
            
        Returns:
            bool: 是否有权限
        """
        try:
            role = self.get_user_role(username)
            if not role:
                return False
                
            permissions = self.get_role_permissions(role)
            return "*" in permissions or permission in permissions
            
        except Exception as e:
            logger.error(f"检查用户权限失败: {str(e)}")
            return False
            
    def load_config(self):
        """加载配置"""
        try:
            # 创建配置目录
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                
            # 加载用户配置
            if os.path.exists(self.users_file):
                with open(self.users_file, "r", encoding="utf-8") as f:
                    self.users = json.load(f)
            else:
                self.users = {}
                
            # 加载角色配置
            if os.path.exists(self.roles_file):
                with open(self.roles_file, "r", encoding="utf-8") as f:
                    self.roles = json.load(f)
            else:
                # 创建默认角色
                self.roles = {
                    UserRole.ROOT_ADMIN.value: {
                        "name": "超级管理员",
                        "permissions": ["*"]  # 所有权限
                    },
                    UserRole.WECOM_ADMIN.value: {
                        "name": "企业微信管理员",
                        "permissions": [
                            "manage_live",
                            "view_live",
                            "manage_users",
                            "view_stats"
                        ]
                    },
                    UserRole.NORMAL.value: {
                        "name": "普通用户",
                        "permissions": [
                            "view_live",
                            "view_stats"
                        ]
                    }
                }
                
            # 保存配置
            self.save_config()
                
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            raise
            
    def save_config(self):
        """保存配置"""
        try:
            # 保存用户配置
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
                
            # 保存角色配置
            with open(self.roles_file, "w", encoding="utf-8") as f:
                json.dump(self.roles, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            raise
            
    def hash_password(self, password: str, salt: str) -> str:
        """密码哈希
        
        Args:
            password: 原始密码
            salt: 盐值
            
        Returns:
            哈希后的密码
        """
        try:
            # 使用pbkdf2_hmac算法进行密码哈希
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                100000  # 迭代次数
            ).hex()
            return key
        except Exception as e:
            logger.error(f"密码哈希失败: {str(e)}")
            return ""
        
    def add_user(self, username: str, password: str, role: str) -> bool:
        """添加用户
        
        Args:
            username: 用户名
            password: 密码
            role: 角色
            
        Returns:
            是否成功
        """
        try:
            # 检查用户是否已存在
            if username in self.users:
                return False
                
            # 检查角色是否存在
            if role not in self.roles:
                return False
                
            # 添加用户
            self.users[username] = {
                "password": self.hash_password(password, self.generate_salt()),
                "role": role,
                "created_at": datetime.now().isoformat()
            }
            
            # 保存配置
            self.save_config()
            return True
            
        except Exception as e:
            logger.error(f"添加用户失败: {str(e)}")
            return False
            
    def update_user(self, username: str, password: Optional[str] = None, role: Optional[str] = None) -> bool:
        """更新用户
        
        Args:
            username: 用户名
            password: 新密码(可选)
            role: 新角色(可选)
            
        Returns:
            是否成功
        """
        try:
            # 检查用户是否存在
            if username not in self.users:
                return False
                
            # 更新密码
            if password:
                self.users[username]["password"] = self.hash_password(password, self.generate_salt())
                
            # 更新角色
            if role:
                # 检查角色是否存在
                if role not in self.roles:
                    return False
                self.users[username]["role"] = role
                
            # 保存配置
            self.save_config()
            return True
            
        except Exception as e:
            logger.error(f"更新用户失败: {str(e)}")
            return False
            
    def delete_user(self, username: str) -> bool:
        """删除用户
        
        Args:
            username: 用户名
            
        Returns:
            是否成功
        """
        try:
            # 检查用户是否存在
            if username not in self.users:
                return False
                
            # 删除用户
            del self.users[username]
            
            # 保存配置
            self.save_config()
            return True
            
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return False
            
    def get_all_users(self) -> List[Dict]:
        """获取所有用户
        
        Returns:
            用户列表
        """
        try:
            users = []
            for username, info in self.users.items():
                users.append({
                    "username": username,
                    "role": info["role"],
                    "created_at": info["created_at"]
                })
            return users
            
        except Exception as e:
            logger.error(f"获取所有用户失败: {str(e)}")
            return []
            
    def get_all_roles(self) -> List[Dict]:
        """获取所有角色
        
        Returns:
            角色列表
        """
        try:
            roles = []
            for role_id, info in self.roles.items():
                roles.append({
                    "id": role_id,
                    "name": info["name"],
                    "permissions": info["permissions"]
                })
            return roles
            
        except Exception as e:
            logger.error(f"获取所有角色失败: {str(e)}")
            return []
            
    def reset_password(self, username: str) -> bool:
        """重置用户密码为默认密码
        
        Args:
            username: 用户名
            
        Returns:
            是否成功
        """
        try:
            # 生成新密码和盐值
            new_password = "123456"
            hashed, salt = hash_password(new_password)
            
            # 更新数据库
            success = self.db.execute(
                """
                UPDATE users 
                SET password = ?, salt = ?, 
                    password_changed = 0,
                    last_password_change = CURRENT_TIMESTAMP
                WHERE username = ?
                """,
                (hashed, salt, username)
            )
            
            if success:
                logger.info(f"用户 {username} 密码重置成功")
                return True
            else:
                logger.error(f"用户 {username} 密码重置失败")
                return False
                
        except Exception as e:
            logger.error(f"重置密码失败: {str(e)}")
            return False
            
    def change_password(
        self,
        username: str,
        old_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """修改用户密码
        
        Args:
            username: 用户名
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            # 验证旧密码
            user = self.db.query_one(
                "SELECT password_hash, salt FROM users WHERE name = ?",
                (username,)
            )
            
            if not user or not verify_password(old_password, user[0], user[1]):
                return False, "旧密码错误"
                
            # 检查新密码强度
            is_valid, error_msg = check_password_strength(new_password)
            if not is_valid:
                return False, error_msg
                
            # 生成新密码和盐值
            hashed, salt = hash_password(new_password)
            
            # 更新数据库
            success = self.db.execute(
                """
                UPDATE users 
                SET password = ?, salt = ?,
                    password_changed = 1,
                    last_password_change = CURRENT_TIMESTAMP
                WHERE name = ?
                """,
                (hashed, salt, username)
            )
            
            if success:
                logger.info(f"用户 {username} 密码修改成功")
                return True, ""
            else:
                error_msg = f"用户 {username} 密码修改失败"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"修改密码失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    def reset_admin_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """重置超级管理员密码
        
        Args:
            token: 管理员令牌
            new_password: 新密码
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            # 验证令牌
            is_valid, error_msg = verify_admin_token(token)
            if not is_valid:
                return False, error_msg
                
            # 检查新密码强度
            is_valid, error_msg = check_password_strength(new_password)
            if not is_valid:
                return False, error_msg
                
            # 重置密码
            success = self.reset_password("root-admin")
            if not success:
                return False, "重置密码失败"
                
            # 设置新密码
            success, error_msg = self.change_password(
                "root-admin",
                "123456",  # 默认密码
                new_password
            )
            
            return success, error_msg
            
        except Exception as e:
            error_msg = f"重置管理员密码失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

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
            user = self.db.query_one(
                "SELECT password_hash, salt, role, corpname FROM users WHERE login_name = ?",
                (username,)
            )
            if not user:
                return False, "用户不存在"
                
            # 验证密码
            if not verify_password(password, user[0], user[1]):
                return False, "密码错误"
                
            # 检查用户状态
            if not self.db.query_one(
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
            
    def set_admin_password(self, username: str, new_password: str) -> Tuple[bool, str]:
        """设置管理员密码
        
        Args:
            username: 用户名
            new_password: 新密码
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 检查密码强度
            if not check_password_strength(new_password):
                return False, "密码强度不足"
                
            # 获取用户信息
            user = self.db.query_one(
                "SELECT password_hash, salt FROM users WHERE login_name = ?",
                (username,)
            )
            if not user:
                return False, "用户不存在"
                
            # 更新密码
            hashed_password = self.hash_password(new_password, user[1])
            self.db.execute(
                """
                UPDATE users 
                SET password = ?, salt = ?,
                    password_changed = 1,
                    last_password_change = CURRENT_TIMESTAMP
                WHERE name = ?
                """,
                (hashed_password, user[1], username)
            )
            
            logger.info(f"用户 {username} 密码修改成功")
            return True, "密码修改成功"
            
        except Exception as e:
            logger.error(f"设置管理员密码失败: {str(e)}")
            return False, "密码修改失败"
            
    def verify_token(self, token: str) -> Tuple[bool, str]:
        """验证管理员令牌
        
        Args:
            token: 管理员令牌
            
        Returns:
            Tuple[bool, str]: (是否有效, 消息)
        """
        try:
            # TODO: 实现令牌验证逻辑
            return True, "令牌有效"
        except Exception as e:
            logger.error(f"验证管理员令牌失败: {str(e)}")
            return False, "令牌验证失败"

    def set_root_admin_password(self, password: str) -> bool:
        """设置超级管理员密码
        
        Args:
            password: 密码
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("开始设置超级管理员密码...")
            
            # 生成密码哈希和盐值
            salt = os.urandom(16).hex()  # 生成32位的十六进制盐值
            password_hash = self.hash_password(password, salt)
            
            # 更新数据库中的root-admin用户
            with self.db.get_session() as session:
                user = session.query(User).filter_by(login_name="root-admin").first()
                if not user:
                    logger.error("未找到root-admin用户，请先初始化数据库")
                    return False
                    
                # 更新密码和盐值
                user.password_hash = password_hash
                user.salt = salt
                user.is_admin = True  # 确保是管理员
                user.updated_at = datetime.now()
                
                session.commit()
                logger.info("超级管理员密码设置成功")
                return True
                
        except Exception as e:
            logger.error(f"设置超级管理员密码失败: {str(e)}")
            return False 