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
            source: IP来源，'manual' 或 'error'
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 验证IP格式
            if not self._validate_ip(ip):
                logger.warning(f"无效的IP地址格式: {ip}")
                return False
            
            # 检查IP数量限制
            count = self.session.query(IPRecord).filter_by(is_active=True).count()
            if count >= 120:
                logger.warning(f"IP记录数量已达到上限(120)，无法添加新IP: {ip}")
                return False
            
            # 检查IP是否已存在
            existing = self.session.query(IPRecord).filter_by(ip=ip).first()
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                    existing.source = source
                    existing.updated_at = datetime.now()
                    self.session.commit()
                return True
            
            # 添加新IP
            ip_record = IPRecord(ip=ip, source=source)
            self.session.add(ip_record)
            self.session.commit()
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