# API 模块文档

## 概述
API 模块主要负责与企业微信服务器进行通信，封装了所有企业微信相关的接口调用。该模块提供了统一的接口调用方式，包含了错误处理、性能监控、日志记录等功能。

## 核心类

### WeComAPI
企业微信 API 的主要封装类，提供了所有与企业微信服务器交互的方法。

#### 初始化
```python
def __init__(self, corpid: str, corpsecret: str):
    """
    初始化企业微信 API 客户端
    
    Args:
        corpid: 企业ID
        corpsecret: 企业应用Secret
    """
```

#### 主要方法

##### 1. 创建直播
```python
def create_live(self, anchor_userid: str, theme: str, living_start: int, 
               living_duration: int, type: int = 3, description: str = "") -> Dict[str, Any]:
    """
    创建直播
    
    Args:
        anchor_userid: 主播用户ID
        theme: 直播主题
        living_start: 直播开始时间戳
        living_duration: 直播时长(秒)
        type: 直播类型，默认3(企业培训)
        description: 直播描述
        
    Returns:
        Dict[str, Any]: 接口返回结果
    """
```

##### 2. 获取直播详情
```python
def get_living_info(self, livingid: str) -> Dict[str, Any]:
    """
    获取直播详情
    
    Args:
        livingid: 直播ID
        
    Returns:
        Dict[str, Any]: 直播详情信息
    """
```

##### 3. 获取用户直播列表
```python
def get_user_all_livingid(self, userid: str, cursor: str = "", limit: int = 20) -> Dict[str, Any]:
    """
    获取用户直播列表
    
    Args:
        userid: 用户ID
        cursor: 分页游标
        limit: 每页数量
        
    Returns:
        Dict[str, Any]: 直播列表信息
    """
```

##### 4. 获取直播观看明细
```python
def get_watch_stat(self, livingid: str, next_key: str = "") -> Dict[str, Any]:
    """
    获取直播观看明细
    
    Args:
        livingid: 直播ID
        next_key: 分页游标
        
    Returns:
        Dict[str, Any]: 观看明细信息
    """
```

##### 5. 取消预约直播
```python
def cancel_living(self, livingid: str) -> Dict[str, Any]:
    """
    取消预约直播
    
    Args:
        livingid: 直播ID
        
    Returns:
        Dict[str, Any]: 操作结果
    """
```

##### 6. 测试连接
```python
def test_connection(self) -> bool:
    """
    测试企业微信接口连接
    
    Returns:
        bool: 连接是否成功
    """
```

#### 统计功能

##### 1. 获取 API 统计信息
```python
def get_api_stats(self) -> dict:
    """
    获取 API 调用统计信息
    
    Returns:
        dict: 统计信息，包含：
            - total_calls: 总调用次数
            - success_calls: 成功次数
            - error_calls: 失败次数
            - success_rate: 成功率
            - last_error: 最后一次错误
            - last_error_time: 错误时间
            - api_call_times: 各接口调用次数
            - token_stats: Token 统计信息
    """
```

##### 2. 记录统计信息
```python
def log_api_stats(self):
    """
    记录 API 调用统计信息到日志
    """
```

## 错误处理
- 所有 API 调用都包含在 try-except 块中
- 使用 ErrorHandler 类统一处理错误
- 详细的错误日志记录

## 性能监控
- 使用 PerformanceManager 类监控 API 调用性能
- 记录每个接口的响应时间
- 统计接口调用成功率

## 使用示例

```python
# 初始化 API 客户端
api = WeComAPI(corpid="your_corpid", corpsecret="your_corpsecret")

# 创建直播
result = api.create_live(
    anchor_userid="user123",
    theme="测试直播",
    living_start=1234567890,
    living_duration=3600
)

# 获取直播详情
live_info = api.get_living_info(result["livingid"])

# 获取用户直播列表
user_lives = api.get_user_all_livingid("user123")

# 获取观看明细
watch_stats = api.get_watch_stat(result["livingid"])

# 查看 API 统计信息
stats = api.get_api_stats()
```

## 注意事项
1. 所有 API 调用都需要有效的 access_token
2. 注意处理 API 调用频率限制
3. 妥善保管企业微信的 Secret 信息
4. 建议定期检查 API 统计信息，及时发现异常 