# 核心模块文档

## 概述
核心模块包含了系统的主要业务逻辑和管理功能，包括数据库管理、认证管理、配置管理、任务管理等核心功能。

## 核心类说明

### 1. 数据库管理 (database.py)
负责数据库连接、表结构管理和数据操作。

主要功能：
- 数据库连接管理
- 表结构创建和维护
- 数据 CRUD 操作
- 数据库迁移

### 2. 认证管理 (auth_manager.py)
处理用户认证和权限控制。

主要功能：
- 用户登录认证
- 权限验证
- Token 管理
- 会话管理

### 3. 配置管理 (config_manager.py)
管理系统配置和参数。

主要功能：
- 配置文件读写
- 配置参数管理
- 环境变量管理
- 配置验证

### 4. 任务管理 (task_manager.py)
管理系统后台任务。

主要功能：
- 任务调度
- 任务状态管理
- 任务执行监控
- 任务日志记录

### 5. 直播管理 (live_viewer_manager.py)
管理直播相关功能。

主要功能：
- 直播创建
- 直播状态管理
- 观众管理
- 直播数据统计

### 6. Token 管理 (token_manager.py)
管理企业微信 API 的 access_token。

主要功能：
- Token 获取
- Token 刷新
- Token 缓存
- Token 状态监控

### 7. 签到导入管理 (sign_import_manager.py)
处理签到数据的导入。

主要功能：
- Excel 文件解析
- 数据验证
- 数据导入
- 错误处理

### 8. IP 记录管理 (ip_record_manager.py)
管理 IP 地址记录。

主要功能：
- IP 记录
- IP 验证
- IP 黑名单管理
- IP 统计

### 9. 同步管理 (sync_manager.py)
处理数据同步。

主要功能：
- 数据同步
- 冲突处理
- 同步状态管理
- 同步日志

### 10. 统计管理 (stats_manager.py)
处理数据统计。

主要功能：
- 数据统计
- 报表生成
- 趋势分析
- 数据导出

### 11. 权限管理 (permission_manager.py)
管理系统权限。

主要功能：
- 权限定义
- 权限分配
- 权限验证
- 权限继承

### 12. 用户管理 (user_manager.py)
管理用户信息。

主要功能：
- 用户信息管理
- 用户状态管理
- 用户配置管理
- 用户日志

### 13. 导出管理 (export_manager.py)
处理数据导出。

主要功能：
- 数据导出
- 导出格式管理
- 导出任务管理
- 导出日志

### 14. 备份管理 (backup_manager.py)
管理系统备份。

主要功能：
- 数据备份
- 备份恢复
- 备份计划
- 备份验证

### 15. 导入管理 (import_manager.py)
处理数据导入。

主要功能：
- 数据导入
- 导入验证
- 导入任务管理
- 导入日志

### 16. 观众统计管理 (viewer_stats_manager.py)
管理观众统计数据。

主要功能：
- 观众统计
- 观看时长统计
- 互动统计
- 数据报表

## 模块间关系
1. 数据库模块作为基础，为其他模块提供数据存储支持
2. 认证模块和权限模块共同负责系统安全
3. 配置模块为其他模块提供配置支持
4. 任务模块负责协调各个模块的异步操作
5. 统计模块和导出模块负责数据处理和展示

## 使用示例

### 1. 数据库操作
```python
from src.core.database import Database

db = Database()
# 执行查询
result = db.query("SELECT * FROM users")
# 执行更新
db.update("UPDATE users SET status = ?", (1,))
```

### 2. 认证管理
```python
from src.core.auth_manager import AuthManager

auth = AuthManager()
# 用户登录
token = auth.login(username, password)
# 验证权限
has_permission = auth.check_permission(user_id, permission)
```

### 3. 配置管理
```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
# 获取配置
value = config.get("database.host")
# 更新配置
config.set("database.host", "localhost")
```

## 注意事项
1. 所有核心模块都应该进行适当的错误处理
2. 关键操作需要记录日志
3. 注意模块间的依赖关系
4. 定期检查和维护数据库连接
5. 注意配置信息的安全性 