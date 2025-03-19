import os
import json
import shutil
import time
from datetime import datetime
from typing import Any, Dict, Optional
from src.utils.logger import get_logger
from src.models.user import UserRole
from src.config.database import get_default_paths
from src.core.database import get_db_connection_config

logger = get_logger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化ConfigManager..."""
        self.config_dir = None
        self.config_file = None
        self.backup_dir = None
        self.config = None
        self.logger = logger
        logger.info("初始化ConfigManager...")
        
    def initialize(self, config_dir: str, system_config: Dict[str, Any] = None) -> bool:
        """初始化配置管理器
        
        Args:
            config_dir: 配置目录路径
            system_config: 系统配置，如果提供则使用此配置而不是默认配置
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            self.config_dir = config_dir
            self.config_file = os.path.join(config_dir, "config.json")
            
            # 创建必要的目录
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 如果提供了系统配置，使用它
            if system_config:
                self.config = system_config
                # 确保企业配置存在
                if "corporations" not in self.config:
                    self.config["corporations"] = []
                self._save_config(self.config)
            else:
                # 加载配置
                self.config = self._load_config()
            
            # 检查是否已初始化
            if not self.config.get("system", {}).get("initialized", False):
                logger.error("配置未初始化，请先运行初始化向导")
                return False
            
            # 获取用户配置的路径
            paths = self.config.get("paths", {})
            if not all(paths.values()):
                logger.error("路径配置不完整，请先运行初始化向导")
                return False
            
            # 使用用户配置的路径
            self.backup_dir = paths.get("backup")
            log_path = paths.get("log")
            
            # 确保目录存在
            os.makedirs(self.backup_dir, exist_ok=True)
            os.makedirs(log_path, exist_ok=True)
            
            logger.info(f"配置管理器初始化成功: {self.config_dir}")
            return True
            
        except Exception as e:
            logger.error(f"初始化配置管理器失败: {str(e)}")
            return False
            
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        if not self.config_dir:
            raise RuntimeError("配置管理器未初始化")
            
        return {
            "system": {
                "initialized": False,
                "theme": "light",
                "language": "zh_CN",
                "data_path": os.path.join(self.config_dir, "data"),
                "log_path": os.path.join(self.config_dir, "logs"),
                "backup_path": os.path.join(self.config_dir, "backups"),
                "log_level": "INFO",
                "log_retention": 30,
                "backup_retention": 30
            },
            "database": {
                "type": "sqlite",
                "path": os.path.join(self.config_dir, "data", "data.db"),
                "backup_path": os.path.join(self.config_dir, "backups"),
                "pool_size": 5,
                "timeout": 30,
                "echo": False,
                "pool_recycle": 3600,
                "pool_pre_ping": True
            },
            "corporations": []
        }
        
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置
        
        Returns:
            Dict[str, Any]: 数据库配置
        """
        if not self.config:
            raise RuntimeError("配置未初始化")
            
        # 获取用户配置的路径
        paths = self.config.get("paths", {})
        
        # 如果用户没有配置路径，使用默认路径
        if not paths or not paths.get("data"):
            default_paths = get_default_paths()
            if not paths:
                paths = {}
            paths["data"] = paths.get("data") or default_paths["db_path"]
            paths["backup"] = paths.get("backup") or default_paths["backup_path"]
            self.config["paths"] = paths
            
        # 获取数据库连接配置
        db_config = get_db_connection_config()
        
        # 合并用户配置的数据库参数（如果有）
        if "database" in self.config:
            user_db_config = self.config["database"]
            # 合并所有配置，包括路径
            for key, value in user_db_config.items():
                db_config[key] = value
        
        # 确保路径使用正确的分隔符
        if "path" in db_config:
            db_config["path"] = db_config["path"].replace("\\", "/")
        if "backup_path" in db_config:
            db_config["backup_path"] = db_config["backup_path"].replace("\\", "/")
        
        logger.info(f"数据库配置: {db_config}")
        return db_config
        
    def set_database_config(self, db_config: Dict[str, Any]) -> bool:
        """设置数据库配置
        
        Args:
            db_config: 数据库配置
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.config:
                raise RuntimeError("配置未初始化")
                
            self.config["database"] = db_config
            return True
            
        except Exception as e:
            logger.error(f"设置数据库配置失败: {str(e)}")
            return False
            
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            logger.info("加载配置文件...")
            
            # 如果配置文件不存在，创建默认配置
            if not os.path.exists(self.config_file):
                default_config = self._get_default_config()
                self._save_config(default_config)
                return default_config
                
            # 读取配置文件
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                
            # 检查并补充缺失的默认配置
            default_config = self._get_default_config()
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if k not in config[key]:
                            config[key][k] = v
                            
            # 保存合并后的配置
            self._save_config(config)
            return config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
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
            # 如果配置文件不存在，不需要备份
            if not os.path.exists(self.config_file):
                return True
                
            # 如果备份目录还未设置，使用默认路径
            if not hasattr(self, 'backup_dir') or not self.backup_dir:
                self.backup_dir = os.path.join(self.config_dir, "backups")
                os.makedirs(self.backup_dir, exist_ok=True)
                
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
            if not self.config:
                logger.error("配置未初始化，无法清理备份")
                return False
                
            if not self.backup_dir:
                logger.warning("备份目录未设置，跳过清理")
                return True
                
            # 获取备份保留天数
            retention_days = self.config.get("system", {}).get("backup_retention", 30)
            if retention_days <= 0:
                return True
                
            # 获取当前时间
            now = time.time()
            
            # 遍历备份文件
            for file in os.listdir(self.backup_dir):
                if not file.endswith(".json"):
                    continue
                    
                file_path = os.path.join(self.backup_dir, file)
                file_time = os.path.getctime(file_path)
                
                # 如果文件超过保留天数，删除它
                if now - file_time > retention_days * 86400:
                    os.remove(file_path)
                    logger.info(f"删除过期备份: {file}")
                    
            return True
            
        except Exception as e:
            logger.error(f"清理备份失败: {str(e)}")
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
        
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        if not self.config:
            raise RuntimeError("配置未初始化")
        return self.config 