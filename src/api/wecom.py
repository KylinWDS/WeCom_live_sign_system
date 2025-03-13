import requests
from typing import Dict, Any, Optional
from src.utils.logger import get_logger
from src.core.token_manager import TokenManager
from src.utils.error_handler import ErrorHandler
from src.utils.performance_manager import PerformanceManager
import time
from datetime import datetime

logger = get_logger(__name__)

class WeComAPI:
    """企业微信API封装"""
    
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
    
    def __init__(self, corpid: str, corpsecret: str):
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.token_manager = TokenManager()
        self.token_manager.set_credentials(corpid, corpsecret)
        self.error_handler = ErrorHandler()
        self.performance_manager = PerformanceManager()
        
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
                   living_duration: int, type: int = 3, description: str = "") -> Dict[str, Any]:
        """创建直播
        
        Args:
            anchor_userid: 主播用户ID
            theme: 直播主题
            living_start: 直播开始时间戳
            living_duration: 直播时长(秒)
            type: 直播类型，默认3(企业培训)
            description: 直播描述
            
        Returns:
            Dict[str, Any]: 接口返回结果
        """
        try:
            data = {
                "anchor_userid": anchor_userid,
                "theme": theme,
                "living_start": living_start,
                "living_duration": living_duration,
                "type": type,
                "description": description,
                "agentid": self.token_manager.get_agent_id()
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
    
    def get_watch_stat(self, livingid: str, next_key: str = "") -> Dict[str, Any]:
        """获取直播观看明细"""
        try:
            data = {
                "livingid": livingid,
                "next_key": next_key
            }
            return self._make_request("POST", "living/get_watch_stat", data=data)
        except Exception as e:
            self.error_handler.handle_error(e, "获取直播观看明细")
            raise
    
    def cancel_living(self, livingid: str) -> Dict[str, Any]:
        """取消预约直播"""
        try:
            params = {"livingid": livingid}
            return self._make_request("POST", "living/cancel", params=params)
        except Exception as e:
            self.error_handler.handle_error(e, "取消预约直播")
            raise
    
    def test_connection(self) -> bool:
        """测试企业微信接口连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 获取 access_token
            token = self.access_token
            if not token:
                raise Exception("获取 access_token 失败")
                
            # 测试接口调用
            self._make_request("GET", "gettoken", {
                "corpid": self.corpid,
                "corpsecret": self.corpsecret
            })
            
            logger.info("企业微信接口连接测试成功")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "测试企业微信接口连接")
            raise 