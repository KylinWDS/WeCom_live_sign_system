from datetime import datetime
import requests
from sqlalchemy.orm import Session
from src.utils.logger import get_logger
from src.models.live_booking import LiveBooking
from src.models.live_viewer import LiveViewer
from src.models.invitor_cache import InvitorCache
from src.models.sign_record import SignRecord
from src.core.token_manager import TokenManager

logger = get_logger(__name__)

class LiveViewerManager:
    """直播观众管理器"""
    
    def __init__(self, db_manager, corpid: str, corpsecret: str):
        self.db_manager = db_manager
        self.token_manager = TokenManager()
        self.token_manager.set_credentials(corpid, corpsecret)
        
        # 统计信息
        self._stats = {
            "total_viewers": 0,
            "internal_viewers": 0,
            "external_viewers": 0,
            "total_signs": 0,
            "total_watch_time": 0,
            "last_error": None,
            "last_error_time": None,
            "last_sync_time": None
        }
        
    def get_invitor_name(self, living_id, viewer_id, invitor_id, stat_info):
        """获取邀请人名称
        
        Args:
            living_id: 直播ID
            viewer_id: 观看者ID
            invitor_id: 邀请人ID
            stat_info: 观看统计信息
            
        Returns:
            str: 邀请人名称
        """
        try:
            # 1. 从缓存中获取
            session = self.db_manager.get_session()
            try:
                cache = session.query(InvitorCache).filter_by(invitor_id=invitor_id).first()
                if cache:
                    return cache.name
            finally:
                session.close()
            
            # 2. 从观看统计中获取
            if stat_info and "users" in stat_info:
                for user in stat_info["users"]:
                    if user.get("userid") == invitor_id:
                        return user.get("name", "")
            
            # 3. 从外部用户统计中获取
            if stat_info and "external_users" in stat_info:
                for user in stat_info["external_users"]:
                    if user.get("external_userid") == invitor_id:
                        return user.get("name", "")
            
            # 4. 从数据库中的观看记录获取
            session = self.db_manager.get_session()
            try:
                viewer = session.query(LiveViewer).filter_by(
                    living_id=living_id,
                    viewer_id=viewer_id
                ).first()
                if viewer and viewer.invitor_name:
                    return viewer.invitor_name
            finally:
                session.close()
            
            # 5. 尝试从官方接口获取
            try:
                token = self.token_manager.get_token()
                if invitor_id.startswith("wmd"):  # 外部用户
                    url = f"https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get"
                    params = {
                        "access_token": token,
                        "external_userid": invitor_id
                    }
                else:  # 企业成员
                    url = f"https://qyapi.weixin.qq.com/cgi-bin/user/get"
                    params = {
                        "access_token": token,
                        "userid": invitor_id
                    }
                
                response = requests.get(url, params=params)
                result = response.json()
                
                if result["errcode"] == 0:
                    name = result.get("name", "")
                    # 更新缓存
                    self.update_invitor_cache(invitor_id, name)
                    return name
                    
            except Exception as e:
                logger.warning(f"获取邀请人信息失败: {str(e)}")
                # 记录权限问题
                if "errcode" in str(e) and "60020" in str(e):
                    logger.warning("需要开通相关权限以获取邀请人信息")
                
            return ""  # 如果都获取不到，返回空字符串
            
        except Exception as e:
            logger.error(f"获取邀请人名称失败: {str(e)}")
            return ""
            
    def get_live_info(self, living_id):
        """获取直播信息"""
        session = self.db_manager.get_session()
        try:
            return session.query(LiveBooking).filter_by(living_id=living_id).first()
        finally:
            session.close()
            
    def get_invitor_name_from_cache(self, invitor_id):
        """从缓存获取邀请人名称"""
        session = self.db_manager.get_session()
        try:
            cache = session.query(InvitorCache).filter_by(invitor_id=invitor_id).first()
            if cache:
                return cache.name
            return None
        finally:
            session.close()
            
    def update_invitor_cache(self, invitor_id, name):
        """更新邀请人名称缓存"""
        session = self.db_manager.get_session()
        try:
            cache = session.query(InvitorCache).filter_by(invitor_id=invitor_id).first()
            if cache:
                cache.name = name
                cache.updated_at = datetime.now()
            else:
                cache = InvitorCache(invitor_id=invitor_id, name=name)
                session.add(cache)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"更新邀请人缓存失败: {str(e)}")
        finally:
            session.close()
            
    def process_viewer_info(self, living_id):
        """处理观看者信息"""
        try:
            # 获取Token
            token = self.token_manager.get_token()
            
            # 获取直播观看明细
            url = "https://qyapi.weixin.qq.com/cgi-bin/living/get_watch_stat"
            params = {
                "access_token": token,
                "livingid": living_id,
                "next_key": ""
            }
            
            max_retries = 10  # 最大重试次数
            retry_count = 0
            
            while retry_count < max_retries:
                retry_count += 1
                try:
                    response = requests.post(url, json=params, timeout=30)  # 添加30秒超时
                    result = response.json()
                    
                    if result["errcode"] == 0:
                        # 处理企业成员观看记录
                        self.process_internal_users(result["stat_info"]["users"], living_id, result["stat_info"])
                        # 处理外部用户观看记录
                        self.process_external_users(result["stat_info"]["external_users"], living_id, result["stat_info"])
                        
                        if result["ending"] == 1:
                            break
                        params["next_key"] = result["next_key"]
                    else:
                        logger.error(f"获取观看明细失败: {result['errmsg']}")
                        if result["errcode"] in [40014, 42001]:  # token过期
                            token = self.token_manager.get_token(force_refresh=True)
                            params["access_token"] = token
                        else:
                            break
                except requests.Timeout:
                    logger.warning(f"请求超时，重试第{retry_count}次")
                    if retry_count >= max_retries:
                        raise Exception("获取观看明细超时")
                except requests.RequestException as e:
                    logger.error(f"请求异常: {str(e)}")
                    if retry_count >= max_retries:
                        raise
                    
        except Exception as e:
            logger.error(f"处理观看者信息失败: {str(e)}")
            raise
            
    def process_internal_users(self, users, living_id, stat_info):
        """处理企业成员观看记录"""
        session = self.db_manager.get_session()
        try:
            for user in users:
                # 获取邀请人名称
                invitor_name = self.get_invitor_name(
                    living_id=living_id,
                    viewer_id=user["userid"],
                    invitor_id=user.get("invitor_userid"),
                    stat_info=stat_info
                )
                
                # 计算观看时长占比
                live_info = self.get_live_info(living_id)
                total_duration = (live_info.end_time - live_info.start_time).total_seconds()
                watch_percentage = (user["watch_time"] / total_duration) * 100 if total_duration > 0 else 0
                
                viewer = LiveViewer(
                    living_id=living_id,
                    user_id=user["userid"],
                    user_type=1,  # 企业成员
                    first_enter_time=datetime.fromtimestamp(user.get("first_enter_time", 0)),
                    last_leave_time=datetime.fromtimestamp(user.get("last_leave_time", 0)),
                    total_watch_time=user["watch_time"],
                    watch_percentage=watch_percentage,
                    is_comment=user.get("is_comment", False),
                    comment_count=user.get("comment_count", 0),
                    is_mic=user.get("is_mic", False),
                    mic_duration=user.get("mic_duration", 0),
                    invitor_id=user.get("invitor_userid"),
                    invitor_name=invitor_name,
                    invitor_type=1  # 企业成员
                )
                session.add(viewer)
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    def process_external_users(self, users, living_id, stat_info):
        """处理外部用户观看记录"""
        session = self.db_manager.get_session()
        try:
            for user in users:
                # 获取邀请人名称
                invitor_name = self.get_invitor_name(
                    living_id=living_id,
                    viewer_id=user["external_userid"],
                    invitor_id=user.get("invitor_external_userid"),
                    stat_info=stat_info
                )
                
                # 计算观看时长占比
                live_info = self.get_live_info(living_id)
                total_duration = (live_info.end_time - live_info.start_time).total_seconds()
                watch_percentage = (user["watch_time"] / total_duration) * 100 if total_duration > 0 else 0
                
                viewer = LiveViewer(
                    living_id=living_id,
                    user_id=user["external_userid"],
                    user_name=user["name"],
                    user_type=2,  # 外部用户
                    first_enter_time=datetime.fromtimestamp(user.get("first_enter_time", 0)),
                    last_leave_time=datetime.fromtimestamp(user.get("last_leave_time", 0)),
                    total_watch_time=user["watch_time"],
                    watch_percentage=watch_percentage,
                    is_comment=user.get("is_comment", False),
                    comment_count=user.get("comment_count", 0),
                    is_mic=user.get("is_mic", False),
                    mic_duration=user.get("mic_duration", 0),
                    invitor_id=user.get("invitor_external_userid"),
                    invitor_name=invitor_name,
                    invitor_type=2  # 外部用户
                )
                session.add(viewer)
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    def update_sign_info(self, living_id):
        """更新观看者的签到信息
        
        Args:
            living_id: 直播ID
            
        Returns:
            tuple: (更新成功数量, 更新失败数量)
        """
        session = self.db_manager.get_session()
        try:
            success_count = 0
            error_count = 0
            
            # 获取所有签到记录
            sign_records = session.query(SignRecord).filter_by(living_id=living_id).all()
            
            # 获取所有观看记录
            viewers = session.query(LiveViewer).filter_by(living_id=living_id).all()
            
            # 创建用户ID到签到记录的映射
            sign_map = {record.user_id: record for record in sign_records}
            
            # 更新观看记录的签到信息
            for viewer in viewers:
                try:
                    if viewer.user_id in sign_map:
                        sign_record = sign_map[viewer.user_id]
                        viewer.is_signed = True
                        viewer.sign_time = sign_record.sign_time
                        viewer.department = sign_record.department
                        viewer.sign_count = sign_record.sign_count  # 添加签到次数
                        success_count += 1
                    else:
                        viewer.is_signed = False
                        viewer.sign_time = None
                        viewer.department = None
                        viewer.sign_count = 0  # 设置签到次数为0
                        success_count += 1
                except Exception as e:
                    logger.error(f"更新观看者 {viewer.user_id} 签到信息失败: {str(e)}")
                    error_count += 1
                    
            session.commit()
            return success_count, error_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"更新签到信息失败: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_viewer_statistics(self, living_id):
        """获取观看者统计信息
        
        Args:
            living_id: 直播ID
            
        Returns:
            dict: 统计信息
        """
        session = self.db_manager.get_session()
        try:
            viewers = session.query(LiveViewer).filter_by(living_id=living_id).all()
            
            stats = {
                "total_viewers": len(viewers),
                "internal_viewers": len([v for v in viewers if v.user_type == 1]),
                "external_viewers": len([v for v in viewers if v.user_type == 2]),
                "avg_watch_time": sum(v.total_watch_time for v in viewers) / len(viewers) if viewers else 0,
                "avg_watch_percentage": sum(v.watch_percentage for v in viewers) / len(viewers) if viewers else 0,
                "comment_count": sum(v.comment_count for v in viewers),
                "mic_count": len([v for v in viewers if v.is_mic]),
                # 添加签到相关统计
                "signed_count": len([v for v in viewers if v.is_signed]),
                "sign_rate": (len([v for v in viewers if v.is_signed]) / len(viewers) * 100) if viewers else 0,
                "total_sign_count": sum(v.sign_count for v in viewers),  # 总签到次数
                "avg_sign_count": sum(v.sign_count for v in viewers) / len(viewers) if viewers else 0  # 平均签到次数
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取观看者统计信息失败: {str(e)}")
            return {}
        finally:
            session.close()
            
    def get_stats(self) -> dict:
        """获取统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            "total_viewers": self._stats["total_viewers"],
            "internal_viewers": self._stats["internal_viewers"],
            "external_viewers": self._stats["external_viewers"],
            "total_signs": self._stats["total_signs"],
            "total_watch_time": self._stats["total_watch_time"],
            "last_error": self._stats["last_error"],
            "last_error_time": self._stats["last_error_time"],
            "last_sync_time": self._stats["last_sync_time"],
            "token_stats": self.token_manager.get_stats()
        }
        
    def log_stats(self):
        """记录统计信息到日志"""
        stats = self.get_stats()
        logger.info("直播观众统计信息:")
        logger.info(f"总观众数: {stats['total_viewers']}")
        logger.info(f"内部观众: {stats['internal_viewers']}")
        logger.info(f"外部观众: {stats['external_viewers']}")
        logger.info(f"总签到数: {stats['total_signs']}")
        logger.info(f"总观看时长: {stats['total_watch_time']}秒")
        
        if stats["last_error"]:
            logger.warning(f"最后一次错误: {stats['last_error']}")
            logger.warning(f"错误时间: {stats['last_error_time']}")
            
        if stats["last_sync_time"]:
            logger.info(f"最后同步时间: {stats['last_sync_time']}")
            
        # 记录 token 统计信息
        self.token_manager.log_stats() 