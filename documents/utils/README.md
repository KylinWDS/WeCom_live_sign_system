# 工具模块文档

## 概述
工具模块提供了系统所需的各种通用工具类，包括日志记录、错误处理、缓存管理、安全工具等。这些工具类被其他模块广泛使用，提供了基础的功能支持。

## 核心工具类

### 1. 日志工具 (logger.py)
提供系统日志记录功能。

主要功能：
- 日志级别管理
- 日志格式配置
- 日志文件管理
- 日志轮转
- 日志过滤

使用示例：
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("这是一条信息日志")
logger.error("这是一条错误日志")
```

### 2. 缓存管理 (cache_manager.py)
管理系统缓存。

主要功能：
- 内存缓存
- 文件缓存
- 缓存过期
- 缓存清理
- 缓存统计

使用示例：
```python
from src.utils.cache_manager import CacheManager

cache = CacheManager()
cache.set("key", "value", expire=3600)
value = cache.get("key")
```

### 3. 错误处理 (error_handler.py)
统一处理系统错误。

主要功能：
- 错误捕获
- 错误分类
- 错误日志
- 错误恢复
- 错误通知

使用示例：
```python
from src.utils.error_handler import ErrorHandler

error_handler = ErrorHandler()
try:
    # 可能出错的代码
    pass
except Exception as e:
    error_handler.handle_error(e, "操作描述")
```

### 4. 安全工具 (security.py)
提供安全相关功能。

主要功能：
- 密码加密
- 数据加密
- 安全验证
- 权限检查
- 安全审计

使用示例：
```python
from src.utils.security import SecurityManager

security = SecurityManager()
encrypted = security.encrypt("敏感数据")
decrypted = security.decrypt(encrypted)
```

### 5. 异步工具 (async_utils.py)
处理异步操作。

主要功能：
- 异步任务
- 并发控制
- 任务调度
- 异步队列
- 异步监控

使用示例：
```python
from src.utils.async_utils import AsyncManager

async_manager = AsyncManager()
async_manager.run_async(my_async_function)
```

### 6. 认证工具 (auth.py)
处理认证相关功能。

主要功能：
- 用户认证
- Token 管理
- 会话管理
- 权限验证
- 认证日志

使用示例：
```python
from src.utils.auth import AuthManager

auth = AuthManager()
token = auth.generate_token(user_id)
is_valid = auth.validate_token(token)
```

### 7. 加密工具 (crypto.py)
提供加密解密功能。

主要功能：
- 对称加密
- 非对称加密
- 哈希计算
- 签名验证
- 密钥管理

使用示例：
```python
from src.utils.crypto import CryptoManager

crypto = CryptoManager()
encrypted = crypto.encrypt("数据")
decrypted = crypto.decrypt(encrypted)
```

### 8. 数据库监控 (db_monitor.py)
监控数据库状态。

主要功能：
- 连接监控
- 性能监控
- 状态检查
- 告警通知
- 统计报告

使用示例：
```python
from src.utils.db_monitor import DBMonitor

monitor = DBMonitor()
monitor.start_monitoring()
```

### 9. 网络工具 (network.py)
处理网络相关操作。

主要功能：
- HTTP 请求
- 网络状态
- 连接管理
- 超时控制
- 重试机制

使用示例：
```python
from src.utils.network import NetworkManager

network = NetworkManager()
response = network.get("https://api.example.com")
```

### 10. 重试工具 (retry.py)
提供重试机制。

主要功能：
- 重试策略
- 退避算法
- 超时控制
- 错误处理
- 重试日志

使用示例：
```python
from src.utils.retry import RetryManager

retry = RetryManager()
result = retry.execute(my_function, max_retries=3)
```

## 工具类使用规范

### 1. 日志记录
- 使用适当的日志级别
- 包含足够的上下文信息
- 避免敏感信息泄露
- 定期清理日志文件

### 2. 缓存使用
- 合理设置缓存过期时间
- 注意内存使用
- 及时清理过期缓存
- 监控缓存命中率

### 3. 错误处理
- 统一使用错误处理器
- 提供详细的错误信息
- 实现错误恢复机制
- 记录错误日志

### 4. 安全考虑
- 加密敏感数据
- 验证用户输入
- 防止 SQL 注入
- 实现访问控制

### 5. 异步操作
- 合理使用异步
- 控制并发数量
- 处理异步异常
- 监控异步任务

## 注意事项
1. 工具类应该是无状态的
2. 避免循环依赖
3. 保持接口稳定
4. 注意性能影响
5. 做好异常处理
6. 保持代码简洁
7. 添加详细注释
8. 编写单元测试 