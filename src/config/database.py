import os
from pathlib import Path
from typing import Dict, Any

# 应用配置目录
APP_CONFIG_DIR = os.path.join(Path.home(), '.wecom_live_sign')

# 确保配置目录存在
os.makedirs(APP_CONFIG_DIR, exist_ok=True)

def get_default_paths() -> Dict[str, str]:
    """获取默认路径配置
    这些路径仅在用户未指定自定义路径时使用
    """
    return {
        'db_path': os.path.join(APP_CONFIG_DIR, 'data.db'),
        'backup_path': os.path.join(APP_CONFIG_DIR, 'backups'),
        'migration_path': os.path.join(APP_CONFIG_DIR, 'migrations')
    }

def get_default_db_config() -> Dict[str, Any]:
    """获取默认数据库配置"""
    return {
        'db_path': os.path.join(APP_CONFIG_DIR, 'data.db'),
        'backup_path': os.path.join(APP_CONFIG_DIR, 'backups'),
        'max_connections': 5,
        'pool_recycle': 3600,
        'echo': False
    }

def get_default_migration_config() -> Dict[str, Any]:
    """获取默认迁移配置"""
    return {
        'migration_path': os.path.join(APP_CONFIG_DIR, 'migrations'),
        'backup_before_migrate': True
    }

# 数据库配置
DB_CONFIG = get_default_db_config()

# 数据库迁移配置
MIGRATION_CONFIG = get_default_migration_config()

# 确保备份目录存在
os.makedirs(DB_CONFIG['backup_path'], exist_ok=True)
os.makedirs(MIGRATION_CONFIG['migration_path'], exist_ok=True) 