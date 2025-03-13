import requests
import re
from typing import Optional, List
from src.utils.logger import get_logger

logger = get_logger(__name__)

class NetworkUtils:
    """网络工具类"""
    
    @staticmethod
    def get_public_ip() -> Optional[str]:
        """获取本机公网IP
        
        Returns:
            Optional[str]: 公网IP地址，如果获取失败则返回None
        """
        try:
            # 尝试从多个服务获取IP
            services = [
                'https://api.ipify.org?format=json',
                'https://api.myip.com',
                'https://ip.seeip.org/json'
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'ip' in data:
                            return data['ip']
                except:
                    continue
            
            logger.warning("无法从任何服务获取公网IP")
            return None
            
        except Exception as e:
            logger.error(f"获取公网IP失败: {str(e)}")
            return None
    
    @staticmethod
    def extract_ip_from_error(error_msg: str) -> Optional[str]:
        """从错误消息中提取IP地址
        
        Args:
            error_msg: 错误消息
            
        Returns:
            Optional[str]: IP地址，如果未找到则返回None
        """
        try:
            ip_match = re.search(r'from ip: (\d+\.\d+\.\d+\.\d+)', error_msg)
            if ip_match:
                return ip_match.group(1)
            return None
        except Exception as e:
            logger.error(f"从错误消息提取IP失败: {str(e)}")
            return None
    
    @staticmethod
    def format_ip_list(ips: List[str]) -> str:
        """格式化IP列表为分号分隔的字符串
        
        Args:
            ips: IP地址列表
            
        Returns:
            str: 格式化后的IP列表
        """
        return ';'.join(ips)
    
    @staticmethod
    def parse_ip_list(ip_str: str) -> List[str]:
        """解析分号分隔的IP列表
        
        Args:
            ip_str: IP列表字符串
            
        Returns:
            List[str]: IP地址列表
        """
        return [ip.strip() for ip in ip_str.split(';') if ip.strip()] 