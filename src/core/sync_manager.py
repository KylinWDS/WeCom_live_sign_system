import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.utils.logger import get_logger
from src.core.database import DatabaseManager
from src.core.wecom_api import WeComAPI
from src.core.config_manager import ConfigManager
from models.live_booking import LiveBooking
from models.live_viewer import LiveViewer
from models.sign_record import SignRecord
from utils.cache import Cache

logger = get_logger(__name__)
cache = Cache()

class SyncManager:
    """同步管理器"""
    
    def __init__(self, db_manager: DatabaseManager, wecom_api: WeComAPI):
        """初始化同步管理器"""
        self.db_manager = db_manager
        self.config_manager = ConfigManager()
        self.wecom_api = wecom_api
        self.sync_task = None
        self.is_running = False
    
    def start_sync(self):
        """开始同步"""
        try:
            # 获取企业微信配置
            corp_id = self.config_manager.get("wecom.corp_id")
            corp_secret = self.config_manager.get("wecom.corp_secret")
            
            if not corp_id or not corp_secret:
                logger.error("企业微信配置未设置")
                return
            
            # 初始化企业微信API
            self.wecom_api = WeComAPI(corp_id, corp_secret)
            
            # 创建同步任务
            self.is_running = True
            self.sync_task = asyncio.create_task(self._sync_loop())
            
            logger.info("同步任务已启动")
            
        except Exception as e:
            logger.error(f"启动同步任务失败: {str(e)}")
            self.stop_sync()
    
    def stop_sync(self):
        """停止同步"""
        try:
            # 停止同步任务
            self.is_running = False
            if self.sync_task:
                self.sync_task.cancel()
                self.sync_task = None
            
            logger.info("同步任务已停止")
            
        except Exception as e:
            logger.error(f"停止同步任务失败: {str(e)}")
    
    async def _sync_loop(self):
        """同步循环"""
        try:
            while self.is_running:
                # 同步部门数据
                await self._sync_departments()
                
                # 同步用户数据
                await self._sync_users()
                
                # 等待下一次同步
                await asyncio.sleep(3600)  # 每小时同步一次
                
        except asyncio.CancelledError:
            logger.info("同步任务已取消")
        except Exception as e:
            logger.error(f"同步循环异常: {str(e)}")
            self.stop_sync()
    
    async def _sync_departments(self):
        """同步部门数据"""
        try:
            # 获取部门列表
            departments = self.wecom_api.get_department_list()
            if not departments:
                return
            
            # 更新部门数据
            for dept in departments:
                await self._update_department(dept)
            
            logger.info(f"同步部门数据完成，共 {len(departments)} 个部门")
            
        except Exception as e:
            logger.error(f"同步部门数据失败: {str(e)}")
    
    async def _sync_users(self):
        """同步用户数据"""
        try:
            # 获取部门列表
            departments = self.wecom_api.get_department_list()
            if not departments:
                return
            
            # 同步每个部门的用户
            for dept in departments:
                users = self.wecom_api.get_department_users(dept["id"])
                if not users:
                    continue
                
                # 更新用户数据
                for user in users:
                    await self._update_user(user)
            
            logger.info("同步用户数据完成")
            
        except Exception as e:
            logger.error(f"同步用户数据失败: {str(e)}")
    
    async def _update_department(self, dept: dict):
        """更新部门数据"""
        try:
            # TODO: 实现部门数据更新
            pass
            
        except Exception as e:
            logger.error(f"更新部门数据失败: {str(e)}")
    
    async def _update_user(self, user: dict):
        """更新用户数据"""
        try:
            # TODO: 实现用户数据更新
            pass
            
        except Exception as e:
            logger.error(f"更新用户数据失败: {str(e)}")
    
    def sync_live_data(self, living_id: str) -> bool:
        """同步直播数据
        
        Args:
            living_id: 直播ID
            
        Returns:
            bool: 是否同步成功
        """
        try:
            # 获取直播详情
            live_info = self.wecom_api.get_living_info(living_id)
            if live_info["errcode"] != 0:
                logger.error(f"获取直播详情失败: {live_info['errmsg']}")
                return False
                
            # 更新直播信息
            with self.db_manager.get_session() as session:
                live = session.query(LiveBooking).filter_by(livingid=living_id).first()
                if not live:
                    live = LiveBooking(livingid=living_id)
                    session.add(live)
                    
                live.update_from_api(live_info["living_info"])
                session.commit()
                
            # 同步观看记录
            self._sync_viewer_data(living_id)
            
            # 清除缓存
            cache.delete(f"live_stats_{living_id}")
            cache.delete(f"user_profile_{living_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"同步直播数据失败: {str(e)}")
            return False
            
    def _sync_viewer_data(self, living_id: str):
        """同步观看记录数据"""
        try:
            next_key = ""
            while True:
                # 获取观看明细
                watch_stat = self.wecom_api.get_watch_stat(living_id, next_key)
                if watch_stat["errcode"] != 0:
                    logger.error(f"获取观看明细失败: {watch_stat['errmsg']}")
                    break
                    
                # 处理企业成员观看记录
                self._process_internal_users(watch_stat["stat_info"]["users"], living_id)
                
                # 处理外部用户观看记录
                self._process_external_users(watch_stat["stat_info"]["external_users"], living_id)
                
                # 检查是否还有更多数据
                if watch_stat["ending"] == 1:
                    break
                next_key = watch_stat["next_key"]
                
        except Exception as e:
            logger.error(f"同步观看记录失败: {str(e)}")
            
    def _process_internal_users(self, users: List[Dict], living_id: str):
        """处理企业成员观看记录"""
        with self.db_manager.get_session() as session:
            for user in users:
                viewer = session.query(LiveViewer).filter_by(
                    living_id=living_id,
                    user_id=user["userid"]
                ).first()
                
                if not viewer:
                    viewer = LiveViewer(
                        living_id=living_id,
                        user_id=user["userid"],
                        user_type=1  # 企业成员
                    )
                    session.add(viewer)
                    
                viewer.update_from_api(user)
                session.commit()
                
    def _process_external_users(self, users: List[Dict], living_id: str):
        """处理外部用户观看记录"""
        with self.db_manager.get_session() as session:
            for user in users:
                viewer = session.query(LiveViewer).filter_by(
                    living_id=living_id,
                    user_id=user["external_userid"]
                ).first()
                
                if not viewer:
                    viewer = LiveViewer(
                        living_id=living_id,
                        user_id=user["external_userid"],
                        user_type=2  # 外部用户
                    )
                    session.add(viewer)
                    
                viewer.update_from_api(user)
                session.commit()
                
    def schedule_sync(self, living_id: str, interval: int = 300):
        """定时同步数据
        
        Args:
            living_id: 直播ID
            interval: 同步间隔(秒),默认5分钟
        """
        try:
            # 获取直播信息
            with self.db_manager.get_session() as session:
                live = session.query(LiveBooking).filter_by(livingid=living_id).first()
                if not live:
                    return
                    
            # 检查直播状态
            if live.status not in [1, 2]:  # 不是直播中或已结束
                return
                
            # 同步数据
            self.sync_live_data(living_id)
            
            # 设置下次同步
            if live.status == 1:  # 直播中
                from threading import Timer
                Timer(interval, self.schedule_sync, args=[living_id, interval]).start()
                
        except Exception as e:
            logger.error(f"定时同步数据失败: {str(e)}")
            
    def verify_data_consistency(self, living_id: str) -> bool:
        """验证数据一致性
        
        Args:
            living_id: 直播ID
            
        Returns:
            bool: 是否一致
        """
        try:
            # 获取直播信息
            live_info = self.wecom_api.get_living_info(living_id)
            if live_info["errcode"] != 0:
                return False
                
            # 获取本地数据
            with self.db_manager.get_session() as session:
                live = session.query(LiveBooking).filter_by(livingid=living_id).first()
                if not live:
                    return False
                    
                # 验证基本信息
                api_info = live_info["living_info"]
                if (live.theme != api_info["theme"] or
                    live.viewer_num != api_info["viewer_num"] or
                    live.comment_num != api_info["comment_num"] or
                    live.mic_num != api_info["mic_num"]):
                    return False
                    
                # 验证观看记录
                viewers = session.query(LiveViewer).filter_by(living_id=living_id).all()
                if len(viewers) != api_info["viewer_num"]:
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"验证数据一致性失败: {str(e)}")
            return False 