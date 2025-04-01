# 模型模块文档

## 概述
模型模块定义了系统的数据模型，包括用户、直播、签到等核心业务实体。这些模型类负责数据的存储、验证和业务逻辑处理。

## 系统配置

系统采用灵活的配置机制，在应用首次启动时通过初始化向导让用户选择配置：

### 配置路径
- 默认配置路径：`~/.wecom_live_sign_system/`
- 用户可以在初始化向导中自定义配置路径、数据路径、日志路径和备份路径
- 配置信息存储在 `~/.wecom_live_sign_system/config.json` 中
- 启动器(launcher.py)不直接处理配置，而是将配置处理委托给主程序(src/main.py)

### 数据库文件
- 默认位置：用户指定的数据目录下的 `data.db`
- 可通过初始化向导自定义数据库文件名和位置
- 通过 SQLAlchemy ORM 进行访问

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
管理直播观看者信息。请参考 [LiveViewer.md](LiveViewer.md) 了解详细信息。

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
管理签到信息。注意：该模型的部分功能已迁移到 `LiveViewer` 模型中，请参考模型迁移文档 [README_MODEL_MIGRATION.md](README_MODEL_MIGRATION.md)。

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

### 7. 配置模型 (settings.py)
管理系统配置信息。

主要字段：
- key: 配置键
- value: 配置值
- type: 配置类型
- description: 描述
- created_at: 创建时间
- updated_at: 更新时间

主要方法：
```python
class Settings(BaseModel):
    def get(self, key, default=None):
        """获取配置值"""
        
    def set(self, key, value, type=None, description=None):
        """设置配置值"""
        
    def delete(self, key):
        """删除配置"""
        
    def get_all(self):
        """获取所有配置"""
```

### 8. 企业模型 (corporation.py)
管理企业信息。

主要字段：
- corp_id: 企业ID
- name: 企业名称
- corp_secret: 企业应用Secret
- agent_id: 应用ID
- status: 状态

主要方法：
```python
class Corporation(BaseModel):
    def create(self, data):
        """创建企业信息"""
        
    def update(self, corp_id, data):
        """更新企业信息"""
        
    def get_by_id(self, corp_id):
        """根据ID获取企业信息"""
        
    def get_token(self):
        """获取企业微信访问令牌"""
```

## 模型关系

模型之间的主要关系如下：

1. 企业 (Corporation) 与 用户 (User)：一对多
2. 直播 (Live) 与 观看者 (LiveViewer)：一对多
3. 用户 (User) 与 直播预约 (LiveBooking)：一对多
4. 直播 (Live) 与 签到 (Sign)：一对多

## 数据访问

系统使用 SQLAlchemy ORM 进行数据访问，主要特点：

1. 连接池管理
2. 事务支持
3. 惰性加载
4. 级联操作

示例：
```python
# 创建会话
with db.get_session() as session:
    # 查询用户
    user = session.query(User).filter_by(username="example").first()
    
    # 创建直播
    live = Live(
        title="示例直播",
        anchor_id=user.id,
        start_time=datetime.now(),
        duration=3600
    )
    
    # 保存到数据库
    session.add(live)
    session.commit()
```

## 数据迁移

系统支持数据模型升级和迁移。当模型结构发生变化时，可以使用迁移工具进行数据迁移。详细信息请参考 [README_MODEL_MIGRATION.md](README_MODEL_MIGRATION.md)。

## 注意事项
1. 模型类应该保持单一职责
2. 注意数据验证的完整性
3. 合理使用缓存机制
4. 注意数据一致性
5. 实现适当的错误处理
6. 保持代码的可维护性
7. 添加详细的注释
8. 编写单元测试 