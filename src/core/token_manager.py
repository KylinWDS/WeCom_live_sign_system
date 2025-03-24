import time
from typing import Optional, Dict, Any
from src.utils.logger import get_logger
import requests
from datetime import datetime

logger = get_logger(__name__)

class TokenManager:
    """企业微信 access_token 管理器"""
    
    def __init__(self):
        self._access_token = None
        self._expires_at = None
        self._corpid = None
        self._corpsecret = None
        self._agent_id = None
        
        # 监控统计
        self._stats = {
            "total_requests": 0,  # 总请求次数
            "success_count": 0,   # 成功次数
            "error_count": 0,     # 失败次数
            "refresh_count": 0,   # 刷新次数
            "last_error": None,   # 最后一次错误
            "last_error_time": None,  # 最后一次错误时间
            "last_success_time": None,  # 最后一次成功时间
            "avg_response_time": 0,  # 平均响应时间
            "response_times": []  # 响应时间记录
        }
    
    def set_credentials(self, corpid: str, corpsecret: str, agent_id: str = None):
        """设置企业凭证
        
        Args:
            corpid: 企业ID
            corpsecret: 企业应用Secret
            agent_id: 应用ID，可选
        """
        self._corpid = corpid
        self._corpsecret = corpsecret
        self._agent_id = agent_id
        self._access_token = None
        self._expires_at = None
        
        # 重置统计
        self._stats = {
            "total_requests": 0,
            "success_count": 0,
            "error_count": 0,
            "refresh_count": 0,
            "last_error": None,
            "last_error_time": None,
            "last_success_time": None,
            "avg_response_time": 0,
            "response_times": []
        }
    
    def get_token(self) -> str:
        """获取 access_token
        
        Returns:
            str: access_token
            
        Raises:
            ValueError: 未设置企业凭证
            Exception: 获取 token 失败
        """
        start_time = time.time()
        
        try:
            # 检查凭证
            if not self._corpid or not self._corpsecret:
                raise ValueError("未设置企业凭证")
                
            # 更新请求计数
            self._stats["total_requests"] += 1
            
            # 检查 token 是否有效
            if self._access_token and self._expires_at and time.time() < self._expires_at:
                self._stats["success_count"] += 1
                self._stats["last_success_time"] = datetime.now()
                return self._access_token
                
            # 获取新 token
            self._stats["refresh_count"] += 1
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                "corpid": self._corpid,
                "corpsecret": self._corpsecret
            }
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get("errcode") == 0:
                self._access_token = result["access_token"]
                self._expires_at = time.time() + result["expires_in"] - 300  # 提前5分钟过期
                self._stats["success_count"] += 1
                self._stats["last_success_time"] = datetime.now()
                
                # 记录响应时间
                response_time = time.time() - start_time
                self._stats["response_times"].append(response_time)
                self._stats["avg_response_time"] = sum(self._stats["response_times"]) / len(self._stats["response_times"])
                
                return self._access_token
            else:
                error_msg = result.get("errmsg", "未知错误")
                self._stats["error_count"] += 1
                self._stats["last_error"] = error_msg
                self._stats["last_error_time"] = datetime.now()
                raise Exception(f"获取 token 失败: {error_msg}")
                
        except Exception as e:
            self._stats["error_count"] += 1
            self._stats["last_error"] = str(e)
            self._stats["last_error_time"] = datetime.now()
            logger.error(f"获取 access_token 失败: {str(e)}")
            raise
            
    def clear_token(self):
        """清除 access_token"""
        self._access_token = None
        self._expires_at = None
        
    def get_stats(self) -> dict:
        """获取统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            "total_requests": self._stats["total_requests"],
            "success_count": self._stats["success_count"],
            "error_count": self._stats["error_count"],
            "refresh_count": self._stats["refresh_count"],
            "success_rate": (self._stats["success_count"] / self._stats["total_requests"] * 100) if self._stats["total_requests"] > 0 else 0,
            "last_error": self._stats["last_error"],
            "last_error_time": self._stats["last_error_time"],
            "last_success_time": self._stats["last_success_time"],
            "avg_response_time": round(self._stats["avg_response_time"], 3),
            "token_status": {
                "has_token": bool(self._access_token),
                "expires_at": datetime.fromtimestamp(self._expires_at).strftime("%Y-%m-%d %H:%M:%S") if self._expires_at else None,
                "time_to_expire": round(self._expires_at - time.time(), 2) if self._expires_at else None
            }
        }
        
    def log_stats(self):
        """记录统计信息到日志"""
        stats = self.get_stats()
        logger.info("Token 管理统计信息:")
        logger.info(f"总请求次数: {stats['total_requests']}")
        logger.info(f"成功次数: {stats['success_count']}")
        logger.info(f"失败次数: {stats['error_count']}")
        logger.info(f"刷新次数: {stats['refresh_count']}")
        logger.info(f"成功率: {stats['success_rate']:.2f}%")
        logger.info(f"平均响应时间: {stats['avg_response_time']}秒")
        
        if stats["last_error"]:
            logger.warning(f"最后一次错误: {stats['last_error']}")
            logger.warning(f"错误时间: {stats['last_error_time']}")
            
        if stats["token_status"]["has_token"]:
            logger.info(f"Token 状态: 有效")
            logger.info(f"过期时间: {stats['token_status']['expires_at']}")
            logger.info(f"剩余时间: {stats['token_status']['time_to_expire']}秒")
        else:
            logger.warning("Token 状态: 无效")

    def get_agent_id(self) -> str:
        """获取应用ID
        
        Returns:
            str: 应用ID，如果未设置则返回None
        """
        return self._agent_id 