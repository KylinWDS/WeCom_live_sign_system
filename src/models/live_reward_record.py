from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Enum
from sqlalchemy.orm import relationship, Session
from .base import BaseModel
import enum


class RewardRuleType(enum.Enum):
    """红包奖励规则类型"""
    SIGN = "sign"                  # 仅签到次数
    WATCH = "watch"                # 仅观看时长
    COUNT = "count"                # 仅观看场次
    SIGN_WATCH = "sign-watch"      # 签到次数和观看时长
    SIGN_COUNT = "sign-count"      # 签到次数和观看场次
    WATCH_COUNT = "watch-count"    # 观看时长和观看场次
    ALL_OR = "all-or"              # 所有条件满足其一即可
    ALL_AND = "all-and"            # 所有条件必须全满足


class LiveRewardRecord(BaseModel):
    """直播红包奖励记录模型
    
    用于记录用户的红包奖励详情，关联直播和观众
    """
    __tablename__ = "live_reward_records"
    
    # 关联字段
    living_id = Column(Integer, ForeignKey("livings.id"), nullable=False, index=True, comment="关联的直播ID")
    live_viewer_id = Column(Integer, ForeignKey("live_viewers.id"), nullable=False, index=True, comment="关联的观众ID")
    
    # 奖励规则
    rule_sign_count = Column(Integer, nullable=True, default=0, comment="奖励规则：单场最少签到次数")
    rule_watch_time = Column(Integer, nullable=True, default=0, comment="奖励规则：单场最少观看时长(秒)")
    rule_watch_count = Column(Integer, nullable=True, default=0, comment="奖励规则：合计最少观看场次")
    rule_type = Column(Enum(RewardRuleType), nullable=False, default=RewardRuleType.ALL_AND, comment="奖励规则方式")
    
    # 计算批次
    calculate_batch = Column(String(100), nullable=True, index=True, comment="计算批次标识")
    
    # 奖励信息
    reward_amount = Column(Float, default=0.0, comment="红包奖励金额")
    is_reward_eligible = Column(Boolean, default=False, comment="是否符合奖励条件")
    
    # 关联关系
    living = relationship("Living", back_populates="reward_records")
    viewer = relationship("LiveViewer", back_populates="reward_records")
    
    def __init__(
        self,
        living_id: int,
        live_viewer_id: int,
        rule_type: RewardRuleType = RewardRuleType.ALL_AND,
        rule_sign_count: Optional[int] = 0,
        rule_watch_time: Optional[int] = 0,
        rule_watch_count: Optional[int] = 0,
        reward_amount: float = 0.0,
        is_reward_eligible: bool = False,
        calculate_batch: Optional[str] = None
    ):
        self.living_id = living_id
        self.live_viewer_id = live_viewer_id
        self.rule_type = rule_type
        self.rule_sign_count = rule_sign_count
        self.rule_watch_time = rule_watch_time
        self.rule_watch_count = rule_watch_count
        self.reward_amount = reward_amount
        self.is_reward_eligible = is_reward_eligible
        self.calculate_batch = calculate_batch
    
    @staticmethod
    def generate_batch_id(user_id: str, rule_type: RewardRuleType) -> str:
        """生成计算批次ID
        
        Args:
            user_id: 当前登录用户ID
            rule_type: 规则类型
            
        Returns:
            str: 批次ID格式：yyyyMMddHHmmss-用户id-rule_type
        """
        now = datetime.now()
        time_str = now.strftime("%Y%m%d%H%M%S")
        return f"{time_str}-{user_id}-{rule_type.value}"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "living_id": self.living_id,
            "live_viewer_id": self.live_viewer_id,
            "rule_sign_count": self.rule_sign_count,
            "rule_watch_time": self.rule_watch_time,
            "rule_watch_count": self.rule_watch_count,
            "rule_type": self.rule_type.value if self.rule_type else None,
            "calculate_batch": self.calculate_batch,
            "reward_amount": self.reward_amount,
            "is_reward_eligible": self.is_reward_eligible,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LiveRewardRecord':
        """从字典创建实例"""
        # 处理枚举类型
        if 'rule_type' in data and isinstance(data['rule_type'], str):
            try:
                data['rule_type'] = RewardRuleType(data['rule_type'])
            except ValueError:
                data['rule_type'] = RewardRuleType.ALL_AND  # 默认值
        
        return cls(**data)
    
    def check_eligibility(self, db_session: Session, current_batch: str, batch_living_ids: List[int]) -> bool:
        """检查是否符合奖励条件
        
        Args:
            db_session: 数据库会话
            current_batch: 当前计算批次
            batch_living_ids: 当前批次包含的所有直播ID列表
            
        Returns:
            bool: 是否符合奖励条件
        """
        from .live_sign_record import LiveSignRecord
        from .live_viewer import LiveViewer
        
        # 获取当前观众信息
        viewer = db_session.query(LiveViewer).filter(LiveViewer.id == self.live_viewer_id).first()
        if not viewer:
            return False
        
        # 获取观众的userid
        viewer_userid = viewer.userid
        
        # 获取该直播的签到记录数
        sign_count = db_session.query(LiveSignRecord).filter(
            LiveSignRecord.viewer_id == self.live_viewer_id,
            LiveSignRecord.living_id == self.living_id
        ).count()
        
        # 获取观看时长
        watch_time = viewer.watch_time if viewer else 0
        
        # 计算该观众在当前批次指定的直播范围内观看的次数
        watch_count = db_session.query(LiveViewer).filter(
            LiveViewer.userid == viewer_userid,
            LiveViewer.living_id.in_(batch_living_ids)
        ).count()
        
        # 更新计算批次
        self.calculate_batch = current_batch
        
        # 根据不同规则类型判断
        if self.rule_type == RewardRuleType.SIGN:
            # 当前直播的签到次数
            return sign_count >= self.rule_sign_count
        
        elif self.rule_type == RewardRuleType.WATCH:
            # 当前直播的观看时长
            return watch_time >= self.rule_watch_time
        
        elif self.rule_type == RewardRuleType.COUNT:
            # 当前批次中观看的直播次数
            return watch_count >= self.rule_watch_count
        
        elif self.rule_type == RewardRuleType.SIGN_WATCH:
            # 签到次数和观看时长
            return sign_count >= self.rule_sign_count and watch_time >= self.rule_watch_time
        
        elif self.rule_type == RewardRuleType.SIGN_COUNT:
            # 签到次数和观看场次
            return sign_count >= self.rule_sign_count and watch_count >= self.rule_watch_count
        
        elif self.rule_type == RewardRuleType.WATCH_COUNT:
            # 观看时长和观看场次
            return watch_time >= self.rule_watch_time and watch_count >= self.rule_watch_count
        
        elif self.rule_type == RewardRuleType.ALL_OR:
            # 任意条件满足即可
            return (
                sign_count >= self.rule_sign_count or 
                watch_time >= self.rule_watch_time or 
                watch_count >= self.rule_watch_count
            )
        
        elif self.rule_type == RewardRuleType.ALL_AND:
            # 所有条件都必须满足
            return (
                sign_count >= self.rule_sign_count and 
                watch_time >= self.rule_watch_time and 
                watch_count >= self.rule_watch_count
            )
        
        return False 