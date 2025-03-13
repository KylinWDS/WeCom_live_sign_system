from datetime import datetime
from typing import Optional

class Sign:
    """签到模型"""
    
    def __init__(
        self,
        id: int,
        user_id: int,
        live_id: int,
        sign_time: str,
        status: str,
        created_at: str
    ):
        self.id = id
        self.user_id = user_id
        self.live_id = live_id
        self.sign_time = sign_time
        self.status = status
        self.created_at = created_at
    
    def is_valid(self) -> bool:
        """检查签到是否有效
        
        Returns:
            bool: 是否有效
        """
        return self.status == "valid"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "live_id": self.live_id,
            "sign_time": self.sign_time,
            "status": self.status,
            "created_at": self.created_at
        } 