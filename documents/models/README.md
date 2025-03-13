# 模型模块文档

## 概述
模型模块定义了系统的数据模型，包括用户、直播、签到等核心业务实体。这些模型类负责数据的存储、验证和业务逻辑处理。

## 基础模型

### 1. 基础模型类 (base.py)
所有模型的基类，提供通用的模型功能。

主要功能：
- 数据库连接管理
- 模型验证
- 数据转换
- 错误处理

```python
class BaseModel:
    def __init__(self):
        self.db = Database()
        self.validator = ModelValidator()
```

## 核心模型

### 1. 用户模型 (user.py)
管理用户信息。

主要字段：
- user_id: 用户ID
- username: 用户名
- password: 密码
- role: 角色
- status: 状态

主要方法：
```python
class User(BaseModel):
    def create(self, data):
        """创建用户"""
        
    def update(self, user_id, data):
        """更新用户信息"""
        
    def delete(self, user_id):
        """删除用户"""
        
    def get_by_id(self, user_id):
        """根据ID获取用户"""
```

### 2. 部门模型 (department.py)
管理部门信息。

主要字段：
- dept_id: 部门ID
- name: 部门名称
- parent_id: 父部门ID
- order: 排序

主要方法：
```python
class Department(BaseModel):
    def create(self, data):
        """创建部门"""
        
    def get_tree(self):
        """获取部门树"""
        
    def get_children(self, dept_id):
        """获取子部门"""
```

### 3. 直播模型 (live.py)
管理直播信息。

主要字段：
- live_id: 直播ID
- title: 直播标题
- anchor_id: 主播ID
- start_time: 开始时间
- duration: 时长
- status: 状态

主要方法：
```python
class Live(BaseModel):
    def create(self, data):
        """创建直播"""
        
    def update_status(self, live_id, status):
        """更新直播状态"""
        
    def get_details(self, live_id):
        """获取直播详情"""
```

### 4. 直播预约模型 (live_booking.py)
管理直播预约信息。

主要字段：
- booking_id: 预约ID
- live_id: 直播ID
- user_id: 预约用户ID
- booking_time: 预约时间
- status: 状态

主要方法：
```python
class LiveBooking(BaseModel):
    def create(self, data):
        """创建预约"""
        
    def cancel(self, booking_id):
        """取消预约"""
        
    def get_user_bookings(self, user_id):
        """获取用户预约列表"""
```

### 5. 直播观看者模型 (live_viewer.py)
管理直播观看者信息。

主要字段：
- viewer_id: 观看者ID
- live_id: 直播ID
- user_id: 用户ID
- watch_time: 观看时长
- join_time: 加入时间

主要方法：
```python
class LiveViewer(BaseModel):
    def record_view(self, data):
        """记录观看"""
        
    def get_viewer_stats(self, live_id):
        """获取观看统计"""
        
    def get_user_views(self, user_id):
        """获取用户观看记录"""
```

### 6. 签到模型 (sign.py)
管理签到信息。

主要字段：
- sign_id: 签到ID
- live_id: 直播ID
- user_id: 用户ID
- sign_time: 签到时间
- status: 状态

主要方法：
```python
class Sign(BaseModel):
    def create(self, data):
        """创建签到记录"""
        
    def get_user_signs(self, user_id):
        """获取用户签到记录"""
        
    def get_live_signs(self, live_id):
        """获取直播签到记录"""
```

### 7. 签到记录模型 (sign_record.py)
管理详细的签到记录。

主要字段：
- record_id: 记录ID
- sign_id: 签到ID
- user_id: 用户ID
- record_time: 记录时间
- record_type: 记录类型

主要方法：
```python
class SignRecord(BaseModel):
    def create(self, data):
        """创建签到记录"""
        
    def get_user_records(self, user_id):
        """获取用户签到记录"""
        
    def get_live_records(self, live_id):
        """获取直播签到记录"""
```

### 8. 邀请人缓存模型 (invitor_cache.py)
管理邀请人信息缓存。

主要字段：
- cache_id: 缓存ID
- user_id: 用户ID
- invitor_id: 邀请人ID
- cache_time: 缓存时间

主要方法：
```python
class InvitorCache(BaseModel):
    def set(self, user_id, invitor_id):
        """设置缓存"""
        
    def get(self, user_id):
        """获取缓存"""
        
    def clear(self, user_id):
        """清除缓存"""
```

### 9. IP记录模型 (ip_record.py)
管理IP地址记录。

主要字段：
- record_id: 记录ID
- ip: IP地址
- record_time: 记录时间
- record_type: 记录类型

主要方法：
```python
class IPRecord(BaseModel):
    def add(self, ip, record_type):
        """添加记录"""
        
    def get_records(self, ip):
        """获取记录"""
        
    def clear_expired(self):
        """清理过期记录"""
```

### 10. 导出配置模型 (export_config.py)
管理导出配置信息。

主要字段：
- config_id: 配置ID
- name: 配置名称
- fields: 导出字段
- format: 导出格式

主要方法：
```python
class ExportConfig(BaseModel):
    def create(self, data):
        """创建配置"""
        
    def update(self, config_id, data):
        """更新配置"""
        
    def get_config(self, config_id):
        """获取配置"""
```

## 模型关系

### 1. 一对多关系
- 直播 -> 直播观看者
- 直播 -> 签到记录
- 用户 -> 签到记录

### 2. 多对多关系
- 用户 <-> 直播（通过直播观看者）
- 用户 <-> 签到（通过签到记录）

## 数据验证

### 1. 字段验证
```python
class ModelValidator:
    def validate_required(self, data, fields):
        """验证必填字段"""
        
    def validate_type(self, data, field_types):
        """验证字段类型"""
        
    def validate_range(self, data, field_ranges):
        """验证字段范围"""
```

### 2. 业务验证
```python
class BusinessValidator:
    def validate_live_creation(self, data):
        """验证直播创建"""
        
    def validate_sign_in(self, data):
        """验证签到"""
```

## 注意事项
1. 模型类应该保持单一职责
2. 注意数据验证的完整性
3. 合理使用缓存机制
4. 注意数据一致性
5. 实现适当的错误处理
6. 保持代码的可维护性
7. 添加详细的注释
8. 编写单元测试 