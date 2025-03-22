from typing import List
from src.utils.network import NetworkUtils
from src.core.ip_record_manager import IPRecordManager
import logging
import random

logger = logging.getLogger(__name__)

class IPSuggestion:
    """IP地址建议工具类"""

    def __init__(self, ip_record_manager: IPRecordManager):
        self.ip_record_manager = ip_record_manager

    def suggest_ips(self, base_ip: str, num_suggestions: int = 10, offset_base: int = 11) -> List[str]:
        """基于基准IP地址，智能推测可能的IP地址
        
        Args:
            base_ip: 基准IP地址（公网IP）
            num_suggestions: 需要建议的IP地址数量
            offset_base: IP范围偏移基数，默认11（3种类型*2个网段+5）
        
        Returns:
            List[str]: 可能的IP地址列表
        """
        if not self._is_valid_ip(base_ip):
            return []

        # 计算各部分的IP数量
        original_segment_count = int(num_suggestions * 0.7)  # 70%给原有网段
        other_segment_count = num_suggestions - original_segment_count  # 30%给其他网段

        ip_parts = base_ip.split('.')
        first_octet = int(ip_parts[0])
        prefix = '.'.join(ip_parts[:3])  # 当前C段前缀
        current_last = int(ip_parts[3])  # 当前IP最后一段
        suggestions = []
        used_octets = set()

        # 获取当前IP所在的服务器段
        current_range = self._get_server_range(current_last)
        
        # 1. 在原有网段生成IP (70%)
        # 1.1 优先在当前C段内相同用途段生成IP
        if current_range:
            start, end = current_range
            for last in range(start, end + 1):
                if last != current_last and last not in used_octets:
                    new_ip = f"{prefix}.{last}"
                    suggestions.append(new_ip)
                    used_octets.add(last)
                    if len(suggestions) >= original_segment_count:
                        break

        # 1.2 在当前C段内生成临近值
        if len(suggestions) < original_segment_count:
            # 计算数据库中的类型数量和网段数量

            
            # 计算合理的偏移范围
            min_offset = max(-offset_base, 1 - current_last)  # 确保最小值不小于1
            max_offset = min(offset_base, 254 - current_last)  # 确保最大值不超过254
            
            for offset in range(min_offset, max_offset + 1):
                if offset == 0:  # 跳过当前IP
                    continue
                new_last = current_last + offset
                if new_last not in used_octets:
                    new_ip = f"{prefix}.{new_last}"
                    suggestions.append(new_ip)
                    used_octets.add(new_last)
                    if len(suggestions) >= original_segment_count:
                        break

        # 1.3 如果是B类地址，考虑相邻C段
        if len(suggestions) < original_segment_count and 128 <= first_octet <= 191:
            third_octet = int(ip_parts[2])
            subnet_prefix = '.'.join(ip_parts[:2])
            
            # 检查相邻的C段
            for third in [third_octet - 1, third_octet + 1]:
                if 0 <= third <= 255:
                    # 在相邻C段使用相同的服务器段
                    if current_range:
                        start, end = current_range
                        for last in range(start, end + 1):
                            if last not in used_octets:
                                new_ip = f"{subnet_prefix}.{third}.{last}"
                                suggestions.append(new_ip)
                                used_octets.add(last)
                                if len(suggestions) >= original_segment_count:
                                    break
                    if len(suggestions) >= original_segment_count:
                        break

        # 2. 生成其他网段的IP (30%)
        if other_segment_count > 0:
            # 2.1 使用其他服务器段
            other_suggestions = []
            for range_start, range_end in self._get_all_server_ranges():
                if (range_start, range_end) != current_range:
                    for last in range(range_start, range_end + 1):
                        if last not in used_octets:
                            new_ip = f"{prefix}.{last}"
                            other_suggestions.append(new_ip)
                            used_octets.add(last)
                            if len(other_suggestions) >= other_segment_count:
                                break
                    if len(other_suggestions) >= other_segment_count:
                        break
            
            # 2.2 如果其他服务器段的IP不足，使用随机生成的合法IP
            while len(other_suggestions) < other_segment_count:
                last = random.randint(1, 254)
                if last not in used_octets:
                    new_ip = f"{prefix}.{last}"
                    other_suggestions.append(new_ip)
                    used_octets.add(last)

            # 将其他网段的建议添加到主建议列表
            suggestions.extend(other_suggestions)

        return suggestions[:num_suggestions]

    def _get_server_range(self, last_octet: int) -> tuple:
        """获取IP最后一段所属的服务器段范围
        
        Args:
            last_octet: IP最后一段数字
            
        Returns:
            tuple: (start, end) 服务器段范围，如果不在任何预定义段内返回None
        """
        SERVER_RANGES = [
            (1, 20),      # 网关、核心设备段
            (50, 100),    # 主要服务器段
            (200, 254)    # 备用服务器段
        ]
        
        for start, end in SERVER_RANGES:
            if start <= last_octet <= end:
                return (start, end)
        return None

    def _get_all_server_ranges(self) -> List[tuple]:
        """获取所有预定义的服务器段范围
        
        Returns:
            List[tuple]: 服务器段范围列表
        """
        return [
            (1, 20),      # 网关、核心设备段
            (50, 100),    # 主要服务器段
            (200, 254)    # 备用服务器段
        ]

    def generate_and_save_ips(self, num_ips: int = 100, session = None) -> List[str]:
        """生成IP地址列表
        
        Args:
            num_ips: 需要生成的IP地址总数，默认100个
            session: 数据库会话，如果为None则创建新会话
        
        Returns:
            List[str]: 生成的IP地址列表
        """
        # 获取当前公网IP
        current_ip = NetworkUtils.get_public_ip()
        if not current_ip:
            logger.error("无法获取当前公网IP")
            return []
        
        # 使用提供的session或创建新session
        if session:
            return self._generate_and_save_ips_internal(session, current_ip, num_ips)
        else:
            with self.ip_record_manager.get_session() as session:
                return self._generate_and_save_ips_internal(session, current_ip, num_ips)

    def _generate_and_save_ips_internal(self, session, current_ip: str, num_ips: int) -> List[str]:
        """内部方法：生成和保存IP地址列表
        
        Args:
            session: 数据库会话
            current_ip: 当前IP
            num_ips: 需要生成的IP地址总数
        
        Returns:
            List[str]: 生成的IP地址列表
        """
        from src.models.ip_record import IPRecord
        
        # 1. 收集基础数据（按优先级顺序）
        source_ips = {
            'current': [],
            'manual': [],
            'error': [],
            'history': []
        }
        
        # 1.1 添加当前IP
        if current_ip:
            source_ips['current'].append(current_ip)
            
        # 1.2 获取各类型的活跃IP
        for source in ['manual', 'error', 'history']:
            active_ips = session.query(IPRecord).filter_by(
                source=source,
                is_active=True
            ).all()
            source_ips[source].extend([ip.ip for ip in active_ips])

        # 1.3 尝试仅使用基础IP（current, manual, error）
        final_ip_list = []
        seen_ips = set()
        saved_ips = set()  # 用于跟踪已保存到数据库的IP
        
        # 添加基础IP（按优先级：current, manual, error）
        for source_type in ['current', 'manual', 'error']:
            for ip in source_ips[source_type]:
                if ip not in seen_ips:
                    final_ip_list.append(ip)
                    seen_ips.add(ip)
                    saved_ips.add(ip)  # 基础IP已经存在于数据库中
        
        # 如果基础IP数量已经满足要求，直接返回
        if len(final_ip_list) >= num_ips:
            return final_ip_list[:num_ips]

        # 2. 清理旧数据
        # 2.1 将所有旧的推测数据置为无效
        session.query(IPRecord).filter_by(
            source='infer',
            is_active=True
        ).update({'is_active': False})
        
        # 2.2 检查并清理过多的无效推测数据
        inactive_infer_count = session.query(IPRecord).filter_by(
            source='infer',
            is_active=False
        ).count()
        
        if inactive_infer_count > 1000:
            old_records = session.query(IPRecord).filter_by(
                source='infer',
                is_active=False
            ).order_by(
                IPRecord.updated_at.asc()
            ).limit(900).all()
            
            if old_records:
                old_record_ids = [record.id for record in old_records]
                session.query(IPRecord).filter(
                    IPRecord.id.in_(old_record_ids)
                ).delete(synchronize_session=False)

        # 3. 添加history类型的IP
        for ip in source_ips['history']:
            if ip not in seen_ips:
                final_ip_list.append(ip)
                seen_ips.add(ip)
                saved_ips.add(ip)  # history IP已经存在于数据库中
        if len(final_ip_list) >= num_ips:
            return final_ip_list[:num_ips]
        
        # 4. 为每种类型生成并保存推荐IP
        source_suggestions = {}  # 存储每个源类型的推荐IP
        
        # 获取所有不同的前3位网段
        prefix_set = set()
        for source_type in ['current', 'manual', 'error', 'history']:
            for ip in source_ips[source_type]:
                prefix = '.'.join(ip.split('.')[:3])
                prefix_set.add(prefix)
        
        # 如果没有找到任何网段，使用当前IP的网段
        if not prefix_set and current_ip:
            prefix_set.add('.'.join(current_ip.split('.')[:3]))
        
        # 第一轮：为每种类型的每个前3位网段生成更多建议
        for source_type in ['current', 'manual', 'error', 'history']:
            if not source_ips[source_type]:
                continue
                
            source_suggestions[source_type] = []
            
            # 对每个前3位网段生成建议
            for prefix in prefix_set:
                suggestions_count = 0
                
                # 找到该类型中属于这个网段的基础IP
                base_ips_in_prefix = [ip for ip in source_ips[source_type] if '.'.join(ip.split('.')[:3]) == prefix]
                if not base_ips_in_prefix:
                    continue
                
                # 计算实际的offset_base，增加生成范围
                type_count = len([t for t in ['current', 'manual', 'error', 'history'] if source_ips[t]])
                prefix_count = len(prefix_set) if prefix_set else 1
                actual_offset_base = type_count * prefix_count * 2 + 10  # 增加生成范围

                # 确保每个类型每个网段生成更多推荐
                max_attempts = 100  # 增加最大尝试次数
                attempts = 0
                while suggestions_count < 20 and attempts < max_attempts:  # 增加每个网段的生成数量
                    attempts += 1
                    for base_ip in base_ips_in_prefix:
                        if suggestions_count >= 20:  # 增加每个网段的生成数量
                            break
                            
                        suggestions = self.suggest_ips(base_ip, 20 - suggestions_count, actual_offset_base)  # 增加每次生成的数量
                        for suggested_ip in suggestions:
                            if suggested_ip not in seen_ips and '.'.join(suggested_ip.split('.')[:3]) == prefix:
                                source_suggestions[source_type].append(suggested_ip)
                                seen_ips.add(suggested_ip)
                                final_ip_list.append(suggested_ip)
                                suggestions_count += 1
                                if suggestions_count >= 20:  # 增加每个网段的生成数量
                                    break
                
                if suggestions_count < 20:  # 增加每个网段的生成数量
                    logger.warning(f"无法为类型 {source_type} 在网段 {prefix} 生成足够的推荐IP")

            # 保存该类型的推荐IP到数据库（去重）
            for suggested_ip in source_suggestions[source_type]:
                if suggested_ip not in saved_ips:
                    self.ip_record_manager.add_ip(suggested_ip, 'infer')
                    saved_ips.add(suggested_ip)

        # 如果用户需要更多IP，生成额外的IP（但不保存到数据库）
        remaining_count = num_ips - len(final_ip_list)
        if remaining_count > 0:
            # 继续使用每个类型的基础IP生成更多建议
            for source_type in ['current', 'manual', 'error', 'history']:
                if not source_ips[source_type] or remaining_count <= 0:
                    continue
                    
                # 对每个前3位网段继续生成
                for prefix in prefix_set:
                    if remaining_count <= 0:
                        break
                        
                    base_ips_in_prefix = [ip for ip in source_ips[source_type] if '.'.join(ip.split('.')[:3]) == prefix]
                    if not base_ips_in_prefix:
                        continue
                    
                    for base_ip in base_ips_in_prefix:
                        if remaining_count <= 0:
                            break
                            
                        # 生成额外的建议IP（不保存到数据库）
                        # 计算实际的offset_base，增加生成范围
                        type_count = len([t for t in ['current', 'manual', 'error', 'history'] if source_ips[t]])
                        prefix_count = len(prefix_set) if prefix_set else 1
                        actual_offset_base = type_count * prefix_count * 2 + 10  # 增加生成范围
                        
                        additional_suggestions = self.suggest_ips(base_ip, remaining_count, actual_offset_base)
                        for suggested_ip in additional_suggestions:
                            if suggested_ip not in seen_ips and '.'.join(suggested_ip.split('.')[:3]) == prefix:
                                final_ip_list.append(suggested_ip)
                                seen_ips.add(suggested_ip)
                                # 保存到数据库（去重）
                                if suggested_ip not in saved_ips:
                                    self.ip_record_manager.add_ip(suggested_ip, 'infer')
                                    saved_ips.add(suggested_ip)
                                remaining_count -= 1
                                if remaining_count <= 0:
                                    break

        # 如果仍然需要更多IP，使用随机生成
        if len(final_ip_list) < num_ips:
            remaining = num_ips - len(final_ip_list)
            for prefix in prefix_set:
                if remaining <= 0:
                    break
                for _ in range(remaining):
                    last = random.randint(1, 254)
                    new_ip = f"{prefix}.{last}"
                    if new_ip not in seen_ips:
                        final_ip_list.append(new_ip)
                        seen_ips.add(new_ip)
                        # 保存到数据库（去重）
                        if new_ip not in saved_ips:
                            self.ip_record_manager.add_ip(new_ip, 'infer')
                            saved_ips.add(new_ip)
                        remaining -= 1
                        if remaining <= 0:
                            break

        # 确保返回的IP列表不重复且数量正确
        return list(dict.fromkeys(final_ip_list))[:num_ips]

    def _is_valid_ip(self, ip: str) -> bool:
        """检查IP地址是否有效
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否是有效的IP地址
        """
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (AttributeError, TypeError, ValueError):
            return False

# 示例用法
if __name__ == "__main__":
    # 假设我们有一个IPRecordManager实例
    ip_record_manager = IPRecordManager(None)  # 这里需要传入实际的Session对象
    ip_suggestion = IPSuggestion(ip_record_manager)
    generated_ips = ip_suggestion.generate_and_save_ips()
    print("生成的IP地址:", generated_ips) 