import os
import shutil
import zipfile
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.utils.logger import get_logger
from src.core.config_manager import ConfigManager

logger = get_logger(__name__)

class BackupManager:
    """备份管理器"""
    
    def __init__(self):
        """初始化备份管理器"""
        self.config_manager = ConfigManager()
        self.backup_dir = self.config_manager.get("system.backup_path", "backups")
        self.backup_days = self.config_manager.get("system.backup_days", 30)
        self.max_backups = self.config_manager.get("system.max_backups", 10)
        self.compress_backups = self.config_manager.get("system.compress_backups", True)
        
        # 创建备份目录
        os.makedirs(self.backup_dir, exist_ok=True)
    
    async def create_backup(self, source_path: str = "data.db") -> Optional[str]:
        """创建备份
        
        Args:
            source_path: 源文件路径
            
        Returns:
            Optional[str]: 备份文件路径
        """
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.db")
            
            # 复制文件
            shutil.copy2(source_path, backup_file)
            
            # 压缩备份
            if self.compress_backups:
                zip_file = f"{backup_file}.zip"
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_file, os.path.basename(backup_file))
                os.remove(backup_file)
                backup_file = zip_file
            
            # 清理旧备份
            await self.cleanup_old_backups()
            
            logger.info(f"创建备份成功: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            return None
    
    async def restore_backup(self, backup_file: str, target_path: str = "data.db") -> bool:
        """恢复备份
        
        Args:
            backup_file: 备份文件路径
            target_path: 目标文件路径
            
        Returns:
            bool: 是否恢复成功
        """
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_file):
                logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 创建当前文件的备份
            current_backup = await self.create_backup(target_path)
            if not current_backup:
                logger.error("创建当前文件备份失败")
                return False
            
            # 解压备份文件(如果是压缩的)
            if backup_file.endswith('.zip'):
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    zipf.extractall(self.backup_dir)
                backup_file = backup_file.replace('.zip', '')
            
            # 恢复备份
            shutil.copy2(backup_file, target_path)
            
            logger.info(f"恢复备份成功: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """获取备份列表
        
        Returns:
            List[Dict[str, Any]]: 备份列表
        """
        try:
            backups = []
            
            # 遍历备份目录
            for filename in os.listdir(self.backup_dir):
                if not filename.startswith("backup_"):
                    continue
                    
                file_path = os.path.join(self.backup_dir, filename)
                file_stat = os.stat(file_path)
                
                backups.append({
                    "name": filename,
                    "path": file_path,
                    "size": file_stat.st_size,
                    "created_at": datetime.fromtimestamp(file_stat.st_ctime),
                    "is_compressed": filename.endswith('.zip')
                })
            
            # 按创建时间排序
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"获取备份列表失败: {str(e)}")
            return []
    
    async def cleanup_old_backups(self):
        """清理旧备份"""
        try:
            # 获取备份列表
            backups = self.list_backups()
            if not backups:
                return
            
            # 按时间排序
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
            # 删除多余的备份
            if len(backups) > self.max_backups:
                for backup in backups[self.max_backups:]:
                    try:
                        os.remove(backup["path"])
                        logger.info(f"删除多余备份: {backup['name']}")
                    except Exception as e:
                        logger.error(f"删除多余备份失败: {str(e)}")
            
            # 删除过期备份
            expire_time = datetime.now().timestamp() - (self.backup_days * 24 * 3600)
            for backup in backups:
                if backup["created_at"].timestamp() < expire_time:
                    try:
                        os.remove(backup["path"])
                        logger.info(f"删除过期备份: {backup['name']}")
                    except Exception as e:
                        logger.error(f"删除过期备份失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {str(e)}")
            
    def get_backup_info(self, backup_file: str) -> Optional[Dict[str, Any]]:
        """获取备份文件信息
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 备份信息
        """
        try:
            if not os.path.exists(backup_file):
                return None
                
            file_stat = os.stat(backup_file)
            return {
                "name": os.path.basename(backup_file),
                "path": backup_file,
                "size": file_stat.st_size,
                "created_at": datetime.fromtimestamp(file_stat.st_ctime),
                "is_compressed": backup_file.endswith('.zip')
            }
            
        except Exception as e:
            logger.error(f"获取备份信息失败: {str(e)}")
            return None 