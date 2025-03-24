from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.ip_record import IPRecord
from src.utils.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)

class IPRecordManager:
    """IP记录管理器"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add_ip(self, ip: str, source: str = 'manual') -> bool:
        """添加IP记录
        
        Args:
            ip: IP地址
            source: IP来源，可选值：'manual', 'error', 'history', 'infer'
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 1. 验证IP地址格式
            if not self._validate_ip(ip):
                logger.warning(f"无效的IP地址格式: {ip}")
                return False
            
            # 2. 检查数量限制（非infer类型）
            if source != 'infer':
                count = self.session.query(IPRecord).filter(
                    IPRecord.is_active == True,
                    IPRecord.source != 'infer'
                ).count()
                if count >= 254:
                    logger.warning(f"IP记录数量已达到上限(254)，无法添加新IP: {ip}")
                    return False
            
            # 3. 检查IP是否已存在
            existing = self.session.query(IPRecord).filter_by(ip=ip).first()
            
            # 4. 处理manual类型的特殊逻辑
            if source == 'manual':
                if existing:
                    # 如果IP已存在，更新为manual类型
                    existing.source = 'manual'
                    existing.updated_at = datetime.now()
                    existing.is_active = True
                    self.session.commit()
                    logger.info(f"将已存在的IP记录 [{ip}] 更新为manual类型")
                    
                    # 成功设置当前IP为manual后，将其他manual类型IP更改为history
                    other_manuals = self.session.query(IPRecord).filter(
                        IPRecord.source == 'manual',
                        IPRecord.is_active == True,
                        IPRecord.ip != ip  # 排除当前IP
                    ).all()
                    
                    for record in other_manuals:
                        record.source = 'history'
                        record.updated_at = datetime.now()
                        logger.info(f"将IP [{record.ip}] 从manual类型更改为history类型")
                    
                    self.session.commit()
                    return True
                else:
                    # 如果是新IP，先添加为manual类型
                    ip_record = IPRecord(ip=ip, source=source)
                    self.session.add(ip_record)
                    self.session.commit()
                    logger.info(f"添加新IP记录: {ip}, 类型: {source}")
                    
                    # 成功添加当前IP后，将其他manual类型IP更改为history
                    other_manuals = self.session.query(IPRecord).filter(
                        IPRecord.source == 'manual',
                        IPRecord.is_active == True,
                        IPRecord.ip != ip  # 排除当前IP
                    ).all()
                    
                    for record in other_manuals:
                        record.source = 'history'
                        record.updated_at = datetime.now()
                        logger.info(f"将IP [{record.ip}] 从manual类型更改为history类型")
                    
                    self.session.commit()
                    return True
            
            # 5. 处理非manual类型的情况
            if existing:
                # 更新通用属性
                existing.updated_at = datetime.now()
                existing.is_active = True
                
                # 根据不同情况更新source
                if source == 'error':
                    # error类型不能覆盖manual类型，但可以覆盖其他类型
                    if existing.source == 'manual':
                        # 当error遇到manual时，只更新时间，不改变类型
                        logger.info(f"保留IP {ip} 的'manual'类型，只更新时间")
                    elif existing.source != 'error':
                        # error可以覆盖history和infer类型
                        existing.source = 'error'
                        logger.info(f"将IP {ip} 从'{existing.source}'类型更新为'error'类型")
                elif source in ['history', 'infer']:
                    # history和infer类型不覆盖已有类型，保持原有类型
                    logger.info(f"保留IP {ip} 的'{existing.source}'类型，不覆盖为'{source}'类型")
                
                self.session.commit()
                return True
            
            # 6. 添加新IP记录（非manual类型）
            ip_record = IPRecord(ip=ip, source=source)
            self.session.add(ip_record)
            self.session.commit()
            logger.info(f"添加新IP记录: {ip}, 类型: {source}")
            return True
            
        except Exception as e:
            logger.error(f"添加IP记录失败: {str(e)}")
            self.session.rollback()
            return False
    
    def get_all_records(self) -> List[IPRecord]:
        """获取所有IP记录
        
        Returns:
            List[IPRecord]: IP记录列表
        """
        try:
            return self.session.query(IPRecord).order_by(IPRecord.created_at.desc()).all()
        except Exception as e:
            logger.error(f"获取IP记录失败: {str(e)}")
            return []
    
    def get_active_records(self) -> List[IPRecord]:
        """获取所有活跃的IP记录
        
        Returns:
            List[IPRecord]: 活跃的IP记录列表
        """
        try:
            return self.session.query(IPRecord).filter_by(is_active=True).order_by(IPRecord.created_at.desc()).all()
        except Exception as e:
            logger.error(f"获取活跃IP记录失败: {str(e)}")
            return []
    
    def delete_record(self, record_id: int) -> bool:
        """删除IP记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            record = self.session.query(IPRecord).filter_by(id=record_id).first()
            if record:
                record.is_active = False
                record.updated_at = datetime.now()
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"删除IP记录失败: {str(e)}")
            self.session.rollback()
            return False
    
    def _validate_ip(self, ip: str) -> bool:
        """验证IP地址格式
        
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
    
    def get_all_ips(self) -> List[str]:
        """获取所有活跃的IP地址
        
        Returns:
            List[str]: IP地址列表
        """
        try:
            records = self.session.query(IPRecord).filter_by(is_active=True).all()
            return [record.ip for record in records]
        except Exception as e:
            logger.error(f"获取IP记录失败: {str(e)}")
            return []
    
    def remove_ip(self, ip: str) -> bool:
        """移除IP记录
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否移除成功
        """
        try:
            record = self.session.query(IPRecord).filter_by(ip=ip).first()
            if record:
                record.is_active = False
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"移除IP记录失败: {str(e)}")
            self.session.rollback()
            return False
    
    def get_ip_count(self) -> int:
        """获取当前活跃IP数量
        
        Returns:
            int: IP数量
        """
        try:
            return self.session.query(IPRecord).filter_by(is_active=True).count()
        except Exception as e:
            logger.error(f"获取IP数量失败: {str(e)}")
            return 0
    
    def clean_history_records(self, days: int = 30) -> int:
        """清理指定天数之前的历史记录
        
        Args:
            days: 天数，默认30天
            
        Returns:
            int: 清理的记录数量
        """
        try:
            # 计算截止时间
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 查询需要清理的记录
            records = self.session.query(IPRecord).filter(
                IPRecord.created_at < cutoff_date,
                IPRecord.is_active == True
            ).all()
            
            # 清理记录
            count = 0
            for record in records:
                record.is_active = False
                record.updated_at = datetime.now()
                count += 1
            
            self.session.commit()
            logger.info(f"清理了 {count} 条历史IP记录")
            return count
            
        except Exception as e:
            logger.error(f"清理历史记录失败: {str(e)}")
            self.session.rollback()
            return 0
    
    def clean_selected_records(self, record_ids: List[int]) -> int:
        """清理选中的记录
        
        Args:
            record_ids: 记录ID列表
            
        Returns:
            int: 清理的记录数量
        """
        try:
            count = 0
            for record_id in record_ids:
                record = self.session.query(IPRecord).filter_by(id=record_id).first()
                if record:
                    record.is_active = False
                    record.updated_at = datetime.now()
                    count += 1
            
            self.session.commit()
            logger.info(f"清理了 {count} 条选中的IP记录")
            return count
            
        except Exception as e:
            logger.error(f"清理选中记录失败: {str(e)}")
            self.session.rollback()
            return 0
    
    def get_record_by_id(self, record_id: int) -> Optional[IPRecord]:
        """根据ID获取记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            Optional[IPRecord]: IP记录对象
        """
        try:
            return self.session.query(IPRecord).filter_by(id=record_id).first()
        except Exception as e:
            logger.error(f"获取IP记录失败: {str(e)}")
            return None
    
    def get_records_by_ids(self, record_ids: List[int]) -> List[IPRecord]:
        """根据ID列表获取记录
        
        Args:
            record_ids: 记录ID列表
            
        Returns:
            List[IPRecord]: IP记录列表
        """
        try:
            return self.session.query(IPRecord).filter(IPRecord.id.in_(record_ids)).all()
        except Exception as e:
            logger.error(f"获取IP记录失败: {str(e)}")
            return []
    
    def get_ip_source(self, ip: str) -> str:
        """获取IP地址的来源
        
        Args:
            ip: IP地址
            
        Returns:
            str: IP来源，可能的值：'manual', 'error', 'history', 'infer'
        """
        try:
            record = self.session.query(IPRecord).filter_by(ip=ip, is_active=True).first()
            return record.source if record else ''
        except Exception as e:
            logger.error(f"获取IP来源失败: {str(e)}")
            return ''
    
    def get_ips_by_source(self, source: str) -> List[str]:
        """根据来源获取IP地址列表
        
        Args:
            source: IP来源，可选值：'manual', 'error', 'history', 'infer'
            
        Returns:
            List[str]: IP地址列表
        """
        try:
            records = self.session.query(IPRecord).filter_by(
                source=source,
                is_active=True
            ).order_by(IPRecord.created_at.desc()).all()
            return [record.ip for record in records]
        except Exception as e:
            logger.error(f"获取{source}来源的IP记录失败: {str(e)}")
            return [] 