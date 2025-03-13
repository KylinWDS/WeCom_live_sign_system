from typing import Optional, List
from src.utils.logger import get_logger

logger = get_logger(__name__)

class Department:
    """部门模型"""
    
    def __init__(self, **kwargs):
        """初始化部门"""
        self.id = kwargs.get("id")
        self.dept_id = kwargs.get("dept_id")
        self.name = kwargs.get("name")
        self.parent_id = kwargs.get("parent_id")
        self.order_num = kwargs.get("order_num", 0)
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "dept_id": self.dept_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "order_num": self.order_num,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Department":
        """从字典创建部门"""
        return cls(**data)
    
    def is_root(self) -> bool:
        """检查是否是根部门"""
        return not self.parent_id
    
    def get_path(self, departments: List["Department"]) -> str:
        """获取部门路径"""
        try:
            path = [self.name]
            current = self
            
            while current.parent_id:
                parent = next(
                    (d for d in departments if d.dept_id == current.parent_id),
                    None
                )
                if not parent:
                    break
                path.insert(0, parent.name)
                current = parent
            
            return " / ".join(path)
            
        except Exception as e:
            logger.error(f"获取部门路径失败: {str(e)}")
            return self.name
    
    def get_children(self, departments: List["Department"]) -> List["Department"]:
        """获取子部门"""
        try:
            return [
                d for d in departments
                if d.parent_id == self.dept_id
            ]
            
        except Exception as e:
            logger.error(f"获取子部门失败: {str(e)}")
            return []
    
    def get_all_children(self, departments: List["Department"]) -> List["Department"]:
        """获取所有子部门（包括子部门的子部门）"""
        try:
            children = self.get_children(departments)
            all_children = []
            
            for child in children:
                all_children.append(child)
                all_children.extend(child.get_all_children(departments))
            
            return all_children
            
        except Exception as e:
            logger.error(f"获取所有子部门失败: {str(e)}")
            return []
    
    def get_parent(self, departments: List["Department"]) -> Optional["Department"]:
        """获取父部门"""
        try:
            if not self.parent_id:
                return None
            return next(
                (d for d in departments if d.dept_id == self.parent_id),
                None
            )
            
        except Exception as e:
            logger.error(f"获取父部门失败: {str(e)}")
            return None 