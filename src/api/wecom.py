import requests
from typing import Dict, Any, Optional
from ..utils.logger import get_logger
from ..core.token_manager import TokenManager
from ..utils.error_handler import ErrorHandler
from ..utils.performance_manager import PerformanceManager
import time
from datetime import datetime
import os

logger = get_logger(__name__)

class WeComAPI:
    """企业微信API封装"""
    
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
    
    def __init__(self, corpid: str, corpsecret: str, agent_id: str = None):
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agent_id = agent_id
        self.token_manager = TokenManager()
        self.token_manager.set_credentials(corpid, corpsecret, agent_id)
        self.error_handler = ErrorHandler()
        self.performance_manager = PerformanceManager()
        self._session = None
        
        # API 调用统计
        self._api_stats = {
            "total_calls": 0,
            "success_calls": 0,
            "error_calls": 0,
            "last_error": None,
            "last_error_time": None,
            "api_call_times": {}  # 各接口调用次数
        }
    
    @property
    def access_token(self) -> str:
        """获取access_token"""
        try:
            return self.token_manager.get_token()
        except Exception as e:
            self.error_handler.handle_error(e, "获取 access_token")
            raise
    
    @PerformanceManager.measure_operation("api_request")
    def _make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
        """发送 API 请求
        
        Args:
            method: 请求方法
            endpoint: 接口地址
            params: URL 参数
            data: 请求数据
            
        Returns:
            dict: 响应数据
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        start_time = time.time()
        
        try:
            # 更新统计
            self._api_stats["total_calls"] += 1
            self._api_stats["api_call_times"][endpoint] = self._api_stats["api_call_times"].get(endpoint, 0) + 1
            
            # 构建请求 URL
            url = f"{self.BASE_URL}/{endpoint}"
            if params is None:
                params = {}
            params["access_token"] = self.access_token
            
            # 发送请求
            if method.upper() == "GET":
                response = requests.get(url, params=params)
            else:
                response = requests.post(url, params=params, json=data)
                
            result = response.json()
            
            # 检查响应
            if result.get("errcode") == 0:
                self._api_stats["success_calls"] += 1
                return result
            else:
                error_msg = result.get("errmsg", "未知错误")
                self._api_stats["error_calls"] += 1
                self._api_stats["last_error"] = error_msg
                self._api_stats["last_error_time"] = datetime.now()
                
                # 记录错误日志
                logger.error(f"API 调用失败: {endpoint}")
                logger.error(f"错误信息: {error_msg}")
                logger.error(f"请求参数: {params}")
                if data:
                    logger.error(f"请求数据: {data}")
                
                # 处理特定的错误码
                error_code = result.get("errcode")
                if error_code == 60020 or "not allow to access from your ip" in error_msg:
                    raise Exception(f"API 调用失败: {error_msg}")
                else:    
                    raise Exception(f"API 调用失败: {error_msg}")
                
        except Exception as e:
            self._api_stats["error_calls"] += 1
            self._api_stats["last_error"] = str(e)
            self._api_stats["last_error_time"] = datetime.now()
            
            # 记录异常日志
            logger.error(f"API 请求异常: {endpoint}")
            logger.error(f"异常信息: {str(e)}")
            logger.error(f"请求参数: {params}")
            if data:
                logger.error(f"请求数据: {data}")
                
            raise
        finally:
            # 记录响应时间
            response_time = time.time() - start_time
            logger.debug(f"API 响应时间: {endpoint} - {response_time:.3f}秒")
            
    def get_session(self):
        """获取或创建requests会话，用于多次请求复用连接
        
        Returns:
            requests.Session: requests会话对象
        """
        if self._session is None:
            self._session = requests.Session()
        return self._session
    
    def get_api_stats(self) -> dict:
        """获取 API 调用统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            "total_calls": self._api_stats["total_calls"],
            "success_calls": self._api_stats["success_calls"],
            "error_calls": self._api_stats["error_calls"],
            "success_rate": (self._api_stats["success_calls"] / self._api_stats["total_calls"] * 100) if self._api_stats["total_calls"] > 0 else 0,
            "last_error": self._api_stats["last_error"],
            "last_error_time": self._api_stats["last_error_time"],
            "api_call_times": self._api_stats["api_call_times"],
            "token_stats": self.token_manager.get_stats()
        }
        
    def log_api_stats(self):
        """记录 API 调用统计信息到日志"""
        stats = self.get_api_stats()
        logger.info("API 调用统计信息:")
        logger.info(f"总调用次数: {stats['total_calls']}")
        logger.info(f"成功次数: {stats['success_calls']}")
        logger.info(f"失败次数: {stats['error_calls']}")
        logger.info(f"成功率: {stats['success_rate']:.2f}%")
        
        if stats["last_error"]:
            logger.warning(f"最后一次错误: {stats['last_error']}")
            logger.warning(f"错误时间: {stats['last_error_time']}")
            
        logger.info("各接口调用次数:")
        for endpoint, count in stats["api_call_times"].items():
            logger.info(f"- {endpoint}: {count}次")
            
        # 记录 token 统计信息
        self.token_manager.log_stats()
        
    def create_live(self, anchor_userid: str, theme: str, living_start: int, 
                   living_duration: int, type: int = 3, description: str = "", agentid = None) -> Dict[str, Any]:
        """创建直播
        
        Args:
            anchor_userid: 主播用户ID
            theme: 直播主题
            living_start: 直播开始时间戳
            living_duration: 直播时长(秒)
            type: 直播类型，默认3(企业培训)
            description: 直播描述
            agentid: 企业微信应用ID，如果不传则使用当前企业应用ID
            
        Returns:
            Dict[str, Any]: 接口返回结果
        """
        try:
            # 确定使用哪个应用ID，并确保是整数类型
            if agentid is not None:
                try:
                    actual_agentid = int(agentid)
                except (ValueError, TypeError):
                    logger.warning(f"传入的agentid '{agentid}'不是有效的整数，使用默认值")
                    actual_agentid = 1000002
            elif hasattr(self, 'agent_id') and self.agent_id:
                try:
                    actual_agentid = int(self.agent_id)
                except (ValueError, TypeError):
                    logger.warning(f"实例的agent_id '{self.agent_id}'不是有效的整数，使用默认值")
                    actual_agentid = 1000002
            else:
                actual_agentid = 1000002
            
            data = {
                "anchor_userid": anchor_userid,
                "theme": theme,
                "living_start": living_start,
                "living_duration": living_duration,
                "type": type,
                "description": description,
                "agentid": actual_agentid
            }
            
            result = self._make_request("POST", "living/create", data=data)
            
            if result["errcode"] == 0:
                logger.info(f"创建直播成功: {result['livingid']}")
                return result
            else:
                logger.error(f"创建直播失败: {result['errmsg']}")
                raise Exception(result["errmsg"])
                
        except Exception as e:
            self.error_handler.handle_error(e, "创建直播")
            raise
            
    def get_living_info(self, livingid: str) -> Dict[str, Any]:
        """获取直播详情"""
        try:
            params = {"livingid": livingid}
            return self._make_request("GET", "living/get_living_info", params=params)
        except Exception as e:
            self.error_handler.handle_error(e, "获取直播详情")
            raise
    
    def get_user_all_livingid(self, userid: str, cursor: str = "", limit: int = 20) -> Dict[str, Any]:
        """获取用户直播列表"""
        try:
            data = {
                "userid": userid,
                "cursor": cursor,
                "limit": limit
            }
            return self._make_request("POST", "living/get_user_all_livingid", data=data)
        except Exception as e:
            self.error_handler.handle_error(e, "获取用户直播列表")
            raise
    
    def get_watch_stat(self, livingid: str, next_key: str = '', data_type: int = 1, token: str = None) -> dict:
        """获取观看直播回放的详细信息
        
        参数:
            livingid: 直播ID
            next_key: 用于分页查询的key，首次请求可不填
            data_type: 数据类型，1表示观看直播数据，2表示观看回放数据
            token: 可选的访问令牌，如果提供则优先使用
            
        返回:
            dict: API响应
        """
        try:
            # 优先使用传入的token，其次使用token管理器的token
            access_token = token if token else self.token_manager.get_token()
            url = f"{self.BASE_URL}/living/get_watch_stat?access_token={access_token}"
            
            payload = {
                "livingid": livingid,
                "next_key": next_key,
                "data_type": data_type
            }
            
            logger.debug(f"发送API请求: {url} 参数: {payload}")
            response = requests.post(url, json=payload)
            result = response.json()
            
            if result.get("errcode") != 0:
                # 如果token过期，尝试刷新后重试
                if result.get("errcode") == 42001:
                    logger.warning("Token已过期，尝试刷新并重试...")
                    self.token_manager.refresh_token()
                    return self.get_watch_stat(livingid, next_key, data_type)
                
                logger.error(f"获取直播观看数据失败: {result}")
                return {"error": result.get("errmsg", "未知错误")}
            
            # 检查并标准化API返回结构
            if "stat_info" in result:
                # 处理返回数据，确保字段一致性
                stat_info = result.get("stat_info", {})
                
                # 确保有内部用户字段
                if "users" in stat_info and "user_list" not in stat_info:
                    stat_info["user_list"] = stat_info["users"]
                    
                # 确保有外部用户字段
                if "external_users" in stat_info and "external_user_list" not in stat_info:
                    stat_info["external_user_list"] = stat_info["external_users"]
                    
                # 更新结果
                result["stat_info"] = stat_info
            
            # 记录返回数据大小和结构信息
            external_users_count = len(result.get("stat_info", {}).get("external_users", []))
            internal_users_count = len(result.get("stat_info", {}).get("users", []))
            
            logger.info(f"获取到直播[{livingid}]观看数据: "
                      f"内部用户 {internal_users_count} 条, "
                      f"外部用户 {external_users_count} 条")
            
            return result
            
        except Exception as e:
            logger.error(f"获取直播观看数据异常: {str(e)}")
            return {"error": str(e)}
            
    def fetch_watch_stat_batch(self, livingid: str, next_key: str = None, data_type: int = 1, token: str = None):
        """批量获取直播观看数据（优化版）
        
        直接返回API原始响应，供多线程处理使用
        
        Args:
            livingid: 直播ID
            next_key: 下一页的key，首次请求可不填
            data_type: 数据类型，1表示观看直播数据，2表示观看回放数据
            token: 可选的访问令牌，如果提供则优先使用
            
        Returns:
            dict: API原始响应
        """
        try:
            logger.info(f"获取直播[{livingid}]观看数据，next_key=[{next_key}]")
            
            # 调用API获取数据
            response = self.get_watch_stat(livingid, next_key, data_type, token)
            
            # 记录API返回的原始数据结构，帮助诊断
            if not next_key:  # 只在第一页记录
                logger.info(f"API返回的数据结构: {list(response.keys())}")
            
            # 检查是否成功
            if "error" in response or response.get("errcode", 0) != 0:
                error_msg = response.get("error") or response.get("errmsg", "未知错误")
                logger.error(f"批量获取直播观看数据出错: {error_msg}")
                return {"error": error_msg, "errcode": response.get("errcode", -1)}
            
            # 直接返回原始响应
            return response
            
        except Exception as e:
            logger.error(f"批量获取直播观看数据异常: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return {"error": str(e), "errcode": -1}
    
    def cancel_living(self, livingid: str) -> Dict[str, Any]:
        """取消预约直播"""
        try:
            params = {"livingid": livingid}
            return self._make_request("POST", "living/cancel", params=params)
        except Exception as e:
            self.error_handler.handle_error(e, "取消预约直播")
            raise
    
    def test_connection(self, user_id: str = None) -> bool:
        """测试企业微信接口连接
        
        Args:
            user_id: 用户ID，用于测试获取用户直播列表接口
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 获取 access_token
            token = self.access_token
            if not token:
                raise Exception("获取 access_token 失败")
                
            # 基础测试接口调用
            self._make_request("GET", "gettoken", {
                "corpid": self.corpid,
                "corpsecret": self.corpsecret
            })
            
            # 如果提供了用户ID，测试获取用户直播列表接口
            if user_id:
                try:
                    self.get_user_all_livingid(user_id, "", 1)
                    logger.info(f"测试获取用户[{user_id}]直播列表成功")
                except Exception as e:
                    logger.error(f"测试获取用户[{user_id}]直播列表失败: {str(e)}")
                    raise Exception(f"获取用户直播列表失败: {str(e)}")
            
            logger.info("企业微信接口连接测试成功")
            return True
            
        except Exception as e:
            # 检查是否为IP白名单错误，如果是则通过错误处理器的handle_wecom_api_error方法处理
            if ErrorHandler.is_ip_whitelist_error(str(e)):
                # 此处不直接调用UI相关处理，仅记录错误
                logger.error(f"企业微信API连接测试失败，可能是IP白名单限制: {str(e)}")
            else:
                # 记录一般错误
                self.error_handler.handle_error(e, "测试企业微信接口连接")
            raise
    
    def get_user_info(self, userid: str) -> Dict[str, Any]:
        """获取用户信息
        
        Args:
            userid: 用户ID
            
        Returns:
            Dict[str, Any]: 用户信息
        """
        try:
            params = {"userid": userid}
            return self._make_request("GET", "user/get", params=params)
        except Exception as e:
            self.error_handler.handle_error(e, "获取用户信息")
            raise
            
    def get_external_contact(self, external_userid: str) -> Dict[str, Any]:
        """获取外部联系人信息
        
        Args:
            external_userid: 外部联系人ID
            
        Returns:
            Dict[str, Any]: 外部联系人信息
        """
        try:
            params = {"external_userid": external_userid}
            return self._make_request("GET", "externalcontact/get", params=params)
        except Exception as e:
            self.error_handler.handle_error(e, "获取外部联系人信息")
            raise
    