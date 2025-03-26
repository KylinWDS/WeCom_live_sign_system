import requests
import json
import re
from loguru import logger
import socket
from urllib.parse import urlparse
from typing import List, Dict, Optional, Tuple, Any
from src.utils.logger import get_logger
from src.core.database import DatabaseManager
from src.core.ip_record_manager import IPRecordManager
from src.app import get_app_context, ResourceNotInitializedError

logger = get_logger(__name__)

class NetworkUtils:
    """网络工具类"""
    
    @staticmethod
    def get_public_ip() -> str:
        """获取公网IP地址
        
        通过多个服务交叉验证获取最可靠的公网IP，同时将所有检测到的IP保存到数据库
        
        Returns:
            str: 公网IP地址，或者空字符串（如果获取失败）
        """
        try:
            # 调用可靠IP获取方法
            ip, details = NetworkUtils.get_reliable_public_ip()
            
            # 如果获取失败，返回空字符串
            if not ip or details.get('status') != 'success':
                logger.error("获取公网IP失败")
                return ''
                
            # 保存IP到数据库
            try:
                # 获取应用上下文中的数据库管理器实例
                app_context = get_app_context()
                if app_context:
                    try:
                        db_manager = app_context.db_manager
                        
                        # 确认数据库已初始化
                        if db_manager.initialized:
                            with db_manager.get_session() as session:
                                ip_manager = IPRecordManager(session)
                                
                                # 保存最可靠的IP为manual类型
                                if ip and isinstance(ip, str):
                                    ip_manager.add_ip(ip, 'manual')
                                    logger.info(f"将最可靠IP [{ip}] 添加到数据库 (类型: manual)")
                                
                                # 获取并保存其他检测到的IP
                                all_ips = details.get('all_ips', {})
                                if all_ips and isinstance(all_ips, dict):
                                    for detected_ip, count in all_ips.items():
                                        if detected_ip != ip:  # 跳过已添加为manual的IP
                                            try:
                                                if detected_ip and isinstance(detected_ip, str):
                                                    ip_manager.add_ip(detected_ip, 'history')
                                                    logger.info(f"将探测到的其他IP [{detected_ip}] 添加到数据库 (类型: history)")
                                            except Exception as inner_e:
                                                logger.warning(f"添加IP [{detected_ip}] 到数据库失败: {str(inner_e)}")
                        else:
                            logger.error("数据库管理器未初始化")
                    except ResourceNotInitializedError:
                        logger.error("数据库管理器尚未初始化")
                else:
                    logger.error("无法获取应用上下文")
            except Exception as e:
                logger.error(f"保存IP到数据库失败: {str(e)}")
            
            return ip
        except Exception as e:
            logger.error(f"获取公网IP失败: {str(e)}")
            return ''
    
    @staticmethod
    def get_reliable_public_ip() -> Tuple[str, Dict[str, Any]]:
        """获取最可靠的公网IP地址，通过多个服务交叉验证
        
        Returns:
            Tuple[str, Dict[str, Any]]: (最可靠的IP地址, 附加信息)
            附加信息包含：信任度、所有收集到的IP、地理位置信息等
        """
        ip_results = {}
        ip_details = {}
        geo_info = {}
        
        try:
            # 定义服务列表，按可靠性排序
            services = [
                # 国内服务
                ('https://whois.pconline.com.cn/ipJson.jsp', 'pconline'),   # 太平洋电脑网，含地理位置
                ('https://myip.ipip.net', 'ipip'),                           # IPIP.NET，含地理位置
                ('https://qifu-api.baidubce.com/ip/local/geo/v1/district', 'baiduce'),  # 百度地理位置
                ('https://ip.useragentinfo.com/json', 'useragentinfo'),      # User Agent Info，含地理位置
                ('https://qifu.baidu.com/ip/local/geo/v1/district', 'baidu'),# 百度地理位置
                # 国际服务作为备选
                ('https://httpbin.org/ip', 'httpbin'),                       # httpbin
            ]
            
            # 尝试所有服务
            for service_url, service_id in services:
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'}
                    response = requests.get(service_url, headers=headers, timeout=3)
                    
                    if response.status_code != 200:
                        continue
                        
                    content = response.text
                    ip = None
                    
                    # 根据不同服务解析IP和地理位置
                    if service_id == 'pconline':
                        match = re.search(r'\"ip\":\"([^\"]+)\"', content)
                        if match:
                            ip = match.group(1)
                        # 提取地理位置
                        pro_match = re.search(r'\"pro\":\"([^\"]+)\"', content)
                        city_match = re.search(r'\"city\":\"([^\"]+)\"', content)
                        if pro_match and city_match:
                            geo_info[service_id] = {
                                'province': pro_match.group(1),
                                'city': city_match.group(1)
                            }
                    elif service_id == 'ipip':
                        match = re.search(r'当前 IP：([\d\.]+).*来自于：([^<]+)', content, re.DOTALL)
                        if match:
                            ip = match.group(1)
                            location = match.group(2).strip()
                            geo_info[service_id] = {'location': location}
                    elif service_id in ['baiduce', 'baidu']:
                        try:
                            data = json.loads(content)
                            if 'ip' in data:
                                ip = data['ip']
                            else:
                                ip = data.get('data', {}).get('ip')
                            
                            # 提取地理位置
                            if 'data' in data and isinstance(data['data'], dict):
                                geo_data = data['data']
                                geo_info[service_id] = {
                                    'country': geo_data.get('country'),
                                    'province': geo_data.get('prov'),
                                    'city': geo_data.get('city')
                                }
                        except:
                            pass
                    elif service_id == 'useragentinfo':
                        try:
                            data = json.loads(content)
                            ip = data.get('ip')
                            # 提取地理位置
                            geo_info[service_id] = {
                                'country': data.get('country'),
                                'province': data.get('province'),
                                'city': data.get('city'),
                                'isp': data.get('isp')
                            }
                        except:
                            pass
                    elif service_id == 'httpbin':
                        try:
                            data = json.loads(content)
                            ip = data.get('origin')
                        except:
                            pass
                    
                    if ip:
                        logger.debug(f"从 {service_id} 获取到IP: {ip}")
                        ip_results[service_id] = ip
                        
                        # 保存详细信息
                        ip_details[service_id] = {
                            'ip': ip,
                            'service': service_url,
                            'geo': geo_info.get(service_id, {})
                        }
                except Exception as e:
                    logger.warning(f"从 {service_id} 获取IP失败: {str(e)}")
                    continue
            
            # 分析结果，找出最可靠的IP
            if not ip_results:
                logger.error("所有服务都未能成功获取IP")
                return '', {'status': 'error', 'message': '无法获取公网IP'}
            
            # 统计各IP出现次数
            ip_counts = {}
            for ip in ip_results.values():
                ip_counts[ip] = ip_counts.get(ip, 0) + 1
            
            # 获取出现次数最多的IP
            most_common_ip, count = max(ip_counts.items(), key=lambda x: x[1])
            confidence = min(count / len(services) * 100, 100)  # 计算可信度
            
            # 收集最终结果
            result_info = {
                'status': 'success',
                'ip': most_common_ip,
                'confidence': confidence,
                'source_count': count,
                'total_sources': len(ip_results),
                'all_ips': ip_counts,
                'details': ip_details,
                'is_consistent': len(ip_counts) == 1,  # 是否所有服务返回一致结果
                'geo': {}  # 合并地理位置信息
            }
            
            # 合并地理位置信息，优先使用高可靠性服务的信息
            for service_id in ['pconline', 'ipip', 'useragentinfo', 'baiduce', 'baidu']:
                if service_id in geo_info and geo_info[service_id]:
                    # 检查此服务返回的IP是否与最终选择的IP一致
                    if service_id in ip_results and ip_results[service_id] == most_common_ip:
                        result_info['geo'].update(geo_info[service_id])
            
            logger.info(f"最可靠的公网IP: {most_common_ip} (可信度: {confidence:.1f}%)")
            return most_common_ip, result_info
            
        except Exception as e:
            logger.error(f"获取可靠公网IP失败: {str(e)}")
            return '', {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def extract_ip_from_error(error_message: str) -> Optional[str]:
        """从错误消息中提取IP地址
        
        Args:
            error_message: 错误消息
            
        Returns:
            Optional[str]: IP地址，如果没有找到则返回None
        """
        # 尝试从错误消息中提取IP地址
        ip_pattern = r'from ip: ([\d\.]+)'
        match = re.search(ip_pattern, error_message)
        if match:
            return match.group(1)
        
        # 通用IP提取模式
        general_ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        match = re.search(general_ip_pattern, error_message)
        if match:
            return match.group(0)
            
        return None
        
    @staticmethod
    def is_port_open(host: str, port: int, timeout: int = 2) -> bool:
        """检查主机端口是否开放
        
        Args:
            host: 主机地址
            port: 端口号
            timeout: 超时时间（秒）
            
        Returns:
            bool: 端口是否开放
        """
        try:
            socket.setdefaulttimeout(timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = s.connect_ex((host, port))
            s.close()
            return result == 0
        except Exception as e:
            logger.error(f"检查端口 {host}:{port} 时发生错误: {str(e)}")
            return False
    
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