from datetime import datetime
import requests
from sqlalchemy.orm import Session
from src.utils.logger import get_logger
from src.models.live_booking import LiveBooking
from src.models.live_viewer import LiveViewer, UserSource
from src.models.living import Living
from src.models.user import User
from src.core.token_manager import TokenManager
from src.api.wecom import WeComAPI
from sqlalchemy import text, func
from typing import List, Tuple, Dict, Any, Optional
import threading
from src.models.corporation import Corporation
from src.core.auth_manager import AuthManager
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = get_logger(__name__)

class LiveViewerManager:
    """直播观看者管理器"""
    
    def __init__(self, db_manager, auth_manager=None):
        """初始化直播观看者管理器
        
        Args:
            db_manager: 数据库管理器
            auth_manager: 认证管理器，可选
        """
        self.db_manager = db_manager
        self.auth_manager = auth_manager or AuthManager(db_manager)
        self.session_factory = db_manager.get_session
        self.livingid = None
        self.wecom_api = None
        
        # 缓存
        self._cache = {
            "existing_viewers": {},      # 现有内部用户观看记录: {userid: viewer}
            "existing_external_viewers": {},  # 现有外部用户观看记录: {userid: viewer}
            "user_map": {},             # 用户信息缓存: {userid: user_info}
            "external_user_map": {},    # 外部用户信息缓存: {external_userid: user_info}
            "anchor_info": {},          # 主播信息缓存
            "stat_info": None,          # API返回的统计信息缓存
            "wecom_contact_tried": False # 是否已尝试过获取企业微信通讯录
        }
        
        # 统计信息
        self._stats = {
            "total_viewers": 0,          # 总观众数
            "internal_viewers": 0,       # 内部观众数
            "external_viewers": 0,       # 外部观众数
            "sign_count": 0,             # 总签到次数
            "success_count": 0,          # 成功处理的记录数
            "error_count": 0,            # 处理失败的记录数
            "last_sync_time": None,      # 最后同步时间
            "last_error": None,          # 最后一次错误信息
            "last_error_time": None,     # 最后一次错误时间
            "processed_batches": 0,      # 已处理批次数
        }
    
    def _preload_existing_viewers(self, living_id):
        """预加载当前直播的观看人员信息
        
        Args:
            living_id: 直播ID
            
        Returns:
            Dict[str, LiveViewer]: 观看人员信息字典，key为"user_type:userid"格式
        """
        existing_viewers = {}
        with self.db_manager.get_session() as session:
            # 先获取直播记录的ID
            live_info = session.query(Living).filter_by(livingid=living_id).first()
            if not live_info:
                logger.warning(f"找不到直播记录: {living_id}")
                return existing_viewers
            
            logger.debug(f"找到直播记录: {live_info.id}")
            
            # 使用直播记录的ID查询观看记录
            viewers = session.query(LiveViewer).filter_by(living_id=live_info.id).all()
            for viewer in viewers:
                key = f"{viewer.user_type}:{viewer.userid}"
                existing_viewers[key] = viewer
                logger.debug(f"加载已存在的观看记录: {key}")
            
            logger.info(f"已加载 {len(existing_viewers)} 条观看记录")
        return existing_viewers
    
    def _preload_user_map(self):
        """预加载用户模型信息
        
        Returns:
            Dict[str, Dict]: 用户信息字典，key为userid，value为用户信息
        """
        user_map = {}
        with self.db_manager.get_session() as session:
            users = session.query(User).all()
            for user in users:
                user_data = {
                    "name": user.name,
                    "wecom_code": user.wecom_code,
                    "login_name": user.login_name,
                    "userid": user.userid
                }
                
                # 使用所有可能的ID作为key
                if user.userid:
                    user_map[user.userid] = user_data
                if user.wecom_code:
                    user_map[user.wecom_code] = user_data
                if user.login_name:
                    user_map[user.login_name] = user_data
                    
                logger.debug(f"缓存用户信息: {user_data}")
                
        return user_map
    
    def _preload_context(self, living_id: int):
        """预加载上下文数据
        
        Args:
            living_id: 直播ID
        """
        try:
            logger.info(f"开始预加载直播[{living_id}]的上下文数据...")
            
            # 1. 加载主播信息
            with self.db_manager.get_session() as session:
                live_info = session.query(Living).filter_by(livingid=living_id).first()
                if not live_info:
                    logger.error(f"找不到ID为[{living_id}]的直播记录")
                    return False
                    
                logger.info(f"找到直播记录: {live_info.livingid}")
                
                # 获取主播信息
                anchor_user = None
                if live_info.anchor_userid:
                    anchor_user = session.query(User).filter(
                        (User.wecom_code == live_info.anchor_userid) | 
                        (User.login_name == live_info.anchor_userid)
                    ).first()
                    
                    if anchor_user:
                        logger.info(f"找到主播信息: {anchor_user.name}({live_info.anchor_userid})")
                    else:
                        logger.warning(f"未找到主播[{live_info.anchor_userid}]的用户信息")
                
                # 设置主播信息缓存
                self._cache["anchor_info"] = {
                    "userid": live_info.anchor_userid,
                    "name": anchor_user.name if anchor_user else live_info.anchor_userid,
                    "live_booking_id": live_info.live_booking_id
                }
                logger.info("主播信息缓存已更新")
            
            # 2. 加载当前直播数据库观看人员信息
            logger.info("开始加载观看人员信息...")
            self._cache["existing_viewers"] = self._preload_existing_viewers(living_id)
            logger.info(f"已加载 {len(self._cache['existing_viewers'])} 条观看记录")
            
            # 3. 加载用户users模型信息
            logger.info("开始加载用户模型信息...")
            self._cache["user_map"] = self._preload_user_map()
            logger.info(f"已加载 {len(self._cache['user_map'])} 条用户信息")
            
            # 4. 初始化其他缓存
            self._cache["wecom_contact_tried"] = False
            logger.info("其他缓存已初始化")
            
            logger.info("上下文数据预加载完成")
            return True
            
        except Exception as e:
            logger.error(f"预加载上下文数据失败: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            self._cache = {}  # 重置缓存
            return False
    
    def _preload_user_information(self, session=None):
        """预加载所有可能的用户信息"""
        start_time = time.time()
        logger.info("开始预加载用户信息...")
        
        # 如果没有提供session，则创建新的session
        if not session:
            with self.db_manager.get_session() as new_session:
                self._do_preload_user_info(new_session)
        else:
            # 使用提供的session
            self._do_preload_user_info(session)
        
        duration = time.time() - start_time
        logger.info(f"用户信息预加载完成，共 {len(self._cache['user_map'])} 条，耗时 {duration:.2f} 秒")
    
    def _do_preload_user_info(self, session):
        """执行实际的用户信息预加载，同时考虑wecom_code和login_name"""
        from src.models.user import User
        users = session.query(User).all()
        
        for user in users:
            user_data = {
                "id": user.userid,
                "name": user.name,
                "wecom_code": user.wecom_code,
                "login_name": user.login_name,
                "department": user.department if hasattr(user, 'department') else None,
                "department_id": user.department_id if hasattr(user, 'department_id') else None
            }
            
            # 使用企业微信ID作为主键
            if user.wecom_code:
                self._cache["user_map"][user.wecom_code] = user_data
            
            # 同时也可以用登录名查找
            if user.login_name:
                self._cache["user_map"][user.login_name] = user_data
        
        logger.info(f"已预加载 {len(users)} 条用户信息")
    
    def _initialize_wecom_api(self):
        """初始化企业微信API"""
        try:
            # 获取企业信息
            with self.db_manager.get_session() as session:
                # 获取当前用户信息
                if self.auth_manager:
                    user_id = self.auth_manager.get_current_user_id()
                    from src.models.user import User
                    user = session.query(User).filter_by(userid=user_id).first()
                    if not user:
                        logger.error("当前用户未登录，无法获取企业信息")
                        return False
                else:
                    logger.error("认证管理器未设置，无法获取用户信息")
                    return False
                
                # 获取企业信息
                from src.models.corporation import Corporation
                corp = session.query(Corporation).filter_by(name=user.corpname, status=1).first()
                if not corp:
                    logger.error(f"找不到企业[{user.corpname}]的信息")
                    return False
                
                # 创建WeComAPI实例
                self.wecom_api = WeComAPI(corpid=corp.corp_id, corpsecret=corp.corp_secret, agent_id=corp.agent_id)
                return True
        except Exception as e:
            logger.error(f"初始化企业微信API失败: {str(e)}")
            return False
    
    def process_viewer_info(self, livingid: str, token: str = None) -> bool:
        """处理直播观看者信息(优化版)
        
        使用多线程和批量处理，显著减少数据库操作次数
        
        Args:
            livingid: 直播ID
            token: 可选的访问令牌，如果提供则优先使用
            
        Returns:
            bool: 处理是否成功
        """
        logger.info(f"开始处理直播[{livingid}]的观看者信息")
        start_time = time.time()
        
        # 1. 预加载上下文信息
        self.livingid = livingid
        if not self._preload_context(livingid):
            logger.error(f"预加载直播[{livingid}]的上下文信息失败")
            return False
        
        # 2. 初始化企业微信API
        if not self.wecom_api and not self._initialize_wecom_api():
            logger.error("初始化企业微信API失败")
            return False
        
        # 3. 使用多线程处理数据
        try:
            # 初始化数据队列和结果集
            internal_queue = queue.Queue()
            external_queue = queue.Queue()
            
            # 合并所有现有记录用于查找
            existing_records = {}
            existing_records.update({k: v for k, v in self._cache["existing_viewers"].items()})
            existing_records.update({k: v for k, v in self._cache["existing_external_viewers"].items()})
            
            # 获取living_id
            with self.db_manager.get_session() as session:
                live_info = session.query(Living).filter_by(livingid=livingid).first()
                if not live_info:
                    logger.error(f"找不到直播[{livingid}]的信息")
                    return False
                live_id = live_info.id
            
            # 启动数据收集线程
            logger.info("启动数据收集线程...")
            collector_future = None
            collector_stats = None
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 提交数据收集任务
                collector_future = executor.submit(
                    self._collect_all_data, livingid, internal_queue, external_queue
                )
                
                # 等待数据收集线程完成
                collector_stats = collector_future.result()
                logger.info(f"数据收集完成: {collector_stats}")
                
                # 提交数据处理任务
                internal_future = executor.submit(
                    self._process_user_queue, 
                    internal_queue, 
                    existing_records,
                    live_id,
                    1,  # 内部用户类型
                    collector_stats.get("stat_info") if collector_stats else None  # 传递 stat_info
                )
                
                external_future = executor.submit(
                    self._process_user_queue, 
                    external_queue, 
                    existing_records,
                    live_id,
                    2,  # 外部用户类型
                    collector_stats.get("stat_info") if collector_stats else None  # 传递 stat_info
                )
                
                # 等待数据处理线程完成
                internal_result = internal_future.result()
                external_result = external_future.result()
            
            # 4. 批量处理邀请关系
            logger.info("开始处理邀请关系...")
            invitation_map = {}
            invitation_map.update(internal_result.get("invitation_map", {}))
            invitation_map.update(external_result.get("invitation_map", {}))
            
            if invitation_map:
                logger.info(f"处理 {len(invitation_map)} 个邀请关系")
                self._process_all_invitations(invitation_map)
            
            # 5. 更新直播记录
            with self.db_manager.get_session() as session:
                live_info = session.query(Living).filter_by(livingid=livingid).first()
                if live_info:
                    live_info.is_viewer_fetched = 1
                    live_info.viewer_num = (
                        internal_result.get("processed_count", 0) + 
                        external_result.get("processed_count", 0)
                    )
                    session.commit()
                    logger.info(f"已更新直播[{livingid}]的观看人数: {live_info.viewer_num}")
            
            # 6. 更新统计信息
            total_viewers = (
                internal_result.get("processed_count", 0) + 
                external_result.get("processed_count", 0)
            )
            self._stats["total_viewers"] = total_viewers
            self._stats["internal_viewers"] = internal_result.get("processed_count", 0)
            self._stats["external_viewers"] = external_result.get("processed_count", 0)
            self._stats["success_count"] = (
                internal_result.get("new_count", 0) + 
                external_result.get("new_count", 0) + 
                internal_result.get("update_count", 0) + 
                external_result.get("update_count", 0)
            )
            self._stats["last_sync_time"] = datetime.now()
            
            # 记录处理时间
            duration = time.time() - start_time
            logger.info(f"成功处理直播[{livingid}]的观看数据，共 {total_viewers} 条记录，耗时 {duration:.2f} 秒")
            logger.info(f"总观众: {total_viewers}, 内部: {self._stats['internal_viewers']}, 外部: {self._stats['external_viewers']}")
            
            return True
            
        except Exception as e:
            logger.error(f"处理直播[{livingid}]观看者信息失败: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            
            # 更新错误统计
            self._stats["error_count"] += 1
            self._stats["last_error"] = str(e)
            self._stats["last_error_time"] = datetime.now()
            
            return False
    
    def _collect_all_data(self, livingid, internal_queue, external_queue):
        """收集所有数据并分发到内部和外部用户队列"""
        stats = {'total_batches': 0, 'internal_count': 0, 'external_count': 0}
        
        try:
            next_key = None
            has_more = True
            
            while has_more:
                # 获取一批数据
                logger.info(f"获取第 {stats['total_batches']+1} 批数据...")
                start_time = time.time()
                
                response = self.wecom_api.get_watch_stat(livingid, next_key)
                stats['total_batches'] += 1
                self._stats['processed_batches'] = stats['total_batches']
                
                if "error" in response:
                    logger.error(f"获取直播观看数据失败：{response.get('error')}")
                    if stats['total_batches'] == 1:
                        internal_queue.put(None)
                        external_queue.put(None)
                        return stats
                    break
                
                # 保存API返回的统计信息到缓存
                stat_info = response.get("stat_info", {})
                self._cache["stat_info"] = stat_info
                
                # 更新用户映射缓存
                if "users" in stat_info:
                    for user in stat_info["users"]:
                        if "userid" in user and "name" in user:
                            self._cache["user_map"][user["userid"]] = {
                                "name": user["name"],
                                "userid": user["userid"]
                            }
                            logger.debug(f"缓存内部用户: {user['userid']} -> {user['name']}")
                
                if "external_users" in stat_info:
                    for user in stat_info["external_users"]:
                        if "external_userid" in user and "name" in user:
                            self._cache["external_user_map"][user["external_userid"]] = {
                                "name": user["name"],
                                "external_userid": user["external_userid"]
                            }
                            logger.debug(f"缓存外部用户: {user['external_userid']} -> {user['name']}")
                
                # 处理内部用户数据
                internal_users = stat_info.get("users", [])
                for user in internal_users:
                    user['user_type'] = 1
                    internal_queue.put(user)
                
                # 处理外部用户数据
                external_users = stat_info.get("external_users", [])
                for user in external_users:
                    user['user_type'] = 2
                    external_queue.put(user)
                
                # 统计数量
                stats['internal_count'] += len(internal_users)
                stats['external_count'] += len(external_users)
                
                # 检查是否有更多数据
                next_key = response.get("next_key", "")
                has_more = bool(next_key) and not response.get("ending", False)
                
                duration = time.time() - start_time
                logger.info(f"第 {stats['total_batches']} 批数据处理完成，耗时 {duration:.2f} 秒")
                
                if has_more and (stats['total_batches'] % 5 == 0):
                    time.sleep(1)
            
            logger.info(f"所有数据收集完毕，共 {stats['internal_count']} 内部用户和 {stats['external_count']} 外部用户")
            internal_queue.put(None)
            external_queue.put(None)
            
            return stats
            
        except Exception as e:
            logger.error(f"收集数据失败: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            
            internal_queue.put(None)
            external_queue.put(None)
            return stats
    
    def _get_invitor_info(self, user_data, user_type, stat_info):
        """获取邀请人信息
        
        Args:
            user_data: 用户数据
            user_type: 用户类型(1=内部用户，2=外部用户)
            stat_info: API返回的统计信息
            
        Returns:
            tuple: (invitor_id, invitor_name)
        """
        if not user_data:
            return None, None
            
        # 1. 获取邀请人ID
        invitor_id = None
        is_internal_invitor = True
        
        # 优先使用内部邀请人ID
        invitor_id = user_data.get("invitor_userid")
        if not invitor_id:
            # 如果没有内部邀请人，尝试使用外部邀请人ID
            invitor_id = user_data.get("invitor_external_userid")
            is_internal_invitor = False
            
        if not invitor_id:
            return None, None
            
        logger.debug(f"处理邀请人信息: invitor_id={invitor_id}, is_internal={is_internal_invitor}")
        
        # 2. 获取邀请人名称
        invitor_name = None
        
        # 2.1 检查是否是主播
        anchor_info = self._cache.get("anchor_info", {})
        if invitor_id == anchor_info.get("userid"):
            invitor_name = anchor_info.get("name")
            logger.debug(f"找到主播邀请人: {invitor_id} -> {invitor_name}")
            return invitor_id, invitor_name
        
        # 2.2 从缓存中查找
        if is_internal_invitor:
            # 从内部用户缓存中查找
            user_info = self._cache["user_map"].get(invitor_id)
            if user_info and "name" in user_info:
                invitor_name = user_info["name"]
                logger.debug(f"从内部用户缓存中找到邀请人: {invitor_id} -> {invitor_name}")
                return invitor_id, invitor_name
        else:
            # 从外部用户缓存中查找
            user_info = self._cache["external_user_map"].get(invitor_id)
            if user_info and "name" in user_info:
                invitor_name = user_info["name"]
                logger.debug(f"从外部用户缓存中找到邀请人: {invitor_id} -> {invitor_name}")
                return invitor_id, invitor_name
        
        # 2.3 从API返回的统计信息中查找
        if stat_info:
            if is_internal_invitor and "users" in stat_info:
                for user in stat_info["users"]:
                    if user.get("userid") == invitor_id:
                        invitor_name = user.get("name")
                        logger.debug(f"从API统计信息中找到内部邀请人: {invitor_id} -> {invitor_name}")
                        return invitor_id, invitor_name
            elif not is_internal_invitor and "external_users" in stat_info:
                for user in stat_info["external_users"]:
                    if user.get("external_userid") == invitor_id:
                        invitor_name = user.get("name")
                        logger.debug(f"从API统计信息中找到外部邀请人: {invitor_id} -> {invitor_name}")
                        return invitor_id, invitor_name
        
        # 2.4 如果还是找不到，尝试从企业微信获取
        if not invitor_name and self.wecom_api:
            try:
                if is_internal_invitor:
                    # 获取内部用户信息
                    user_info = self.wecom_api.get_user_info(invitor_id)
                    if user_info and user_info.get("errcode") == 0:
                        invitor_name = user_info.get("name")
                        # 更新缓存
                        self._cache["user_map"][invitor_id] = {
                            "name": invitor_name,
                            "userid": invitor_id
                        }
                        logger.debug(f"从企业微信API获取到内部邀请人: {invitor_id} -> {invitor_name}")
                else:
                    # 获取外部联系人信息
                    contact_info = self.wecom_api.get_external_contact(invitor_id)
                    if contact_info and contact_info.get("errcode") == 0:
                        invitor_name = contact_info.get("name")
                        # 更新缓存
                        self._cache["external_user_map"][invitor_id] = {
                            "name": invitor_name,
                            "external_userid": invitor_id
                        }
                        logger.debug(f"从企业微信API获取到外部邀请人: {invitor_id} -> {invitor_name}")
            except Exception as e:
                logger.warning(f"获取邀请人[{invitor_id}]信息失败: {str(e)}")
        
        # 2.5 如果所有方法都无法获取到名称，使用ID作为名称
        if not invitor_name:
            invitor_name = invitor_id
            logger.warning(f"无法获取邀请人[{invitor_id}]的名称，使用ID作为名称")
        
        return invitor_id, invitor_name
    
    def _process_user_queue(self, user_queue, existing_records, living_id, user_type, stat_info):
        """处理特定类型用户队列中的数据
        
        Args:
            user_queue: 用户数据队列
            existing_records: 现有记录映射表
            living_id: 直播记录ID
            user_type: 用户类型(1内部用户/2外部用户)
            stat_info: API返回的统计信息
            
        Returns:
            dict: 处理结果统计
        """
        result = {
            'user_type': 'internal' if user_type == 1 else 'external',
            'new_records': [],
            'update_records': [],
            'processed_count': 0,
            'new_count': 0,
            'update_count': 0,
            'error_count': 0,
            'invitation_map': {}
        }
        
        # 批量操作缓冲区
        batch_size = 1000
        new_batch = []
        update_batch = []
        
        # 使用一个session处理整个批次
        with self.db_manager.get_session() as session:
            while True:
                try:
                    user_data = user_queue.get()
                    if user_data is None:  # 结束标记
                        break
                    
                    # 获取用户ID
                    userid = user_data.get("userid") if user_type == 1 else user_data.get("external_userid")
                    if not userid:
                        logger.warning(f"跳过无效用户数据: {user_data}")
                        continue
                    
                    # 获取邀请人信息
                    invitor_id, invitor_name = self._get_invitor_info(user_data, user_type, stat_info or {})
                    
                    # 创建或更新记录
                    key = f"{user_type}:{userid}"
                    if key in existing_records:
                        # 更新现有记录
                        record = existing_records[key]
                        # 确保记录与当前session关联
                        if record not in session:
                            record = session.merge(record)
                        
                        self._update_record_data(record, user_data)
                        
                        # 设置邀请人信息
                        if invitor_id:
                            record.invitor_userid = invitor_id
                            record.invitor_name = invitor_name or invitor_id
                            if invitor_id == self._cache["anchor_info"].get("userid") and hasattr(record, 'is_invited_by_anchor'):
                                record.is_invited_by_anchor = True
                                
                        update_batch.append(record)
                        result['update_count'] += 1
                    else:
                        # 创建新记录
                        record = LiveViewer.from_api_data(user_data, living_id=living_id, user_type=user_type)
                        
                        # 设置 live_booking_id
                        if self._cache["anchor_info"].get("live_booking_id"):
                            record.live_booking_id = self._cache["anchor_info"]["live_booking_id"]
                        
                        # 设置邀请人信息
                        if invitor_id:
                            record.invitor_userid = invitor_id
                            record.invitor_name = invitor_name or invitor_id
                            if invitor_id == self._cache["anchor_info"].get("userid") and hasattr(record, 'is_invited_by_anchor'):
                                record.is_invited_by_anchor = True
                                
                        new_batch.append(record)
                        # 更新映射以便后续处理
                        existing_records[key] = record
                        result['new_count'] += 1
                    
                    # 如果仍有邀请关系需要处理
                    if invitor_id and not invitor_name:
                        result['invitation_map'][key] = (invitor_id, user_type)
                    
                    result['processed_count'] += 1
                    
                    # 批量提交
                    if len(new_batch) >= batch_size:
                        session.bulk_save_objects(new_batch)
                        new_batch = []
                        session.flush()
                    
                    if len(update_batch) >= batch_size:
                        for record in update_batch:
                            session.merge(record)
                        update_batch = []
                        session.flush()
                    
                except Exception as e:
                    logger.error(f"处理用户数据失败: {str(e)}")
                    import traceback
                    logger.error(f"错误详情: {traceback.format_exc()}")
                    result['error_count'] += 1
                    continue
            
            # 提交剩余的批次
            try:
                if new_batch:
                    session.bulk_save_objects(new_batch)
                if update_batch:
                    for record in update_batch:
                        session.merge(record)
                session.commit()
            except Exception as e:
                logger.error(f"提交最后批次时失败: {str(e)}")
                session.rollback()
                raise
        
        return result
    
    def _update_record_data(self, record: LiveViewer, user_data: Dict[str, Any]) -> None:
        """更新记录数据
        
        Args:
            record: 现有记录
            user_data: 用户数据
        """
        # 更新观看信息
        record.watch_time = user_data.get('watch_time', record.watch_time)
        record.is_comment = user_data.get('is_comment', record.is_comment)
        record.is_mic = user_data.get('is_mic', record.is_mic)
        
        # 设置邀请人信息
        if not record.invitor_userid:  # 只在没有邀请人时设置
            invitor_id, invitor_name, is_anchor = self._identify_inviter(user_data)
            if invitor_id:
                record.invitor_userid = invitor_id
                record.invitor_name = invitor_name
                record.is_invited_by_anchor = is_anchor
        
        # 更新时间戳
        record.updated_at = datetime.now()
    
    def _bulk_insert_records(self, records):
        """批量插入记录
        
        Args:
            records: 记录列表
        """
        if not records:
            return

            # 确保不会设置id字段，让数据库自动生成
        for record in records:
            if hasattr(record, 'id') and record.id is not None:
                record.id = None
        
        with self.db_manager.get_session() as session:
            session.bulk_save_objects(records)
            session.commit()
    
    def _bulk_update_records(self, records):
        """批量更新记录
        
        Args:
            records: 记录列表
        """
        if not records:
            return
        
        with self.db_manager.get_session() as session:
            for record in records:
                session.merge(record)
            session.commit()
    
    def _commit_batch(self, new_batch, update_batch):
        """提交批量操作
        
        Args:
            new_batch: 新记录列表
            update_batch: 需要更新的记录列表
        """
        try:
            if new_batch:
                self._bulk_insert_records(new_batch)
            if update_batch:
                self._bulk_update_records(update_batch)
        except Exception as e:
            logger.error(f"批量提交失败: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise
    
    def _process_all_invitations(self, invitation_map):
        """批量处理所有邀请关系
        
        使用预加载数据减少数据库查询，并控制批量操作不超过1000条
        
        Args:
            invitation_map: 邀请关系映射表 {key: (inviter_id, user_type)}
        """
        if not invitation_map:
            return
        
        start_time = time.time()
        logger.info(f"开始处理 {len(invitation_map)} 个邀请关系...")
        
        try:
            # 获取预加载的主播信息
            anchor_info = self._cache.get("anchor_info", {})
            living_id = anchor_info.get("living_id")
            anchor_userid = anchor_info.get("userid")
            anchor_name = anchor_info.get("name")
            
            # 分批处理, 每批最多1000条
            MAX_BATCH_SIZE = 1000
            batch_updates = []
            update_count = 0
            
            # 获取所有涉及的用户ID
            all_user_ids = set()
            all_inviter_ids = set()
            
            for key, (inviter_id, inviter_type) in invitation_map.items():
                user_type, user_id = key.split(":", 1)
                all_user_ids.add((user_id, int(user_type)))
                all_inviter_ids.add((inviter_id, inviter_type))
            
            # 一次性查询所有观众记录和邀请人记录
            with self.db_manager.get_session() as session:
                # 查询所有观众记录
                user_records = {}
                for user_id, user_type in all_user_ids:
                    viewer = session.query(LiveViewer).filter_by(
                        living_id=living_id, 
                        userid=user_id,
                        user_type=user_type
                    ).first()
                    if viewer:
                        key = f"{user_type}:{user_id}"
                        user_records[key] = viewer.id
                
                # 查询所有邀请人记录
                inviter_records = {}
                for inviter_id, inviter_type in all_inviter_ids:
                    # 检查是否是主播
                    if inviter_id == anchor_userid:
                        inviter_records[f"{inviter_type}:{inviter_id}"] = {
                            "userid": anchor_userid,
                            "name": anchor_name
                        }
                        continue
                        
                    # 尝试从预加载的用户模型中查找
                    user_info = self._cache["user_map"].get(inviter_id)
                    if user_info:
                        inviter_records[f"{inviter_type}:{inviter_id}"] = {
                            "userid": inviter_id,
                            "name": user_info["name"]
                        }
                        continue
                        
                    # 查询数据库
                    inviter = session.query(LiveViewer).filter_by(
                        living_id=living_id, 
                        userid=inviter_id,
                        user_type=int(inviter_type)
                    ).first()
                    
                    if inviter:
                        inviter_records[f"{inviter_type}:{inviter_id}"] = {
                            "userid": inviter.userid,
                            "name": inviter.name
                        }
                
                # 批量更新邀请关系
                for key, (inviter_id, inviter_type) in invitation_map.items():
                    user_id_key = key
                    inviter_key = f"{inviter_type}:{inviter_id}"
                    
                    if user_id_key in user_records:
                        user_record_id = user_records[user_id_key]
                        
                        # 获取邀请人信息
                        inviter_info = inviter_records.get(inviter_key)
                        if inviter_info:
                            inviter_userid = inviter_info["userid"]
                            inviter_name = inviter_info["name"]
                        else:
                            # 如果找不到邀请人，使用ID作为名称
                            inviter_userid = inviter_id
                            inviter_name = inviter_id
                        
                        # 检查是否是主播邀请
                        is_anchor_invitation = (inviter_id == anchor_userid)
                        
                        # 构建批量更新数据
                        batch_updates.append({
                            "id": user_record_id,
                            "invitor_userid": inviter_userid,
                            "invitor_name": inviter_name,
                            "is_anchor_invitation": is_anchor_invitation
                        })
                        update_count += 1
                        
                        # 达到批处理大小时执行批量更新
                        if len(batch_updates) >= MAX_BATCH_SIZE:
                            self._execute_batch_invitation_update(session, batch_updates)
                            logger.info(f"已批量更新 {len(batch_updates)} 条邀请关系")
                            batch_updates = []
                
                # 处理剩余的批次
                if batch_updates:
                    self._execute_batch_invitation_update(session, batch_updates)
                    logger.info(f"已批量更新剩余 {len(batch_updates)} 条邀请关系")
                
                duration = time.time() - start_time
                logger.info(f"邀请关系处理完成，更新了 {update_count} 条记录，耗时 {duration:.2f} 秒")
                
        except Exception as e:
            logger.error(f"处理邀请关系失败: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
    
    def _execute_batch_invitation_update(self, session, batch_updates):
        """执行批量邀请关系更新
        
        控制批量大小不超过1000条
        
        Args:
            session: 数据库会话
            batch_updates: 批量更新数据
        """
        if not batch_updates:
            return
        
        try:
            # 构建批量更新SQL
            values_str = ", ".join([
                f"({item['id']}, '{item['invitor_userid']}', '{item['invitor_name']}', {item['is_anchor_invitation']}, NOW())"
                for item in batch_updates
            ])
            
            # 检查LiveViewer表是否有is_invited_by_anchor字段
            has_anchor_field = False
            with self.db_manager.get_session() as check_session:
                result = check_session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'live_viewers' AND column_name = 'is_invited_by_anchor'"))
                has_anchor_field = result.fetchone() is not None
            
            # 根据字段是否存在构建不同的SQL
            if has_anchor_field:
                sql = f"""
                UPDATE live_viewers AS lv
                SET invitor_userid = v.invitor_userid, 
                    invitor_name = v.invitor_name,
                    is_invited_by_anchor = v.is_anchor_invitation,
                    updated_at = v.updated_at
                FROM (VALUES {values_str}) AS v(id, invitor_userid, invitor_name, is_anchor_invitation, updated_at)
                WHERE lv.id = v.id
                """
            else:
                sql = f"""
                UPDATE live_viewers AS lv
                SET invitor_userid = v.invitor_userid, 
                    invitor_name = v.invitor_name,
                    updated_at = v.updated_at
                FROM (VALUES {values_str}) AS v(id, invitor_userid, invitor_name, is_anchor_invitation, updated_at)
                WHERE lv.id = v.id
                """
            
            session.execute(text(sql))
            session.commit()
            
        except Exception as e:
            logger.error(f"执行批量邀请关系更新失败: {str(e)}")
            session.rollback()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self._stats
        
    def log_stats(self):
        """记录统计信息到日志"""
        stats = self.get_stats()
        logger.info("直播观众统计信息:")
        logger.info(f"总观众数: {stats['total_viewers']}")
        logger.info(f"内部观众: {stats['internal_viewers']}")
        logger.info(f"外部观众: {stats['external_viewers']}")
        logger.info(f"总签到数: {stats['sign_count']}")
        logger.info(f"成功处理的记录数: {stats['success_count']}")
        logger.info(f"处理失败的记录数: {stats['error_count']}")
        logger.info(f"已处理批次数: {stats['processed_batches']}")
        
        if stats.get("last_error"):
            logger.warning(f"最后一次错误: {stats['last_error']}")
            logger.warning(f"错误时间: {stats['last_error_time']}")
            
        if stats.get("last_sync_time"):
            logger.info(f"最后同步时间: {stats['last_sync_time']}")

    def get_viewer_statistics(self, living_id):
        """获取观看者统计信息
        
        Args:
            living_id: 直播ID
            
        Returns:
            dict: 统计信息
        """
        with self.db_manager.get_session() as session:
            try:
                # 使用聚合查询减少内存消耗
                stats = {}
                
                # 获取总观看人数
                stats["total_viewers"] = session.query(LiveViewer).filter_by(living_id=living_id).count()
                
                # 获取内部和外部观众数量
                internal_count = session.query(LiveViewer).filter_by(
                    living_id=living_id,
                    user_source=UserSource.INTERNAL
                ).count()
                
                external_count = session.query(LiveViewer).filter_by(
                    living_id=living_id,
                    user_source=UserSource.EXTERNAL
                ).count()
                
                stats["internal_viewers"] = internal_count
                stats["external_viewers"] = external_count
                
                # 获取平均观看时长
                avg_watch_time = session.query(func.avg(LiveViewer.watch_time)).filter_by(
                    living_id=living_id
                ).scalar() or 0
                
                stats["avg_watch_time"] = avg_watch_time
                
                # 获取评论和连麦人数
                comment_count = session.query(LiveViewer).filter_by(
                    living_id=living_id,
                    is_comment=1
                ).count()
                
                mic_count = session.query(LiveViewer).filter_by(
                    living_id=living_id,
                    is_mic=1
                ).count()
                
                stats["comment_count"] = comment_count
                stats["mic_count"] = mic_count
                
                # 获取签到相关统计
                signed_count = session.query(LiveViewer).filter_by(
                    living_id=living_id,
                    is_signed=True
                ).count()
                
                stats["signed_count"] = signed_count
                stats["sign_rate"] = (signed_count / stats["total_viewers"] * 100) if stats["total_viewers"] > 0 else 0
                
                # 获取奖励相关统计
                reward_eligible_count = session.query(LiveViewer).filter_by(
                    living_id=living_id,
                    is_reward_eligible=True
                ).count()
                
                reward_total_amount = session.query(func.sum(LiveViewer.reward_amount)).filter_by(
                    living_id=living_id
                ).scalar() or 0
                
                stats["reward_eligible_count"] = reward_eligible_count
                stats["reward_total_amount"] = reward_total_amount
                
                # 主播邀请人数
                if "is_invited_by_anchor" in LiveViewer.__table__.columns:
                    anchor_invited_count = session.query(LiveViewer).filter_by(
                        living_id=living_id,
                        is_invited_by_anchor=True
                    ).count()
                    stats["anchor_invited_count"] = anchor_invited_count
                
                return stats
                
            except Exception as e:
                logger.error(f"获取观看者统计信息失败: {str(e)}")
                return {}

    def _is_anchor_invitation(self, user_data: dict) -> bool:
        """检查邀请是否来自主播"""
        invitor = user_data.get('invitor_userid', '')
        # 获取直播信息
        with self.db_manager.get_session() as session:
            live_info = session.query(Living).filter_by(livingid=self.livingid).first()
            if not live_info:
                return False
            return invitor == live_info.anchor_userid 

    def _process_invitation_relationship(self):
        """处理邀请关系（内外互相邀请）"""
        try:
            with self.db_manager.get_session() as session:
                # 查询所有有邀请关系的观众
                viewers_with_invitor = session.query(LiveViewer).filter(
                    LiveViewer.living_id == self.livingid,
                    LiveViewer.invitor_userid.isnot(None),
                    LiveViewer.invitor_userid != ''
                ).all()
                
                # 处理邀请关系
                updated_count = 0
                for viewer in viewers_with_invitor:
                    invitor_id = viewer.invitor_userid
                    
                    # 根据用户类型查找邀请人
                    if viewer.user_type == 1:  # 内部用户
                        # 先在内部用户中查找
                        invitor = session.query(LiveViewer).filter_by(
                            living_id=self.livingid,
                            userid=invitor_id,
                            user_type=1
                        ).first()
                        
                        if not invitor:
                            # 再在外部用户中查找
                            invitor = session.query(LiveViewer).filter_by(
                                living_id=self.livingid,
                                userid=invitor_id,
                                user_type=2
                            ).first()
                    else:  # 外部用户
                        # 先在外部用户中查找
                        invitor = session.query(LiveViewer).filter_by(
                            living_id=self.livingid,
                            userid=invitor_id,
                            user_type=2
                        ).first()
                        
                        if not invitor:
                            # 再在内部用户中查找
                            invitor = session.query(LiveViewer).filter_by(
                                living_id=self.livingid,
                                userid=invitor_id,
                                user_type=1
                            ).first()
                    
                    # 如果找到邀请人，更新邀请人姓名
                    if invitor and not viewer.invitor_name:
                        viewer.invitor_name = invitor.name
                        updated_count += 1
                
                if updated_count > 0:
                    session.commit()
                    logger.info(f"已更新 {updated_count} 条邀请关系信息")
        except Exception as e:
            logger.error(f"处理邀请关系时出错: {str(e)}") 

    def _identify_inviter(self, user_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], bool]:
        """识别邀请人信息
        
        Args:
            user_data: 用户数据
            
        Returns:
            Tuple[Optional[str], Optional[str], bool]: (邀请人ID, 邀请人名称, 是否为主播邀请)
        """
        # 1. 检查是否有邀请人ID
        invitor_id = user_data.get('invitor_userid')
        if not invitor_id:
            return None, None, False
        
        # 2. 按优先级获取邀请人信息
        invitor_name = None
        
        # 2.1 检查是否为主播
        anchor_info = self._cache.get("anchor_info", {})
        if invitor_id == anchor_info.get("userid"):
            return invitor_id, anchor_info.get("name"), True
        
        # 2.2 检查当前直播数据库观看人员信息
        existing_viewers = self._cache.get("existing_viewers", {})
        if invitor_id in existing_viewers:
            viewer = existing_viewers[invitor_id]
            return invitor_id, viewer.name, False
        
        # 2.3 检查用户users模型
        user_map = self._cache.get("user_map", {})
        if invitor_id in user_map:
            return invitor_id, user_map[invitor_id]["name"], False
        
        # 2.4 检查当次API拉取的用户观看信息
        if invitor_id in user_data.get("name", ""):
            return invitor_id, user_data.get("name"), False
        
        # 2.5 尝试企微获取通讯录对比(仅1次尝试)
        if not self._cache.get("wecom_contact_tried"):
            try:
                # 调用企微API获取通讯录信息
                contact_info = self._get_wecom_contact(invitor_id)
                if contact_info:
                    return invitor_id, contact_info["name"], False
            except Exception as e:
                logger.warning(f"获取企微通讯录失败: {str(e)}")
            finally:
                self._cache["wecom_contact_tried"] = True
            
        # 3. 如果都找不到,使用ID作为名称
        return invitor_id, invitor_id, False 

    def _get_wecom_contact(self, userid: str) -> Optional[Dict[str, str]]:
        """从企业微信获取通讯录信息
        
        Args:
            userid: 用户ID
            
        Returns:
            Optional[Dict[str, str]]: 用户信息字典,包含name字段,如果获取失败则返回None
        """
        try:
            # 获取企业微信API实例
            from src.api.wecom import WeComAPI
            wecom_api = WeComAPI()
            
            # 尝试获取用户信息
            response = wecom_api.get_user_info(userid)
            if response.get("errcode") == 0:
                return {
                    "name": response.get("name", userid)
                }
            
            # 如果获取失败,尝试获取外部联系人信息
            response = wecom_api.get_external_contact(userid)
            if response.get("errcode") == 0:
                return {
                    "name": response.get("name", userid)
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"获取企业微信用户信息失败: {str(e)}")
            return None 