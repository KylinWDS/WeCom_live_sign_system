from typing import List
from src.utils.network import NetworkUtils
from src.core.ip_record_manager import IPRecordManager
import logging

logger = logging.getLogger(__name__)

class IPSuggestion:
    """IP地址建议工具类"""

    def __init__(self, ip_record_manager: IPRecordManager):
        self.ip_record_manager = ip_record_manager

    def suggest_ips(self, current_ip: str, num_suggestions: int = 5) -> List[str]:
        """基于当前IP地址，建议可能的IP地址，优化推算算法
        
        Args:
            current_ip: 当前的公网IP地址
            num_suggestions: 需要建议的IP地址数量
        
        Returns:
            List[str]: 可能的IP地址列表
        """
        # 分析当前IP地址的前缀
        ip_parts = current_ip.split('.')
        if len(ip_parts) != 4:
            return []

        # 假设IP地址的前三部分不变，最后一部分变化
        base_ip = '.'.join(ip_parts[:3])
        suggestions = []

        # 获取历史IP记录
        historical_ips = self.ip_record_manager.get_all_ips()
        historical_last_octets = [int(ip.split('.')[3]) for ip in historical_ips if ip.startswith(base_ip)]

        # 计算历史IP的最后一部分的平均值和标准差
        if historical_last_octets:
            avg_last_octet = sum(historical_last_octets) / len(historical_last_octets)
            std_dev_last_octet = (sum((x - avg_last_octet) ** 2 for x in historical_last_octets) / len(historical_last_octets)) ** 0.5
        else:
            avg_last_octet = int(ip_parts[3])
            std_dev_last_octet = 10  # 默认标准差

        # 生成可能的IP地址，基于平均值和标准差
        for i in range(num_suggestions):
            suggested_last_octet = int(avg_last_octet + std_dev_last_octet * ((-1) ** i) * (i // 2 + 1)) % 256
            suggested_ip = f"{base_ip}.{suggested_last_octet}"
            if suggested_ip not in historical_ips:
                suggestions.append(suggested_ip)

        return suggestions

    def generate_and_save_ips(self, num_ips: int = 100) -> List[str]:
        """生成并保存IP地址列表，优先使用真实IP地址
        
        Args:
            num_ips: 需要生成的IP地址总数
        
        Returns:
            List[str]: 生成的IP地址列表
        """
        # 获取当前公网IP
        current_ip = NetworkUtils.get_public_ip()
        if not current_ip:
            logger.error("无法获取当前公网IP")
            return []

        # 获取历史IP记录
        historical_ips = self.ip_record_manager.get_all_ips()

        # 初始化IP地址列表
        ip_list = [current_ip] + historical_ips

        # 如果IP数量不足，使用推算方法补充
        if len(ip_list) < num_ips:
            num_suggestions = num_ips - len(ip_list)
            suggested_ips = self.suggest_ips(current_ip, num_suggestions)
            ip_list.extend(suggested_ips)

        # 截取前num_ips个IP地址
        ip_list = ip_list[:num_ips]

        # 保存IP地址到数据库
        for ip in ip_list:
            source = 'real' if ip in historical_ips or ip == current_ip else 'predicted'
            self.ip_record_manager.add_ip(ip, source)

        return ip_list

# 示例用法
if __name__ == "__main__":
    # 假设我们有一个IPRecordManager实例
    ip_record_manager = IPRecordManager(None)  # 这里需要传入实际的Session对象
    ip_suggestion = IPSuggestion(ip_record_manager)
    generated_ips = ip_suggestion.generate_and_save_ips()
    print("生成的IP地址:", generated_ips) 