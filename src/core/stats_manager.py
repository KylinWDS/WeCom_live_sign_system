from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.live_booking import LiveBooking
from models.live_viewer import LiveViewer
from models.sign_record import SignRecord
from utils.logger import get_logger
from utils.cache import Cache

logger = get_logger(__name__)
cache = Cache()

class StatsManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def get_live_stats(self, living_id: str) -> Dict[str, Any]:
        """获取直播统计数据
        
        Args:
            living_id: 直播ID
            
        Returns:
            Dict: 统计数据
        """
        cache_key = f"live_stats_{living_id}"
        if cache.exists(cache_key):
            return cache.get(cache_key)
            
        try:
            with self.db_manager.get_session() as session:
                # 获取直播基本信息
                live = session.query(LiveBooking).filter_by(livingid=living_id).first()
                if not live:
                    return {}
                    
                # 获取观看记录
                viewers = session.query(LiveViewer).filter_by(living_id=living_id).all()
                
                # 获取签到记录
                sign_records = session.query(SignRecord).filter_by(living_id=living_id).all()
                
                # 计算统计数据
                stats = {
                    "basic_info": {
                        "theme": live.theme,
                        "start_time": live.living_start,
                        "end_time": live.living_start + timedelta(seconds=live.living_duration),
                        "anchor_userid": live.anchor_userid,
                        "status": live.status
                    },
                    "viewer_stats": {
                        "total_viewers": len(viewers),
                        "internal_viewers": len([v for v in viewers if v.user_type == 1]),
                        "external_viewers": len([v for v in viewers if v.user_type == 2]),
                        "peak_viewers": self._calculate_peak_viewers(viewers),
                        "peak_time": self._calculate_peak_time(viewers),
                        "avg_watch_time": sum(v.total_watch_time for v in viewers) / len(viewers) if viewers else 0,
                        "comment_count": sum(1 for v in viewers if v.is_comment),
                        "mic_count": sum(1 for v in viewers if v.is_mic)
                    },
                    "sign_stats": {
                        "total_signs": len(sign_records),
                        "unique_signers": len(set(s.user_id for s in sign_records)),
                        "normal_signs": len([s for s in sign_records if s.sign_type == 1]),
                        "makeup_signs": len([s for s in sign_records if s.sign_type == 2])
                    }
                }
                
                cache.set(cache_key, stats, expire=3600)  # 缓存1小时
                return stats
                
        except Exception as e:
            logger.error(f"获取直播统计数据失败: {str(e)}")
            return {}
            
    def _calculate_peak_viewers(self, viewers: List[LiveViewer]) -> int:
        """计算峰值观看人数"""
        try:
            # 按5分钟间隔统计在线人数
            time_slots = {}
            for viewer in viewers:
                if not viewer.first_enter_time or not viewer.last_leave_time:
                    continue
                    
                current_time = viewer.first_enter_time
                while current_time <= viewer.last_leave_time:
                    slot_key = current_time.strftime("%Y-%m-%d %H:%M")
                    time_slots[slot_key] = time_slots.get(slot_key, 0) + 1
                    current_time += timedelta(minutes=5)
                    
            return max(time_slots.values()) if time_slots else 0
            
        except Exception as e:
            logger.error(f"计算峰值观看人数失败: {str(e)}")
            return 0
            
    def _calculate_peak_time(self, viewers: List[LiveViewer]) -> datetime:
        """计算峰值观看时间"""
        try:
            # 按5分钟间隔统计在线人数
            time_slots = {}
            for viewer in viewers:
                if not viewer.first_enter_time or not viewer.last_leave_time:
                    continue
                    
                current_time = viewer.first_enter_time
                while current_time <= viewer.last_leave_time:
                    slot_key = current_time.strftime("%Y-%m-%d %H:%M")
                    time_slots[slot_key] = time_slots.get(slot_key, 0) + 1
                    current_time += timedelta(minutes=5)
                    
            if not time_slots:
                return None
                
            # 找出人数最多的时间段
            peak_slot = max(time_slots.items(), key=lambda x: x[1])
            return datetime.strptime(peak_slot[0], "%Y-%m-%d %H:%M")
            
        except Exception as e:
            logger.error(f"计算峰值观看时间失败: {str(e)}")
            return None
            
    def get_user_profile(self, living_id: str) -> Dict[str, Any]:
        """获取用户画像分析
        
        Args:
            living_id: 直播ID
            
        Returns:
            Dict: 用户画像数据
        """
        cache_key = f"user_profile_{living_id}"
        if cache.exists(cache_key):
            return cache.get(cache_key)
            
        try:
            with self.db_manager.get_session() as session:
                # 获取观看记录
                viewers = session.query(LiveViewer).filter_by(living_id=living_id).all()
                
                # 获取签到记录
                sign_records = session.query(SignRecord).filter_by(living_id=living_id).all()
                
                # 构建用户画像数据
                profile = {
                    "viewer_stats": {
                        "total_viewers": len(viewers),
                        "internal_viewers": len([v for v in viewers if v.user_type == 1]),
                        "external_viewers": len([v for v in viewers if v.user_type == 2]),
                        "avg_watch_time": sum(v.total_watch_time for v in viewers) / len(viewers) if viewers else 0,
                        "max_watch_time": max((v.total_watch_time for v in viewers), default=0),
                        "min_watch_time": min((v.total_watch_time for v in viewers), default=0)
                    },
                    "sign_stats": {
                        "total_signs": len(sign_records),
                        "valid_signs": len([s for s in sign_records if s.sign_status == 1]),
                        "normal_signs": len([s for s in sign_records if s.sign_type == 1]),
                        "makeup_signs": len([s for s in sign_records if s.sign_type == 2])
                    },
                    "engagement_stats": {
                        "comment_rate": len([v for v in viewers if v.is_comment]) / len(viewers) if viewers else 0,
                        "mic_rate": len([v for v in viewers if v.is_mic]) / len(viewers) if viewers else 0,
                        "sign_rate": len(set(s.user_id for s in sign_records)) / len(viewers) if viewers else 0
                    }
                }
                
                cache.set(cache_key, profile, expire=3600)
                return profile
                
        except Exception as e:
            logger.error(f"获取用户画像数据失败: {str(e)}")
            return {} 