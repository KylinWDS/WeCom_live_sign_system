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
            # 尝试从多个国内服务获取IP
            services = [
                'https://whois.pconline.com.cn/ipJson.jsp',  # 太平洋电脑网
                'https://myip.ipip.net',  # ipip.net
                'https://ip.cn/api/index?ip=&type=0',  # ip.cn
                'https://ip.useragentinfo.com/json',  # useragentinfo
                'https://ip.taobao.com/service/getIpInfo.php?ip=myip'  # 淘宝IP库
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        if 'pconline.com.cn' in service:
                            # 太平洋电脑网返回的是GBK编码的JSONP
                            text = response.content.decode('gbk')
                            ip_match = re.search(r'"ip":"(\d+\.\d+\.\d+\.\d+)"', text)
                            if ip_match:
                                return ip_match.group(1)
                        elif 'ipip.net' in service:
                            # ipip.net返回的是HTML，需要提取IP
                            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', response.text)
                            if ip_match:
                                return ip_match.group(1)
                        elif 'ip.cn' in service:
                            # ip.cn返回JSON
                            data = response.json()
                            if data.get('code') == 0 and 'ip' in data:
                                return data['ip']
                        elif 'useragentinfo.com' in service:
                            # useragentinfo返回JSON
                            data = response.json()
                            if 'ip' in data:
                                return data['ip']
                        elif 'taobao.com' in service:
                            # 淘宝IP库返回JSON
                            data = response.json()
                            if data.get('code') == 0 and 'data' in data:
                                return data['data'].get('ip')
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