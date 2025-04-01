# 配置模块文档

## 概述
配置模块负责系统所有配置项的管理，包括系统设置、用户偏好、企业微信配置、数据库连接等。该模块提供了统一的配置管理机制，支持多种配置方式和灵活的配置路径管理。

## 与启动器的集成

配置模块在启动流程中扮演关键角色，实现了首次启动自动初始化、配置验证和加载流程。启动器在初始化阶段会通过配置模块检查系统配置状态，必要时启动初始化向导。

## 配置文件位置

系统支持灵活的配置文件位置管理：

1. **默认位置**：应用程序所在目录下的`config/`目录
2. **用户自定义位置**：初始化向导中可设置配置文件存储位置
3. **环境变量指定**：通过`WECOM_LIVE_CONFIG_PATH`环境变量指定

优先级顺序为：环境变量 > 用户自定义 > 默认位置

## 目录结构

### 1. 配置项定义 (definitions/)
配置项的模式定义文件。

主要内容：
- 系统配置模式
- 用户配置模式
- 企业微信配置模式
- 数据库配置模式
- 日志配置模式
- UI配置模式

### 2. 管理器 (managers/)
配置管理相关类。

主要管理器：
- 配置管理器 (ConfigManager)
- 路径管理器 (PathManager)
- 初始化管理器 (InitManager)
- 验证管理器 (ValidationManager)
- 迁移管理器 (MigrationManager)
- 加密管理器 (EncryptionManager)

### 3. 工具类 (utils/)
配置相关的工具函数。

主要工具：
- 配置加载工具 (LoadUtils)
- 配置保存工具 (SaveUtils)
- 配置验证工具 (ValidationUtils)
- 配置迁移工具 (MigrationUtils)
- 配置合并工具 (MergeUtils)
- 加密解密工具 (CryptoUtils)

## 主要功能

### 1. 配置加载与保存
- 配置文件加载
- 配置项合并
- 配置保存
- 自动备份
- 配置监控
- 配置重载

```python
# 配置加载示例
def load_config(self, config_path=None):
    """加载配置文件"""
    # 按优先级确定配置路径
    if config_path is None:
        config_path = self._determine_config_path()
        
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        return self._create_default_config(config_path)
        
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 验证配置有效性
        if self._validate_config(config):
            return config
        else:
            logger.warning("配置验证失败，使用默认配置")
            return self._create_default_config(config_path)
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}")
        return self._create_default_config(config_path)
```

### 2. 配置验证
- 配置模式验证
- 类型检查
- 必填项检查
- 值范围检查
- 逻辑关系检查
- 环境依赖检查

```python
# 配置验证示例
def validate_config(self, config):
    """验证配置是否合法"""
    # 检查必要的配置项
    required_keys = ['system', 'database', 'wecom']
    for key in required_keys:
        if key not in config:
            logger.error(f"缺少必要的配置项: {key}")
            return False
            
    # 验证系统配置
    if not self._validate_system_config(config['system']):
        return False
        
    # 验证数据库配置
    if not self._validate_database_config(config['database']):
        return False
        
    # 验证企业微信配置
    if not self._validate_wecom_config(config['wecom']):
        return False
        
    return True
```

### 3. 配置加密
- 敏感配置加密
- 加密密钥管理
- 密钥轮换机制
- 加密配置读写
- 安全级别控制
- 明文配置转换

```python
# 配置加密示例
def encrypt_sensitive_data(self, config):
    """加密敏感配置数据"""
    # 创建加密工具
    crypto = CryptoUtils(self.encryption_key)
    
    # 深拷贝配置以避免修改原始对象
    encrypted_config = copy.deepcopy(config)
    
    # 加密数据库连接信息
    if 'database' in encrypted_config:
        if 'password' in encrypted_config['database']:
            encrypted_config['database']['password'] = crypto.encrypt(
                encrypted_config['database']['password']
            )
    
    # 加密企业微信Secret
    if 'wecom' in encrypted_config:
        if 'corp_secret' in encrypted_config['wecom']:
            encrypted_config['wecom']['corp_secret'] = crypto.encrypt(
                encrypted_config['wecom']['corp_secret']
            )
    
    return encrypted_config
```

### 4. 配置监听
- 配置变更通知
- 监听器注册
- 变更事件分发
- 差异检测
- 批量更新处理
- 监听优先级

```python
# 配置监听示例
class ConfigListener:
    def __init__(self):
        self.listeners = {}
        
    def register(self, key, callback, priority=0):
        """注册配置变更监听器"""
        if key not in self.listeners:
            self.listeners[key] = []
        self.listeners[key].append((priority, callback))
        # 按优先级排序
        self.listeners[key].sort(key=lambda x: x[0], reverse=True)
        
    def notify(self, key, old_value, new_value):
        """通知配置项变更"""
        if key in self.listeners:
            for _, callback in self.listeners[key]:
                try:
                    callback(old_value, new_value)
                except Exception as e:
                    logger.error(f"配置监听器回调错误: {str(e)}")
```

### 5. 配置迁移
- 版本升级迁移
- 配置结构迁移
- 默认值更新
- 配置项重命名
- 配置项删除
- 迁移日志记录

```python
# 配置迁移示例
def migrate_config(self, config, from_version, to_version):
    """迁移配置到新版本"""
    # 检查版本是否需要迁移
    if from_version >= to_version:
        return config
        
    # 深拷贝配置以避免修改原始对象
    migrated_config = copy.deepcopy(config)
    
    # 根据版本差异逐步迁移
    current_version = from_version
    
    # 从旧版本到新版本，逐个版本迁移
    while current_version < to_version:
        next_version = current_version + 0.1
        migrated_config = self._migrate_version(
            migrated_config, 
            current_version, 
            next_version
        )
        current_version = next_version
        
    # 更新配置版本号
    migrated_config['version'] = to_version
    
    return migrated_config
```

### 6. 初始化向导
- 首次启动检测
- 配置向导界面
- 分步配置流程
- 配置验证反馈
- 配置存储位置选择
- 初始配置生成

## 配置项详解

### 1. 系统配置

```json
{
    "version": "1.0.0",
    "app_name": "企业微信直播签到系统",
    "log_level": "INFO",
    "data_path": "/path/to/data",
    "temp_path": "/path/to/temp",
    "export_path": "/path/to/export",
    "auto_update": true,
    "language": "zh_CN",
    "first_run": false,
    "admin_username": "admin"
}
```

### 2. 数据库配置

```json
{
    "type": "sqlite",
    "path": "/path/to/database.db",
    "connection_string": "",
    "backup": {
        "enabled": true,
        "interval": 86400,
        "keep_days": 7,
        "path": "/path/to/backup"
    },
    "pool_size": 5,
    "timeout": 30
}
```

### 3. 企业微信配置

```json
{
    "corp_id": "your_corp_id",
    "corp_secret": "encrypted_corp_secret",
    "agent_id": "your_agent_id",
    "token_expire_time": 7200,
    "api_base_url": "https://qyapi.weixin.qq.com/cgi-bin",
    "redirect_uri": "",
    "access_token": "",
    "token_expires_at": 0,
    "ip_whitelist": []
}
```

### 4. UI配置

```json
{
    "theme": "auto",
    "font_size": "medium",
    "density": "default",
    "animation": true,
    "sidebar_width": 240,
    "custom_css": "",
    "header_height": 64,
    "table_row_height": 48,
    "icon_set": "default"
}
```

## 使用示例

### 1. 初始化配置管理器
```python
from src.config.managers.config_manager import ConfigManager

# 初始化配置管理器
config_manager = ConfigManager()

# 加载配置
config = config_manager.load()
```

### 2. 获取配置项
```python
# 获取简单配置项
log_level = config_manager.get('system.log_level', 'INFO')

# 获取嵌套配置项
backup_interval = config_manager.get('database.backup.interval', 86400)

# 获取带解密的配置项
corp_secret = config_manager.get_secure('wecom.corp_secret')
```

### 3. 修改配置
```python
# 修改配置项
config_manager.set('system.log_level', 'DEBUG')

# 修改嵌套配置项
config_manager.set('database.backup.keep_days', 14)

# 修改并加密敏感配置项
config_manager.set_secure('wecom.corp_secret', 'new_corp_secret')

# 保存配置
config_manager.save()
```

### 4. 监听配置变更
```python
def on_log_level_changed(old_value, new_value):
    print(f"日志级别从 {old_value} 变更为 {new_value}")
    logger.setLevel(new_value)

# 注册配置变更监听
config_manager.register_listener('system.log_level', on_log_level_changed)
```

### 5. 批量更新配置
```python
# 批量更新多个配置项
updates = {
    'system.log_level': 'DEBUG',
    'system.auto_update': False,
    'database.backup.enabled': True,
    'database.backup.keep_days': 14
}

config_manager.batch_update(updates)
config_manager.save()
```

## 线程安全

配置模块实现了线程安全的设计，确保在多线程环境下正常工作：

1. **读写锁**: 使用读写锁保护配置读写操作
2. **原子操作**: 批量修改以原子操作方式进行
3. **本地缓存**: 每个线程维护本地配置缓存
4. **事件队列**: 配置更新通过事件队列同步

```python
class ThreadSafeConfigManager:
    def __init__(self):
        self._config = {}
        self._rw_lock = threading.RLock()
        
    def get(self, key, default=None):
        """线程安全地获取配置项"""
        with self._rw_lock:
            # 使用嵌套字典查找
            value = self._config
            for part in key.split('.'):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
            
    def set(self, key, value):
        """线程安全地设置配置项"""
        with self._rw_lock:
            # 使用嵌套字典设置
            parts = key.split('.')
            current = self._config
            
            # 遍历路径，创建必要的字典
            for i, part in enumerate(parts[:-1]):
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
                
            # 设置最终值
            current[parts[-1]] = value
```

## 注意事项
1. 敏感配置项应使用`set_secure/get_secure`方法处理
2. 配置修改后需要调用`save`方法保存
3. 避免频繁修改和保存配置
4. 大量配置项修改应使用批量更新
5. 配置路径变更需重启应用生效
6. 配置文件格式改变需要相应的迁移逻辑
7. 不要在监听器中再次修改同一配置项，避免循环调用
8. 确保配置目录有写入权限 