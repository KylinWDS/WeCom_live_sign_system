from typing import List, Dict, Any
from src.utils.logger import get_logger
from src.models.user import UserRole

logger = get_logger(__name__)

class PermissionManager:
    """权限管理器"""
    
    # 角色权限映射
    ROLE_PERMISSIONS: Dict[str, List[str]] = {
        UserRole.USER.value: [
            "view_lives",
            "view_signs",
            "view_stats"
        ],
        UserRole.ADMIN.value: [
            "view_lives",
            "create_live",
            "edit_live",
            "delete_live",
            "view_signs",
            "export_signs",
            "view_stats"
        ],
        UserRole.ROOT_ADMIN.value: [
            "view_lives",
            "create_live",
            "edit_live",
            "delete_live",
            "view_signs",
            "export_signs",
            "view_stats",
            "manage_users",
            "manage_roles",
            "manage_permissions"
        ]
    }
    
    # 角色名称映射
    ROLE_NAMES: Dict[str, str] = {
        UserRole.USER.value: "普通用户",
        UserRole.ADMIN.value: "管理员",
        UserRole.ROOT_ADMIN.value: "超级管理员"
    }
    
    def has_permission(self, permission: str, role: str) -> bool:
        """检查角色是否有指定权限
        
        Args:
            permission: 权限名称
            role: 角色
            
        Returns:
            bool: 是否有权限
        """
        try:
            if role == UserRole.ROOT_ADMIN.value:
                return True
            return permission in self.ROLE_PERMISSIONS.get(role, [])
        except Exception as e:
            logger.error(f"检查权限失败: {str(e)}")
            return False
    
    def get_role_permissions(self, role: str) -> List[str]:
        """获取角色的所有权限
        
        Args:
            role: 角色
            
        Returns:
            List[str]: 权限列表
        """
        try:
            return self.ROLE_PERMISSIONS.get(role, [])
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            return []
    
    def get_role_name(self, role: str) -> str:
        """获取角色名称
        
        Args:
            role: 角色
            
        Returns:
            str: 角色名称
        """
        try:
            return self.ROLE_NAMES.get(role, "未知角色")
        except Exception as e:
            logger.error(f"获取角色名称失败: {str(e)}")
            return "未知角色"
    
    def check_data_access(self, user_role: str, data_type: str) -> bool:
        """检查用户是否有数据访问权限
        
        Args:
            user_role: 用户角色
            data_type: 数据类型
            
        Returns:
            bool: 是否有权限
        """
        try:
            if user_role == UserRole.ROOT_ADMIN.value:
                return True
            elif user_role == UserRole.ADMIN.value:
                return data_type in ["lives", "signs", "stats"]
            else:  # USER
                return data_type in ["lives", "signs", "stats"]
        except Exception as e:
            logger.error(f"检查数据访问权限失败: {str(e)}")
            return False
    
    def check_operation_permission(self, user_role: str, operation: str) -> bool:
        """检查用户是否有操作权限
        
        Args:
            user_role: 用户角色
            operation: 操作类型
            
        Returns:
            bool: 是否有权限
        """
        try:
            if user_role == UserRole.ROOT_ADMIN.value:
                return True
            elif user_role == UserRole.ADMIN.value:
                return operation in [
                    "view",
                    "create",
                    "edit",
                    "delete",
                    "export"
                ]
            else:  # USER
                return operation == "view"
        except Exception as e:
            logger.error(f"检查操作权限失败: {str(e)}")
            return False 