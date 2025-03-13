from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LiveStatus:
    """直播状态"""
    RESERVED = 0  # 预约中
    LIVING = 1    # 直播中
    ENDED = 2     # 已结束
    EXPIRED = 3   # 已过期
    CANCELLED = 4 # 已取消
    
    @classmethod
    def get_all_statuses(cls) -> List[int]:
        """获取所有状态"""
        return [cls.RESERVED, cls.LIVING, cls.ENDED, cls.EXPIRED, cls.CANCELLED]
    
    @classmethod
    def is_valid_status(cls, status: int) -> bool:
        """检查状态是否有效"""
        return status in cls.get_all_statuses()

class LiveType:
    """直播类型"""
    GENERAL = 0   # 通用直播
    SMALL = 1     # 小班课
    LARGE = 2     # 大班课
    TRAINING = 3  # 企业培训
    EVENT = 4     # 活动直播
    
    @classmethod
    def get_all_types(cls) -> List[int]:
        """获取所有类型"""
        return [cls.GENERAL, cls.SMALL, cls.LARGE, cls.TRAINING, cls.EVENT]
    
    @classmethod
    def is_valid_type(cls, type_id: int) -> bool:
        """检查类型是否有效"""
        return type_id in cls.get_all_types()

class Live:
    """直播模型"""
    
    def __init__(self, **kwargs):
        """初始化直播"""
        self.id = kwargs.get("id")
        self.livingid = kwargs.get("livingid")
        self.theme = kwargs.get("theme")
        self.living_start = kwargs.get("living_start")
        self.living_duration = kwargs.get("living_duration")
        self.anchor_userid = kwargs.get("anchor_userid")
        self.description = kwargs.get("description")
        self.type = kwargs.get("type", LiveType.GENERAL)
        self.status = kwargs.get("status", LiveStatus.RESERVED)
        self.corpname = kwargs.get("corpname")
        self.agentid = kwargs.get("agentid")
        self.viewer_num = kwargs.get("viewer_num", 0)
        self.comment_num = kwargs.get("comment_num", 0)
        self.mic_num = kwargs.get("mic_num", 0)
        self.online_count = kwargs.get("online_count", 0)
        self.subscribe_count = kwargs.get("subscribe_count", 0)
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "livingid": self.livingid,
            "theme": self.theme,
            "living_start": self.living_start,
            "living_duration": self.living_duration,
            "anchor_userid": self.anchor_userid,
            "description": self.description,
            "type": self.type,
            "status": self.status,
            "corpname": self.corpname,
            "agentid": self.agentid,
            "viewer_num": self.viewer_num,
            "comment_num": self.comment_num,
            "mic_num": self.mic_num,
            "online_count": self.online_count,
            "subscribe_count": self.subscribe_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Live":
        """从字典创建直播"""
        return cls(**data)
    
    def is_active(self) -> bool:
        """检查直播是否正在进行中"""
        try:
            if not self.living_start or not self.living_duration:
                return False
                
            now = datetime.now()
            start_time = datetime.fromtimestamp(self.living_start)
            end_time = start_time + timedelta(seconds=self.living_duration)
            
            return start_time <= now <= end_time
            
        except Exception as e:
            logger.error(f"检查直播状态失败: {str(e)}")
            return False
    
    def is_ended(self) -> bool:
        """检查直播是否已结束"""
        try:
            if not self.living_start or not self.living_duration:
                return False
                
            now = datetime.now()
            start_time = datetime.fromtimestamp(self.living_start)
            end_time = start_time + timedelta(seconds=self.living_duration)
            
            return now > end_time
            
        except Exception as e:
            logger.error(f"检查直播状态失败: {str(e)}")
            return False
    
    def get_duration(self) -> int:
        """获取直播时长（分钟）"""
        try:
            if not self.living_duration:
                return 0
            return self.living_duration // 60
            
        except Exception as e:
            logger.error(f"获取直播时长失败: {str(e)}")
 