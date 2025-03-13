import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.live_viewer import LiveViewer
from models.sign_record import SignRecord
from utils.logger import get_logger
from utils.cache import Cache

logger = get_logger(__name__)
cache = Cache()

class ViewerStatsManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.batch_size = 1000  # 批处理大小
        
    def get_viewer_stats(self, living_id: int) -> pd.DataFrame:
        """获取观众统计数据(使用缓存)"""
        cache_key = f"viewer_stats_{living_id}"
        if cache.exists(cache_key):
            return cache.get(cache_key)
            
        try:
            with self.db_manager.get_session() as session:
                # 使用批量查询
                viewers = session.query(LiveViewer).filter_by(
                    living_id=living_id
                ).yield_per(self.batch_size)
                
                # 使用pandas高效处理
                data = []
                for viewer in viewers:
                    data.append({
                        "用户ID": viewer.user_id,
                        "用户名": viewer.user_name,
                        "部门": viewer.department,
                        "观看时长(分钟)": viewer.total_watch_time / 60,
                        "是否评论": "是" if viewer.is_comment else "否",
                        "是否连麦": "是" if viewer.is_mic else "否",
                        "邀请人": viewer.invitor_name
                    })
                    
                df = pd.DataFrame(data)
                cache.set(cache_key, df, expire=3600)  # 缓存1小时
                return df
                
        except Exception as e:
            logger.error(f"获取观众统计数据失败: {str(e)}")
            raise
            
    def get_department_stats(self, living_id: int) -> pd.DataFrame:
        """获取部门统计数据(使用缓存)"""
        cache_key = f"dept_stats_{living_id}"
        if cache.exists(cache_key):
            return cache.get(cache_key)
            
        try:
            with self.db_manager.get_session() as session:
                # 使用SQL聚合函数优化查询
                stats = session.query(
                    LiveViewer.department,
                    func.count(LiveViewer.id).label('total_count'),
                    func.sum(LiveViewer.total_watch_time).label('total_watch_time'),
                    func.sum(case((LiveViewer.is_comment == 1, 1), else_=0)).label('comment_count'),
                    func.sum(case((LiveViewer.is_mic == 1, 1), else_=0)).label('mic_count')
                ).filter_by(
                    living_id=living_id
                ).group_by(
                    LiveViewer.department
                ).all()
                
                # 转换为DataFrame
                data = []
                for stat in stats:
                    data.append({
                        "部门": stat.department or "未设置",
                        "总人数": stat.total_count,
                        "总观看时长(分钟)": stat.total_watch_time / 60,
                        "平均观看时长(分钟)": (stat.total_watch_time / stat.total_count / 60) if stat.total_count > 0 else 0,
                        "评论人数": stat.comment_count,
                        "连麦人数": stat.mic_count
                    })
                    
                df = pd.DataFrame(data)
                cache.set(cache_key, df, expire=3600)
                return df
                
        except Exception as e:
            logger.error(f"获取部门统计数据失败: {str(e)}")
            raise
            
    def get_time_distribution(self, living_id: int) -> pd.DataFrame:
        """获取观看时长分布数据
        
        Args:
            living_id: 直播ID
            
        Returns:
            pd.DataFrame: 观看时长分布数据
        """
        try:
            with self.db_manager.get_session() as session:
                # 获取观众数据
                viewers = session.query(LiveViewer).filter_by(
                    living_id=living_id
                ).all()
                
                # 统计时长分布
                duration_ranges = {
                    "0-30分钟": 0,
                    "31-60分钟": 0,
                    "61-90分钟": 0,
                    "91-120分钟": 0,
                    "120分钟以上": 0
                }
                
                for viewer in viewers:
                    duration = viewer.watch_duration
                    if duration <= 30:
                        duration_ranges["0-30分钟"] += 1
                    elif duration <= 60:
                        duration_ranges["31-60分钟"] += 1
                    elif duration <= 90:
                        duration_ranges["61-90分钟"] += 1
                    elif duration <= 120:
                        duration_ranges["91-120分钟"] += 1
                    else:
                        duration_ranges["120分钟以上"] += 1
                        
                # 转换为DataFrame
                data = [
                    {"时长范围": range_name, "人数": count}
                    for range_name, count in duration_ranges.items()
                ]
                
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"获取观看时长分布数据失败: {str(e)}")
            raise

    def get_user_profile(self, living_id: int) -> Dict:
        """获取用户画像分析
        
        Args:
            living_id: 直播ID
            
        Returns:
            Dict: 用户画像数据
        """
        try:
            with self.db_manager.get_session() as session:
                # 获取观看记录
                viewers = session.query(LiveViewer).filter_by(
                    living_id=living_id
                ).all()
                
                # 获取签到记录
                sign_records = session.query(SignRecord).filter_by(
                    living_id=living_id
                ).all()
                
                # 构建用户画像数据
                profile = {
                    "viewer_stats": {
                        "total_viewers": len(viewers),
                        "internal_viewers": len([v for v in viewers if v.user_type == 1]),
                        "external_viewers": len([v for v in viewers if v.user_type == 2]),
                        "avg_watch_time": sum(v.watch_duration for v in viewers) / len(viewers) if viewers else 0,
                        "max_watch_time": max((v.watch_duration for v in viewers), default=0),
                        "min_watch_time": min((v.watch_duration for v in viewers), default=0)
                    },
                    "sign_stats": {
                        "total_signs": len(sign_records),
                        "valid_signs": len([s for s in sign_records if s.sign_status == 1]),
                        "normal_signs": len([s for s in sign_records if s.sign_type == 1]),
                        "makeup_signs": len([s for s in sign_records if s.sign_type == 2])
                    },
                    "engagement_metrics": {
                        "sign_rate": len(sign_records) / len(viewers) * 100 if viewers else 0,
                        "comment_rate": len([v for v in viewers if v.is_comment]) / len(viewers) * 100 if viewers else 0,
                        "mic_rate": len([v for v in viewers if v.is_mic]) / len(viewers) * 100 if viewers else 0
                    },
                    "user_behavior": {
                        "early_sign_rate": len([s for s in sign_records if s.sign_time.hour < 12]) / len(sign_records) * 100 if sign_records else 0,
                        "late_sign_rate": len([s for s in sign_records if s.sign_time.hour >= 12]) / len(sign_records) * 100 if sign_records else 0,
                        "high_engagement_rate": len([v for v in viewers if v.watch_duration > 3600]) / len(viewers) * 100 if viewers else 0
                    }
                }
                
                return profile
                
        except Exception as e:
            logger.error(f"获取用户画像分析失败: {str(e)}")
            raise
            
    def get_department_profile(self, living_id: int) -> Dict:
        """获取部门画像分析
        
        Args:
            living_id: 直播ID
            
        Returns:
            Dict: 部门画像数据
        """
        try:
            with self.db_manager.get_session() as session:
                # 获取观看记录
                viewers = session.query(LiveViewer).filter_by(
                    living_id=living_id
                ).all()
                
                # 获取签到记录
                sign_records = session.query(SignRecord).filter_by(
                    living_id=living_id
                ).all()
                
                # 按部门统计
                dept_stats = {}
                
                for viewer in viewers:
                    dept = viewer.department or "未设置"
                    if dept not in dept_stats:
                        dept_stats[dept] = {
                            "viewers": [],
                            "total_watch_time": 0,
                            "sign_count": 0,
                            "comment_count": 0,
                            "mic_count": 0
                        }
                    
                    dept_stats[dept]["viewers"].append(viewer)
                    dept_stats[dept]["total_watch_time"] += viewer.watch_duration
                    dept_stats[dept]["comment_count"] += 1 if viewer.is_comment else 0
                    dept_stats[dept]["mic_count"] += 1 if viewer.is_mic else 0
                
                for sign in sign_records:
                    dept = sign.department or "未设置"
                    if dept in dept_stats:
                        dept_stats[dept]["sign_count"] += 1
                
                # 计算部门指标
                for dept in dept_stats:
                    stats = dept_stats[dept]
                    viewer_count = len(stats["viewers"])
                    stats["avg_watch_time"] = stats["total_watch_time"] / viewer_count if viewer_count > 0 else 0
                    stats["sign_rate"] = stats["sign_count"] / viewer_count * 100 if viewer_count > 0 else 0
                    stats["comment_rate"] = stats["comment_count"] / viewer_count * 100 if viewer_count > 0 else 0
                    stats["mic_rate"] = stats["mic_count"] / viewer_count * 100 if viewer_count > 0 else 0
                
                return dept_stats
                
        except Exception as e:
            logger.error(f"获取部门画像分析失败: {str(e)}")
            raise
            
    def get_sign_records(self, living_id: int) -> pd.DataFrame:
        """获取签到记录(使用缓存)"""
        cache_key = f"sign_records_{living_id}"
        if cache.exists(cache_key):
            return cache.get(cache_key)
            
        try:
            with self.db_manager.get_session() as session:
                # 使用批量查询
                records = session.query(SignRecord).filter_by(
                    living_id=living_id
                ).yield_per(self.batch_size)
                
                # 使用pandas高效处理
                data = []
                for record in records:
                    data.append({
                        "用户ID": record.user_id,
                        "用户名": record.user_name,
                        "签到时间": record.sign_time,
                        "签到类型": "正常签到" if record.sign_type == 1 else "补签",
                        "签到状态": "有效" if record.sign_status == 1 else "无效"
                    })
                    
                df = pd.DataFrame(data)
                cache.set(cache_key, df, expire=3600)
                return df
                
        except Exception as e:
            logger.error(f"获取签到记录失败: {str(e)}")
            raise
            
    def get_invitation_stats(self, living_id: int) -> Dict:
        """获取邀请统计(使用缓存)"""
        cache_key = f"invitation_stats_{living_id}"
        if cache.exists(cache_key):
            return cache.get(cache_key)
            
        try:
            with self.db_manager.get_session() as session:
                # 使用SQL聚合函数优化查询
                stats = session.query(
                    func.count(case((LiveViewer.invitor_id.isnot(None), 1), else_=0)).label('total_invited'),
                    func.count(case((and_(LiveViewer.invitor_id.isnot(None), LiveViewer.invitor_type == 1), 1), else_=0)).label('internal_invited'),
                    func.count(case((and_(LiveViewer.invitor_id.isnot(None), LiveViewer.invitor_type == 2), 1), else_=0)).label('external_invited')
                ).filter_by(
                    living_id=living_id
                ).first()
                
                result = {
                    "total_invited": stats.total_invited,
                    "internal_invited": stats.internal_invited,
                    "external_invited": stats.external_invited,
                    "invitation_chain": self._analyze_invitation_chain(living_id)
                }
                
                cache.set(cache_key, result, expire=3600)
                return result
                
        except Exception as e:
            logger.error(f"获取邀请统计失败: {str(e)}")
            raise
            
    def _analyze_invitation_chain(self, living_id: int) -> Dict:
        """分析邀请链(优化版本)"""
        try:
            with self.db_manager.get_session() as session:
                # 使用SQL递归CTE优化邀请链分析
                chain_query = """
                WITH RECURSIVE invitation_chain AS (
                    SELECT 
                        user_id,
                        invitor_id,
                        1 as depth,
                        ARRAY[user_id] as path
                    FROM live_viewers
                    WHERE living_id = :living_id AND invitor_id IS NOT NULL
                    
                    UNION ALL
                    
                    SELECT 
                        v.user_id,
                        v.invitor_id,
                        c.depth + 1,
                        c.path || v.user_id
                    FROM live_viewers v
                    JOIN invitation_chain c ON v.invitor_id = c.user_id
                    WHERE v.living_id = :living_id
                    AND v.user_id != ALL(c.path)
                )
                SELECT 
                    MAX(depth) as max_depth,
                    COUNT(DISTINCT CASE WHEN depth = 1 THEN user_id END) as direct_invites,
                    COUNT(DISTINCT CASE WHEN depth > 1 THEN user_id END) as indirect_invites,
                    array_agg(DISTINCT path) as paths
                FROM invitation_chain
                GROUP BY living_id
                """
                
                result = session.execute(chain_query, {"living_id": living_id}).first()
                
                return {
                    "direct_invites": result.direct_invites,
                    "indirect_invites": result.indirect_invites,
                    "invitation_depth": result.max_depth,
                    "invitation_paths": result.paths
                }
                
        except Exception as e:
            logger.error(f"分析邀请链失败: {str(e)}")
            raise 