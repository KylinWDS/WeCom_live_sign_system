# 配置模块文档

## 概述
配置模块负责管理系统配置，包括数据库配置、系统参数、环境变量等。该模块提供了统一的配置管理接口，确保系统配置的一致性和可维护性。

## 配置项说明

### 1. 数据库配置 (database.py)
管理数据库连接和操作相关的配置。

主要配置项：
- 数据库类型
- 连接地址
- 用户名密码
- 连接池大小
- 超时设置

配置示例：
```python
DATABASE_CONFIG = {
    "type": "sqlite",
    "path": "data.db",
    "pool_size": 5,
    "timeout": 30
}
```

## 配置文件结构

### 1. 主配置文件 (config.json)
```json
{
    "database": {
        "type": "sqlite",
        "path": "data.db",
        "pool_size": 5,
        "timeout": 30
    },
    "system": {
        "debug": false,
        "log_level": "INFO",
        "log_path": "logs"
    },
    "security": {
        "token_expire": 7200,
        "password_salt": "your_salt"
    },
    "api": {
        "base_url": "https://api.example.com",
        "timeout": 30
    }
}
```

### 2. 环境变量配置
系统支持通过环境变量覆盖配置文件中的设置：

```bash
export DB_TYPE=mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=password
```

## 配置管理

### 1. 配置加载
```python
from src.config import load_config

config = load_config()
```

### 2. 配置访问
```python
# 获取数据库配置
db_config = config.get("database")

# 获取特定配置项
log_level = config.get("system.log_level")
```

### 3. 配置更新
```python
# 更新配置
config.set("system.debug", True)

# 保存配置
config.save()
```

## 配置验证

### 1. 必填项验证
```python
required_fields = [
    "database.type",
    "database.path",
    "system.log_level"
]

config.validate(required_fields)
```

### 2. 类型验证
```python
type_validations = {
    "database.pool_size": int,
    "system.debug": bool,
    "api.timeout": int
}

config.validate_types(type_validations)
```

### 3. 值范围验证
```python
range_validations = {
    "database.pool_size": (1, 20),
    "api.timeout": (1, 60)
}

config.validate_ranges(range_validations)
```

## 配置继承

### 1. 默认配置
```python
DEFAULT_CONFIG = {
    "system": {
        "debug": False,
        "log_level": "INFO"
    }
}
```

### 2. 环境特定配置
```python
ENV_CONFIGS = {
    "development": {
        "system": {
            "debug": True
        }
    },
    "production": {
        "system": {
            "debug": False
        }
    }
}
```

## 配置安全

### 1. 敏感信息加密
```python
# 加密配置
config.encrypt_sensitive(["database.password", "api.key"])

# 解密配置
password = config.decrypt("database.password")
```

### 2. 配置备份
```python
# 备份配置
config.backup()

# 恢复配置
config.restore("backup_20240313.json")
```

## 使用示例

### 1. 初始化配置
```python
from src.config import ConfigManager

config = ConfigManager()
config.load()
```

### 2. 获取配置
```python
# 获取数据库配置
db_config = config.get_database_config()

# 获取系统配置
system_config = config.get_system_config()
```

### 3. 更新配置
```python
# 更新单个配置项
config.set("system.debug", True)

# 批量更新配置
config.update({
    "system": {
        "debug": True,
        "log_level": "DEBUG"
    }
})
```

## 注意事项
1. 配置文件不要包含敏感信息
2. 使用环境变量管理敏感信息
3. 定期备份配置文件
4. 验证配置的有效性
5. 注意配置的继承关系
6. 保持配置的一致性
7. 记录配置变更日志
8. 实现配置回滚机制 