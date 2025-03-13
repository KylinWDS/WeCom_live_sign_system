import os
from pathlib import Path

# 应用配置目录
APP_CONFIG_DIR = os.path.join(Path.home(), '.wecom_live_sign')

# 确保配置目录存在
os.makedirs(APP_CONFIG_DIR, exist_ok=True)

# 数据库配置
DB_CONFIG = {
    'db_path': os.path.join(APP_CONFIG_DIR, 'data.db'),
    'backup_path': os.path.join(APP_CONFIG_DIR, 'backup'),
    'max_connections': 5,
    'pool_recycle': 3600,
    'echo': False
}

# 数据库迁移配置
MIGRATION_CONFIG = {
    'migration_path': os.path.join(APP_CONFIG_DIR, 'migrations'),
    'backup_before_migrate': True
}

# 确保备份目录存在
os.makedirs(DB_CONFIG['backup_path'], exist_ok=True)
os.makedirs(MIGRATION_CONFIG['migration_path'], exist_ok=True) 