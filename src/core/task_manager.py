from typing import Dict, Any
import threading
import time
from datetime import datetime, timedelta
from src.utils.logger import get_logger
from src.api.wecom import WeComAPI
from src.core.database import DatabaseManager

logger = get_logger(__name__)

class TaskManager:
    """任务管理器"""
    
    def __init__(self, wecom_api: WeComAPI, db_manager: DatabaseManager):
        self.wecom_api = wecom_api
        self.db_manager = db_manager
        self.tasks = {}
        self.lock = threading.Lock()
    
    def schedule_live_info_task(self, livingid: str, start_time: int):
        """调度直播详情拉取任务
        
        Args:
            livingid: 直播ID
            start_time: 直播开始时间戳
        """
        try:
            # 创建10分钟后拉取任务
            self._schedule_task(
                livingid,
                self._fetch_live_info,
                args=[livingid],
                delay=600  # 10分钟
            )
            
            # 创建直播开始时间+5分钟后的拉取任务
            start_datetime = datetime.fromtimestamp(start_time)
            delay = int((start_datetime + timedelta(minutes=5) - datetime.now()).total_seconds())
            if delay > 0:
                self._schedule_task(
                    f"{livingid}_start",
                    self._fetch_live_info,
                    args=[livingid],
                    delay=delay
                )
                
            logger.info(f"已调度直播详情拉取任务: {livingid}")
            
        except Exception as e:
            logger.error(f"调度直播详情拉取任务失败: {str(e)}")
    
    def _schedule_task(self, task_id: str, func, args: list = None, delay: int = 0):
        """调度任务
        
        Args:
            task_id: 任务ID
            func: 要执行的函数
            args: 函数参数
            delay: 延迟执行时间(秒)
        """
        with self.lock:
            if task_id in self.tasks:
                return
                
            def task_wrapper():
                try:
                    time.sleep(delay)
                    if args:
                        func(*args)
                    else:
                        func()
                except Exception as e:
                    logger.error(f"执行任务失败: {str(e)}")
                finally:
                    with self.lock:
                        if task_id in self.tasks:
                            del self.tasks[task_id]
            
            thread = threading.Thread(target=task_wrapper)
            thread.daemon = True
            self.tasks[task_id] = thread
            thread.start()
    
    def _fetch_live_info(self, livingid: str):
        """拉取直播详情
        
        Args:
            livingid: 直播ID
        """
        try:
            # 获取直播详情
            result = self.wecom_api.get_living_info(livingid)
            if result["errcode"] != 0:
                logger.error(f"获取直播详情失败: {result['errmsg']}")
                return
                
            # 更新数据库
            with self.db_manager.get_session() as session:
                live = session.query(LiveBooking).filter_by(livingid=livingid).first()
                if live:
                    live.update_from_api(result["living_info"])
                    session.commit()
                    logger.info(f"更新直播详情成功: {livingid}")
                else:
                    logger.warning(f"未找到直播记录: {livingid}")
                    
        except Exception as e:
            logger.error(f"拉取直播详情失败: {str(e)}")
    
    def cancel_task(self, task_id: str):
        """取消任务
        
        Args:
            task_id: 任务ID
        """
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id] 