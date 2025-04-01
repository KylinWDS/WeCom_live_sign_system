# API 模块文档

## 概述
API 模块提供了系统与企业微信进行交互的接口实现，主要负责企业微信认证、用户信息获取、直播管理、数据同步等功能。该模块封装了企业微信开放平台的API接口，提供了简单易用的方法供系统其他模块调用。

## 与启动器的集成

API模块在系统启动过程中由AppContext进行初始化，并且所有耗时的API操作都在后台线程中执行，避免阻塞UI线程。启动器通过进度条展示API初始化的进度，提升用户体验。

## 目录结构

### 1. 客户端 (client/)
企业微信API客户端实现。

主要内容：
- HTTP客户端
- WebSocket客户端
- 重试机制
- 错误处理
- 请求限流
- 响应缓存

### 2. 模型 (models/)
API相关的数据模型。

主要模型：
- 企业微信用户模型 (WeComUser)
- 企业微信部门模型 (WeComDepartment)
- 企业微信直播模型 (WeComLive)
- 企业微信媒体模型 (WeComMedia)
- 企业微信消息模型 (WeComMessage)
- 企业微信令牌模型 (WeComToken)

### 3. 服务 (services/)
封装的API服务。

主要服务：
- 认证服务 (AuthService)
- 用户服务 (UserService)
- 部门服务 (DepartmentService)
- 直播服务 (LiveService)
- 媒体服务 (MediaService)
- 消息服务 (MessageService)
- 统计服务 (StatisticsService)

### 4. 工具 (utils/)
API相关的工具函数。

主要工具：
- 签名工具 (SignatureUtils)
- 加密工具 (EncryptionUtils)
- URL工具 (UrlUtils)
- 参数工具 (ParamUtils)
- 响应工具 (ResponseUtils)
- 错误处理工具 (ErrorUtils)

## 主要功能

### 1. 认证管理
- 获取访问令牌
- 刷新访问令牌
- 验证访问令牌有效性
- 处理认证错误
- 多应用凭证管理
- 自动重试认证

```python
# 获取访问令牌
async def get_access_token(self):
    """获取企业微信访问令牌"""
    url = f"{self.base_url}/gettoken"
    params = {
        "corpid": self.corp_id,
        "corpsecret": self.corp_secret
    }
    
    response = await self.client.get(url, params=params)
    data = response.json()
    
    if data.get("errcode") == 0:
        token = data.get("access_token")
        expires_in = data.get("expires_in", 7200)
        self.token_manager.update_token(token, expires_in)
        return token
    else:
        raise WeComAPIError(
            f"获取访问令牌失败: {data.get('errmsg', '未知错误')}"
        )
```

### 2. 用户管理
- 获取用户列表
- 获取用户详情
- 部门用户查询
- 用户信息同步
- 用户标签管理
- 用户状态查询

### 3. 部门管理
- 获取部门列表
- 获取部门详情
- 部门层级管理
- 部门信息同步
- 部门用户关系管理
- 部门结构查询

### 4. 直播管理
- 获取直播列表
- 获取直播详情
- 获取观看数据
- 获取直播回放
- 获取直播统计
- 直播状态监控

```python
# 获取直播详情
async def get_live_info(self, live_id):
    """获取企业微信直播详情"""
    url = f"{self.base_url}/living/get_living_info"
    params = {
        "access_token": await self.get_access_token()
    }
    data = {
        "livingid": live_id
    }
    
    response = await self.client.post(url, params=params, json=data)
    result = response.json()
    
    if result.get("errcode") == 0:
        return WeComLive.from_dict(result)
    else:
        raise WeComAPIError(
            f"获取直播详情失败: {result.get('errmsg', '未知错误')}"
        )
```

### 5. 消息管理
- 发送文本消息
- 发送图片消息
- 发送视频消息
- 发送文件消息
- 发送卡片消息
- 发送模板消息
- 消息撤回管理
- 消息已读状态

### 6. 统计管理
- 获取直播统计
- 获取观看者统计
- 获取互动数据
- 获取转发数据
- 获取回放数据
- 自定义统计报表

## 线程安全

API模块实现了线程安全的设计，确保在多线程环境下正常工作：

1. **线程锁保护**: 使用锁保护并发访问的关键数据
2. **异步请求**: 使用非阻塞的异步HTTP请求
3. **请求队列**: 请求限流和优先级排序
4. **令牌缓存**: 线程安全的令牌缓存和刷新机制
5. **隔离状态**: 每个服务实例维护独立状态

```python
class ThreadSafeTokenManager:
    def __init__(self):
        self._token = None
        self._expires_at = 0
        self._lock = threading.RLock()
        
    def get_token(self):
        """获取当前令牌（如果有效）"""
        with self._lock:
            if time.time() < self._expires_at - 300:  # 预留5分钟刷新时间
                return self._token
            return None
            
    def update_token(self, token, expires_in):
        """更新令牌及其过期时间"""
        with self._lock:
            self._token = token
            self._expires_at = time.time() + expires_in
```

## 错误处理

API模块实现了完善的错误处理机制：

1. **自定义异常类**: 针对不同API错误定义特定异常
2. **重试策略**: 自动重试临时性错误
3. **降级机制**: 在API不可用时使用本地缓存
4. **日志记录**: 详细记录错误信息
5. **用户友好提示**: 将技术错误转换为用户可理解的信息

```python
class WeComAPIError(Exception):
    """企业微信API错误"""
    def __init__(self, message, error_code=None, request_id=None):
        super().__init__(message)
        self.error_code = error_code
        self.request_id = request_id
        
class AuthenticationError(WeComAPIError):
    """认证错误"""
    pass
    
class RateLimitError(WeComAPIError):
    """请求频率限制错误"""
    pass
    
class ServerError(WeComAPIError):
    """服务器错误"""
    pass
    
class ClientError(WeComAPIError):
    """客户端错误"""
    pass
```

## 配置管理

API模块支持灵活的配置管理：

1. **多环境配置**: 支持开发、测试、生产环境
2. **动态配置**: 支持运行时修改配置
3. **加密配置**: 敏感信息加密存储
4. **配置验证**: 验证配置有效性
5. **默认值**: 提供合理默认配置

```python
class APIConfig:
    def __init__(self, env="production"):
        self.env = env
        self._config = self._load_config()
        
    def _load_config(self):
        """加载配置"""
        config_path = f"config/api_{self.env}.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return self._default_config()
            
    def _default_config(self):
        """默认配置"""
        return {
            "base_url": "https://qyapi.weixin.qq.com/cgi-bin",
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2,
            "enable_cache": True,
            "cache_ttl": 3600
        }
        
    def get(self, key, default=None):
        """获取配置项"""
        return self._config.get(key, default)
```

## 性能优化

API模块采用多种性能优化策略：

1. **连接池**: 重用HTTP连接
2. **响应缓存**: 缓存常用请求结果
3. **批量请求**: 合并多个请求为一次操作
4. **压缩传输**: 使用gzip压缩
5. **异步处理**: 非阻塞API调用

```python
class CacheableAPIClient:
    def __init__(self, base_url, cache_ttl=3600):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=20
        ))
        self.cache = {}
        self.cache_ttl = cache_ttl
        
    def get(self, url, params=None, use_cache=True):
        """发送GET请求，支持缓存"""
        if use_cache:
            cache_key = self._get_cache_key(url, params)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
                
        response = self.session.get(
            url, 
            params=params,
            headers={"Accept-Encoding": "gzip"}
        )
        
        if use_cache and response.status_code == 200:
            self._add_to_cache(cache_key, response)
            
        return response
        
    def _get_cache_key(self, url, params):
        """生成缓存键"""
        return f"{url}:{json.dumps(params or {})}"
        
    def _get_from_cache(self, key):
        """从缓存获取响应"""
        if key in self.cache:
            timestamp, response = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return response
            else:
                del self.cache[key]
        return None
        
    def _add_to_cache(self, key, response):
        """添加响应到缓存"""
        self.cache[key] = (time.time(), response)
```

## 使用示例

### 初始化 API 客户端
```python
from src.api.client.wecom_client import WeComClient

# 初始化客户端
client = WeComClient(
    corp_id="your_corp_id",
    corp_secret="your_corp_secret"
)
```

### 获取用户列表
```python
from src.api.services.user_service import UserService

# 初始化用户服务
user_service = UserService(client)

# 获取部门用户
users = user_service.get_department_users(department_id=1, recursive=True)
```

### 获取直播信息
```python
from src.api.services.live_service import LiveService

# 初始化直播服务
live_service = LiveService(client)

# 获取直播列表
lives = live_service.get_lives(start_time=yesterday, end_time=today)

# 获取直播详情
live_info = live_service.get_live_info(live_id="live123456")
```

### 发送消息
```python
from src.api.services.message_service import MessageService

# 初始化消息服务
message_service = MessageService(client)

# 发送文本消息
message_service.send_text(
    user_ids=["user1", "user2"],
    content="直播将于明天14:00开始，请准时参加！"
)
```

## 注意事项

1. **API 调用频率**: 遵循企业微信API调用频率限制
2. **令牌管理**: 正确管理和刷新访问令牌
3. **错误处理**: 实现全面的错误处理机制
4. **数据安全**: 保护敏感数据和凭证
5. **异步处理**: 长时间运行的API调用应放在后台线程
6. **缓存策略**: 合理使用缓存避免重复请求
7. **降级策略**: 当API不可用时实现降级机制
8. **日志记录**: 记录API调用情况，便于排查问题 