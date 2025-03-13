import os
import json
import shutil
import time
from datetime import datetime
from typing import Any, Dict, Optional
from src.utils.logger_utils import get_logger

logger = get_logger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".wecom_live_sign")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.backup_dir = os.path.join(self.config_dir, "backups")
        self.config = self._load_config() or self._get_default_config()
        
        logger.info("初始化ConfigManager...")
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            logger.info("加载配置文件...")
            # 创建配置目录
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                
            # 如果配置文件不存在,创建默认配置
            if not os.path.exists(self.config_file):
                default_config = self._get_default_config()
                self._save_config(default_config)
                logger.info("配置文件加载成功")
                return default_config
                
            # 读取配置文件
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                
            # 检查并补充缺失的默认配置
            default_config = self._get_default_config()
            merged_config = self._merge_config(default_config, config)
            
            # 保存合并后的配置
            self._save_config(merged_config)
            logger.info("配置文件加载成功")
            return merged_config if merged_config else self._get_default_config()
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            logger.error("加载配置文件失败，使用默认配置")
            return self._get_default_config()
            
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            # 创建备份
            self._create_backup()
            
            # 保存配置
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
            # 清理旧备份
            self._cleanup_backups()
            
            logger.info("ConfigManager初始化完成，配置已加载")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False
            
    def _create_backup(self) -> bool:
        """创建配置文件备份"""
        try:
            # 创建备份目录
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
                
            # 如果配置文件不存在,不需要备份
            if not os.path.exists(self.config_file):
                return True
                
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"config_{timestamp}.json")
            
            # 复制配置文件
            shutil.copy2(self.config_file, backup_file)
            
            logger.info(f"创建配置文件备份: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"创建配置文件备份失败: {str(e)}")
            return False
            
    def _cleanup_backups(self) -> bool:
        """清理旧备份"""
        try:
            if not hasattr(self, 'config') or self.config is None:
                logger.error("配置未初始化，无法清理备份")
                return False
            
            # 获取备份保留天数
            retention_days = self.config.get("system", {}).get("backup_retention", 30)
            
            # 获取所有备份文件
            if not os.path.exists(self.backup_dir):
                return True
                
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("config_") and file.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
                    
            # 按修改时间排序
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除过期备份
            current_time = time.time()
            for file_path, mtime in backup_files:
                if current_time - mtime > retention_days * 24 * 3600:
                    try:
                        os.remove(file_path)
                        logger.info(f"删除过期备份: {file_path}")
                    except Exception as e:
                        logger.error(f"删除过期备份失败: {str(e)}")
                        
            return True
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {str(e)}")
            return False
            
    def restore_backup(self, backup_file: str) -> bool:
        """从备份恢复配置
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_file):
                logger.error(f"备份文件不存在: {backup_file}")
                return False
                
            # 创建当前配置的备份
            self._create_backup()
            
            # 复制备份文件
            shutil.copy2(backup_file, self.config_file)
            
            # 重新加载配置
            self.config = self._load_config()
            
            logger.info(f"从备份恢复配置成功: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"从备份恢复配置失败: {str(e)}")
            return False
            
    def get_backup_list(self) -> list:
        """获取备份列表
        
        Returns:
            list: 备份文件列表
        """
        try:
            if not os.path.exists(self.backup_dir):
                return []
                
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("config_") and file.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append({
                        "path": file_path,
                        "name": file,
                        "size": os.path.getsize(file_path),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path))
                    })
                    
            # 按修改时间排序
            backup_files.sort(key=lambda x: x["modified"], reverse=True)
            return backup_files
            
        except Exception as e:
            logger.error(f"获取备份列表失败: {str(e)}")
            return []
            
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "system": {
                "initialized": False,
                "theme": "light",
                "language": "zh_CN",
                "data_path": os.path.join(self.config_dir, "data"),
                "log_path": os.path.join(self.config_dir, "logs"),
                "log_level": "INFO",
                "log_retention": 30,
                "backup_retention": 30
            },
            "corporations": [],
            "users": {
                "roles": {
                    "admin": {
                        "name": "管理员",
                        "permissions": ["all"]
                    },
                    "user": {
                        "name": "普通用户",
                        "permissions": ["view", "sign"]
                    }
                }
            }
        }
        
    def _merge_config(self, default: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        merged = default.copy()
        
        for key, value in current.items():
            if key in merged:
                if isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = self._merge_config(merged[key], value)
                else:
                    merged[key] = value
            else:
                merged[key] = value
                
        return merged
        
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            keys = key.split(".")
            value = self.config
            
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
                    
            return value if value is not None else default
            
        except Exception as e:
            logger.error(f"获取配置值失败: {str(e)}")
            return default
            
    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        try:
            keys = key.split(".")
            config = self.config
            
            # 遍历到最后一个key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
                
            # 设置值
            config[keys[-1]] = value
            return True
            
        except Exception as e:
            logger.error(f"设置配置值失败: {str(e)}")
            return False
            
    def save_config(self) -> bool:
        """保存配置到文件"""
        return self._save_config(self.config)
        
    def reset_config(self) -> bool:
        """重置配置为默认值"""
        try:
            self.config = self._get_default_config()
            return self._save_config(self.config)
        except Exception as e:
            logger.error(f"重置配置失败: {str(e)}")
            return False
    
    def get_corporations(self):
        """获取企业列表"""
        return self.config.get("corporations", [])
    
    def get_corporation(self, name):
        """获取企业信息"""
        corporations = self.get_corporations()
        for corp in corporations:
            if corp["name"] == name:
                return corp
        return None
    
    def add_corporation(self, corp_info):
        """添加企业"""
        corporations = self.get_corporations()
        corporations.append(corp_info)
        self.set("corporations", corporations)
    
    def update_corporation(self, name, corp_info):
        """更新企业信息"""
        corporations = self.get_corporations()
        for i, corp in enumerate(corporations):
            if corp["name"] == name:
                corporations[i] = corp_info
                self.set("corporations", corporations)
                return True
        return False
    
    def delete_corporation(self, name):
        """删除企业"""
        corporations = self.get_corporations()
        corporations = [corp for corp in corporations if corp["name"] != name]
        self.set("corporations", corporations)
    
    def get_theme(self) -> str:
        """获取主题设置
        
        Returns:
            str: 主题名称，默认为"浅色"
        """
        return self.config.get("theme", "浅色")
    
    def set_theme(self, theme: str):
        """设置主题
        
        Args:
            theme: 主题名称
        """
        self.config["theme"] = theme
        self._save_config()
    
    def get_auto_cleanup(self) -> bool:
        """获取自动清理设置
        
        Returns:
            bool: 是否启用自动清理，默认为 False
        """
        return self.config.get("auto_cleanup", False)
    
    def get_cleanup_days(self) -> int:
        """获取清理天数设置
        
        Returns:
            int: 清理天数，默认为 30
        """
        return self.config.get("cleanup_days", 30) 