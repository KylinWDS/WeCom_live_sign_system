from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import hashlib
import json
import os
import threading
from ..utils.logger import get_logger
from .database import DatabaseManager
from ..utils.security import (
    hash_password,
    verify_password,
    check_password_strength,
    verify_admin_token
)
from ..models.user import UserRole, User

logger = get_logger(__name__)

class AuthManager:
    """用户权限管理类"""
    
    # 添加线程本地存储用于保存当前用户
    _thread_local = threading.local()
    
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
            
    def create_corp_admin(self, username: str, password: str, corp_name: str, corp_id: str, corp_secret: str, agent_id: str) -> bool:
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
                    corpid=corp_id,
                    corpsecret=corp_secret,
                    agentid=agent_id,
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
            
    def verify_user(self, username: str, password: str, session=None) -> Optional[User]:
        """验证用户
        
        Args:
            username: 用户名
            password: 密码
            session: 可选的数据库会话
            
        Returns:
            Optional[User]: 验证通过的用户对象或None
        """
        try:
            # 确定是否需要关闭会话
            should_close_session = False
            
            # 如果没有提供会话，创建一个新的
            if not session:
                session = self.db.Session()
                should_close_session = True
            
            try:
                # 查询用户
                user = session.query(User).filter_by(login_name=username).first()
                
                # 如果用户不存在或未激活
                if not user or not user.is_active:
                    return None
                    
                # 验证密码
                if not user.verify_password(password):
                    return None
                
                # 更新用户最后活跃时间
                user.update_last_active_time()
                session.commit()
                    
                # 返回用户对象
                return user
                
            finally:
                # 如果我们创建了会话，确保关闭它
                if should_close_session:
                    session.close()
                    
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
            
    def has_permission(self, user_or_login: Union[str, int, User], permission: str, session=None) -> bool:
        """检查用户是否有权限
        
        Args:
            user_or_login: 用户对象、用户ID或登录名
            permission: 权限名称
            session: 可选的数据库会话
            
        Returns:
            bool: 是否有权限
        """
        try:
            # 确定是否需要关闭会话
            should_close_session = False
            
            # 如果没有提供会话，创建一个新的
            if not session:
                session = self.db.Session()
                should_close_session = True
            
            try:
                # 获取用户对象
                user = None
                if isinstance(user_or_login, str):
                    # 如果是字符串，假定为登录名
                    user = session.query(User).filter_by(login_name=user_or_login).first()
                elif isinstance(user_or_login, int):
                    # 如果是整数，假定为用户ID
                    user = session.query(User).get(user_or_login)
                elif hasattr(user_or_login, 'userid'):
                    # 如果是用户对象，确保与会话绑定
                    user = session.merge(user_or_login)
                
                if not user:
                    return False
                    
                # 超级管理员拥有所有权限
                if user.role == UserRole.ROOT_ADMIN.value:
                    return True
                    
                # 检查普通权限
                permissions = self.roles.get(user.role, {}).get("permissions", [])
                return "*" in permissions or permission in permissions
                
            finally:
                # 如果我们创建了会话，确保关闭它
                if should_close_session:
                    session.close()
                    
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
            
    def get_all_role_permissions(self, session) -> List[Dict]:
        """获取所有角色的权限信息
        
        Args:
            session: 数据库会话
        
        Returns:
            List[Dict]: 角色权限信息列表
        """
        try:
            result = []
            
            # 定义可用的权限列表
            all_permissions = [
                {"id": "manage_users", "name": "管理用户", "description": "创建、编辑和删除用户"},
                {"id": "manage_corps", "name": "管理企业", "description": "创建、编辑和删除企业信息"},
                {"id": "manage_settings", "name": "管理设置", "description": "修改系统配置和设置"},
                {"id": "manage_permissions", "name": "管理权限", "description": "分配和修改角色权限"},
                {"id": "view_lives", "name": "查看直播", "description": "查看直播列表和详情"},
                {"id": "create_live", "name": "创建直播", "description": "创建新的直播"},
                {"id": "edit_live", "name": "编辑直播", "description": "编辑现有直播信息"},
                {"id": "delete_live", "name": "删除直播", "description": "删除直播记录"},
                {"id": "view_signs", "name": "查看签到", "description": "查看签到记录"},
                {"id": "export_signs", "name": "导出签到", "description": "导出签到数据"},
                {"id": "view_stats", "name": "查看统计", "description": "查看数据统计和报表"},
                {"id": "export_data", "name": "导出数据", "description": "导出系统数据"},
                {"id": "view_system_monitor", "name": "查看系统监控", "description": "查看系统性能监控"}
            ]
            
            # 获取所有角色
            roles = self.get_all_roles()
            
            # 为每个角色构建权限信息
            for role in roles:
                role_perms = []
                role_id = role["id"]
                role_permissions = role["permissions"]
                
                # 特殊处理超级管理员，拥有所有权限
                if role_id == UserRole.ROOT_ADMIN.value:
                    for perm in all_permissions:
                        role_perms.append({
                            "id": perm["id"],
                            "name": perm["name"],
                            "description": perm["description"],
                            "allowed": True
                        })
                else:
                    # 处理其他角色
                    for perm in all_permissions:
                        # 检查权限是否在角色的权限列表中
                        allowed = perm["id"] in role_permissions or "*" in role_permissions
                        
                        role_perms.append({
                            "id": perm["id"],
                            "name": perm["name"],
                            "description": perm["description"],
                            "allowed": allowed
                        })
                
                # 添加到结果
                result.append({
                    "role_id": role_id,
                    "role_name": role["name"],
                    "permissions": role_perms
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取所有角色权限失败: {str(e)}")
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
            
            # 更新最后登录时间
            self.db.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE login_name = ?",
                (username,)
            )
            
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

    def get_current_user(self, session=None):
        """获取当前线程的用户
        
        Args:
            session: 可选的数据库会话，不再使用
            
        Returns:
            User: 用户对象或None
        """
        try:
            # 如果存储了完整用户对象，直接返回
            if hasattr(self._thread_local, 'user') and self._thread_local.user is not None:
                return self._thread_local.user
                
            # 如果只有用户ID，尝试从数据库获取
            elif hasattr(self._thread_local, 'user_id') and self._thread_local.user_id is not None:
                user_id = self._thread_local.user_id
                
                # 如果提供了会话，使用它
                if session:
                    user = session.query(User).get(user_id)
                # 否则创建新会话
                elif self.db:
                    with self.db.get_session() as new_session:
                        user = new_session.query(User).get(user_id)
                        # 如果找到用户，更新存储的用户对象
                        if user:
                            self._thread_local.user = user
                        return user
                else:
                    return None
            else:
                return None
        except Exception as e:
            logger.error(f"获取当前用户失败: {str(e)}")
            return None
    
    def clear_current_user(self):
        """清除当前线程的用户"""
        if hasattr(self._thread_local, 'user'):
            delattr(self._thread_local, 'user')
        if hasattr(self._thread_local, 'user_id'):
            delattr(self._thread_local, 'user_id')

    def update_role_permissions(self, role: str, permissions: list) -> bool:
        """更新角色权限
        
        Args:
            role: 角色
            permissions: 权限列表
            
        Returns:
            bool: 是否成功
        """
        try:
            # 不允许修改超级管理员的权限
            if role == UserRole.ROOT_ADMIN.value:
                logger.warning("不允许修改超级管理员的权限")
                return False
                
            # 更新内存中的角色权限
            if role in self.roles:
                self.roles[role]["permissions"] = permissions
                
                # 更新配置文件中的角色权限
                self.save_config()
                
                logger.info(f"更新角色 {role} 权限成功")
                return True
            else:
                logger.warning(f"未找到角色: {role}")
                return False
                
        except Exception as e:
            logger.error(f"更新角色权限失败: {str(e)}")
            return False
            
    def reset_role_permissions(self, role: str) -> bool:
        """重置角色权限到默认状态
        
        Args:
            role: 角色
            
        Returns:
            bool: 是否成功
        """
        try:
            # 不允许修改超级管理员的权限
            if role == UserRole.ROOT_ADMIN.value:
                logger.warning("不允许修改超级管理员的权限")
                return False
                
            # 重置为默认权限
            default_permissions = {
                UserRole.WECOM_ADMIN.value: [
                    "view_lives",
                    "create_live",
                    "edit_live",
                    "delete_live",
                    "view_signs", 
                    "export_signs",
                    "view_stats"
                ],
                UserRole.NORMAL.value: [
                    "view_lives",
                    "view_signs",
                    "view_stats"
                ]
            }
            
            if role in default_permissions:
                self.roles[role]["permissions"] = default_permissions[role]
                
                # 更新配置文件中的角色权限
                self.save_config()
                
                logger.info(f"重置角色 {role} 权限成功")
                return True
            else:
                logger.warning(f"未找到角色: {role}")
                return False
                
        except Exception as e:
            logger.error(f"重置角色权限失败: {str(e)}")
            return False
    
    def set_role_permission(self, role_id: str, permission_id: str, allowed: bool, session=None) -> bool:
        """设置角色的特定权限
        
        Args:
            role_id: 角色ID
            permission_id: 权限ID
            allowed: 是否允许
            session: 数据库会话（可选）
            
        Returns:
            bool: 是否设置成功
        """
        try:
            # 不允许修改超级管理员的权限
            if role_id == UserRole.ROOT_ADMIN.value:
                logger.warning("不允许修改超级管理员的权限")
                return False
                
            # 检查角色是否存在
            if role_id not in self.roles:
                logger.warning(f"未找到角色: {role_id}")
                return False
                
            # 获取当前权限列表
            current_permissions = self.roles[role_id]["permissions"]
            
            # 根据是否允许更新权限列表
            if allowed and permission_id not in current_permissions:
                current_permissions.append(permission_id)
            elif not allowed and permission_id in current_permissions:
                current_permissions.remove(permission_id)
                
            # 更新角色权限
            self.roles[role_id]["permissions"] = current_permissions
            
            # 保存配置
            self.save_config()
            
            logger.info(f"设置角色 {role_id} 的权限 {permission_id} 为 {allowed} 成功")
            return True
                
        except Exception as e:
            logger.error(f"设置角色权限失败: {str(e)}")
            return False
    
    def reset_permissions(self, session=None) -> bool:
        """重置所有角色权限到默认状态
        
        Args:
            session: 数据库会话（可选）
            
        Returns:
            bool: 是否成功
        """
        try:
            # 重置每个角色的权限
            for role_id in self.roles:
                if role_id != UserRole.ROOT_ADMIN.value:  # 不重置超级管理员
                    self.reset_role_permissions(role_id)
                    
            logger.info("所有角色权限已重置为默认值")
            return True
                
        except Exception as e:
            logger.error(f"重置所有权限失败: {str(e)}")
            return False

    # 添加用户上下文管理方法
    def set_current_user(self, user):
        """设置当前线程的用户
        
        Args:
            user: 用户对象或用户ID
        
        Returns:
            bool: 设置是否成功
        """
        try:
            if user is None:
                self._thread_local.user = None
                self._thread_local.user_id = None
                return True
                
            # 如果是用户对象
            if hasattr(user, 'userid'):
                # 存储完整的用户对象和ID
                self._thread_local.user = user
                self._thread_local.user_id = user.userid
                return True
            # 如果是用户ID，尝试从数据库获取用户对象
            else:
                with self.db.get_session() as session:
                    user_obj = session.query(User).get(user)
                    if user_obj:
                        self._thread_local.user = user_obj
                        self._thread_local.user_id = user
                        return True
                    else:
                        logger.warning(f"设置当前用户失败: 未找到ID为 {user} 的用户")
                        return False
        except Exception as e:
            logger.error(f"设置当前用户失败: {str(e)}")
            return False
    
    def get_current_user_id(self) -> Optional[int]:
        """获取当前线程的用户ID
        
        Returns:
            Optional[int]: 用户ID或None
        """
        try:
            # 如果存储了用户ID，直接返回
            if hasattr(self._thread_local, 'user_id') and self._thread_local.user_id is not None:
                return self._thread_local.user_id
                
            # 如果存储了完整用户对象，返回其ID
            elif hasattr(self._thread_local, 'user') and self._thread_local.user is not None:
                return self._thread_local.user.userid
                
            else:
                return None
        except Exception as e:
            logger.error(f"获取当前用户ID失败: {str(e)}")
            return None 