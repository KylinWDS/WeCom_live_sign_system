# 核心模块文档

## 概述
核心模块是系统的中枢，负责将各个模块集成在一起，并提供统一的应用程序上下文。该模块处理系统初始化、配置管理、数据库连接、认证、企业微信接口封装等核心功能。

## 与启动器的集成

核心模块与启动器实现了优雅的集成，确保系统启动过程流畅且用户友好。启动器负责展示启动界面和进度，核心模块则负责真正的系统初始化工作。核心模块会向启动器报告初始化进度，使用户能够看到系统启动的详细状态。

## 目录结构

### 1. 上下文 (context/)
应用程序上下文相关类。

主要内容：
- 应用上下文 (AppContext)
- 上下文初始化器 (ContextInitializer)
- 事件总线 (EventBus)
- 模块加载器 (ModuleLoader)
- 服务注册器 (ServiceRegistry)
- 生命周期管理器 (LifecycleManager)

### 2. 数据库 (database/)
数据库相关类。

主要内容：
- 数据库连接器 (DatabaseConnector)
- 连接池管理器 (ConnectionPoolManager)
- 事务管理器 (TransactionManager)
- 数据访问对象 (BaseDAO)
- SQL构建器 (SQLBuilder)
- 迁移管理器 (MigrationManager)

### 3. 认证 (auth/)
认证相关类。

主要内容：
- 认证管理器 (AuthManager)
- 用户认证 (UserAuthenticator)
- 会话管理器 (SessionManager)
- 权限管理器 (PermissionManager)
- 角色管理器 (RoleManager)
- 令牌管理器 (TokenManager)

### 4. 企业微信 (wecom/)
企业微信相关类。

主要内容：
- 企业微信管理器 (WeComManager)
- API客户端 (WeComClient)
- 用户管理器 (WeComUserManager)
- 部门管理器 (WeComDepartmentManager)
- 直播管理器 (WeComLiveManager)
- 媒体管理器 (WeComMediaManager)

### 5. 直播 (live/)
直播相关类。

主要内容：
- 直播管理器 (LiveManager)
- 直播预约 (LiveBookingManager)
- 直播观看者 (LiveViewerManager)
- 直播签到 (LiveSignManager)
- 直播统计 (LiveStatisticsManager)
- 直播导出 (LiveExportManager)

### 6. 用户 (user/)
用户相关类。

主要内容：
- 用户管理器 (UserManager)
- 部门管理器 (DepartmentManager)
- 用户信息同步器 (UserSynchronizer)
- 用户导入导出 (UserImportExport)
- 用户组管理器 (UserGroupManager)
- 用户偏好设置 (UserPreferenceManager)

### 7. 任务 (task/)
任务相关类。

主要内容：
- 任务管理器 (TaskManager)
- 任务调度器 (TaskScheduler)
- 任务执行器 (TaskExecutor)
- 后台任务 (BackgroundTask)
- 周期性任务 (RecurringTask)
- 任务监控器 (TaskMonitor)

### 8. 导入导出 (io/)
导入导出相关类。

主要内容：
- 导入管理器 (ImportManager)
- 导出管理器 (ExportManager)
- 模板管理器 (TemplateManager)
- 数据转换器 (DataConverter)
- 格式器 (Formatter)
- 验证器 (Validator)

## 主要功能

### 1. 应用上下文

应用上下文是系统的核心，负责管理所有模块和服务的生命周期，提供统一的访问点。

```python
class AppContext:
    """应用程序上下文"""
    
    _instance = None
    
    @classmethod
    def instance(cls):
        """获取应用上下文单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """初始化应用上下文"""
        if AppContext._instance is not None:
            raise RuntimeError("AppContext is a singleton!")
            
        self.config = None
        self.database = None
        self.auth_manager = None
        self.wecom_manager = None
        self.live_manager = None
        self.user_manager = None
        self.task_manager = None
        self.export_manager = None
        self.import_manager = None
        
        self.services = {}
        self.event_bus = EventBus()
        self.startup_time = time.time()
        self.initialized = False
        self.version = "1.0.0"
        
    def initialize(self, config_path=None, callback=None):
        """初始化应用上下文"""
        if self.initialized:
            return True
            
        try:
            # 初始化配置
            self._init_config(config_path)
            if callback: 
                callback("配置初始化完成", 10)
                
            # 初始化数据库
            self._init_database()
            if callback:
                callback("数据库连接完成", 30)
                
            # 初始化认证管理器
            self._init_auth_manager()
            if callback:
                callback("认证服务初始化完成", 40)
                
            # 初始化企业微信管理器
            self._init_wecom_manager()
            if callback:
                callback("企业微信服务初始化完成", 50)
                
            # 初始化直播管理器
            self._init_live_manager()
            if callback:
                callback("直播服务初始化完成", 60)
                
            # 初始化用户管理器
            self._init_user_manager()
            if callback:
                callback("用户服务初始化完成", 70)
                
            # 初始化任务管理器
            self._init_task_manager()
            if callback:
                callback("任务服务初始化完成", 80)
                
            # 初始化导入导出管理器
            self._init_io_manager()
            if callback:
                callback("导入导出服务初始化完成", 90)
                
            self.initialized = True
            if callback:
                callback("系统初始化完成", 100)
                
            return True
            
        except Exception as e:
            logger.error(f"初始化应用上下文失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            if callback:
                callback(f"初始化失败: {str(e)}", -1)
            return False
```

### 2. 数据库管理

数据库管理器负责处理数据库连接和所有数据库操作。

```python
class Database:
    """数据库管理器"""
    
    def __init__(self, config):
        """初始化数据库管理器"""
        self.config = config
        self.engine = None
        self.session_factory = None
        self.metadata = Base.metadata
        self._init_engine()
        
    def _init_engine(self):
        """初始化数据库引擎"""
        db_config = self.config.get('database', {})
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            db_path = db_config.get('path', 'data/database.db')
            # 确保目录存在
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.engine = create_engine(
                f'sqlite:///{db_path}',
                connect_args={'check_same_thread': False},
                pool_size=db_config.get('pool_size', 5),
                pool_timeout=db_config.get('timeout', 30)
            )
        else:
            conn_str = db_config.get('connection_string', '')
            if not conn_str:
                raise ValueError("数据库连接字符串不能为空")
            self.engine = create_engine(
                conn_str,
                pool_size=db_config.get('pool_size', 5),
                pool_timeout=db_config.get('timeout', 30)
            )
            
        self.session_factory = sessionmaker(bind=self.engine)
        
    def create_session(self):
        """创建数据库会话"""
        return self.session_factory()
        
    def init_tables(self):
        """初始化数据库表"""
        self.metadata.create_all(self.engine)
        
    def get_session(self):
        """获取数据库会话上下文管理器"""
        return SessionManager(self)
```

### 3. 认证管理

认证管理器负责处理用户认证和权限管理。

```python
class AuthManager:
    """认证管理器"""
    
    def __init__(self, database, config):
        """初始化认证管理器"""
        self.database = database
        self.config = config
        self.session_manager = SessionManager()
        self.permission_manager = PermissionManager()
        self.token_manager = TokenManager(config)
        
    def authenticate(self, username, password):
        """验证用户身份"""
        with self.database.get_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return False, "用户不存在"
                
            if not user.is_active:
                return False, "用户已禁用"
                
            if not PasswordUtils.verify_password(password, user.password):
                return False, "密码错误"
                
            # 生成会话令牌
            token = self.token_manager.generate_token(user.id)
            
            # 记录登录信息
            user.last_login = datetime.now()
            session.commit()
            
            return True, {
                "user_id": user.id,
                "username": user.username,
                "token": token,
                "role": user.role,
                "permissions": self.permission_manager.get_permissions(user.role)
            }
            
    def validate_token(self, token):
        """验证会话令牌"""
        user_id = self.token_manager.validate_token(token)
        if not user_id:
            return False, "无效的令牌或已过期"
            
        with self.database.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "用户不存在"
                
            if not user.is_active:
                return False, "用户已禁用"
                
            return True, {
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "permissions": self.permission_manager.get_permissions(user.role)
            }
```

### 4. 企业微信管理

企业微信管理器负责与企业微信API的交互。

```python
class WeComManager:
    """企业微信管理器"""
    
    def __init__(self, config):
        """初始化企业微信管理器"""
        self.config = config
        self.client = WeComClient(
            corp_id=config.get('wecom.corp_id', ''),
            corp_secret=config.get('wecom.corp_secret', ''),
            agent_id=config.get('wecom.agent_id', '')
        )
        self.user_manager = WeComUserManager(self.client)
        self.department_manager = WeComDepartmentManager(self.client)
        self.live_manager = WeComLiveManager(self.client)
        self.media_manager = WeComMediaManager(self.client)
        
    def test_connection(self):
        """测试企业微信连接"""
        return self.client.test_connection()
        
    def get_access_token(self):
        """获取访问令牌"""
        return self.client.get_token()
```

### 5. 直播管理

直播管理器负责处理直播相关的业务逻辑。

```python
class LiveManager:
    """直播管理器"""
    
    def __init__(self, database, wecom_manager):
        """初始化直播管理器"""
        self.database = database
        self.wecom_manager = wecom_manager
        self.booking_manager = LiveBookingManager(database, wecom_manager)
        self.viewer_manager = LiveViewerManager(database)
        self.sign_manager = LiveSignManager(database)
        self.statistics_manager = LiveStatisticsManager(database)
        
    def sync_lives(self, start_time=None, end_time=None):
        """同步直播数据"""
        try:
            # 获取时间范围
            if start_time is None:
                # 默认同步近30天的直播
                end_time = int(time.time())
                start_time = end_time - 30 * 24 * 3600
                
            # 从企业微信获取直播列表
            lives = self.wecom_manager.live_manager.get_lives(
                start_time=start_time, 
                end_time=end_time
            )
            
            # 更新数据库
            with self.database.get_session() as session:
                for live_data in lives:
                    # 查询是否已存在
                    live = session.query(Live).filter(
                        Live.living_id == live_data['livingid']
                    ).first()
                    
                    if live:
                        # 更新现有记录
                        live.theme = live_data['theme']
                        live.living_start = live_data['living_start']
                        live.living_duration = live_data['living_duration']
                        live.status = live_data['status']
                        live.anchor_userid = live_data['anchor_userid']
                        live.viewer_num = live_data.get('viewer_num', 0)
                        live.comment_num = live_data.get('comment_num', 0)
                        live.like_num = live_data.get('like_num', 0)
                    else:
                        # 创建新记录
                        live = Live(
                            living_id=live_data['livingid'],
                            theme=live_data['theme'],
                            living_start=live_data['living_start'],
                            living_duration=live_data['living_duration'],
                            status=live_data['status'],
                            anchor_userid=live_data['anchor_userid'],
                            viewer_num=live_data.get('viewer_num', 0),
                            comment_num=live_data.get('comment_num', 0),
                            like_num=live_data.get('like_num', 0)
                        )
                        session.add(live)
                        
                session.commit()
                
            return len(lives)
            
        except Exception as e:
            logger.error(f"同步直播数据失败: {str(e)}")
            raise
```

### 6. 用户管理

用户管理器负责处理用户和部门相关的业务逻辑。

```python
class UserManager:
    """用户管理器"""
    
    def __init__(self, database, wecom_manager):
        """初始化用户管理器"""
        self.database = database
        self.wecom_manager = wecom_manager
        self.department_manager = DepartmentManager(database, wecom_manager)
        self.user_synchronizer = UserSynchronizer(database, wecom_manager)
        
    def sync_users(self, department_id=1, recursive=True):
        """同步用户数据"""
        try:
            return self.user_synchronizer.sync_department_users(
                department_id=department_id,
                recursive=recursive
            )
        except Exception as e:
            logger.error(f"同步用户数据失败: {str(e)}")
            raise
            
    def get_user(self, user_id):
        """获取用户信息"""
        with self.database.get_session() as session:
            user = session.query(User).filter(User.userid == user_id).first()
            if user:
                return user.to_dict()
            return None
            
    def get_users_by_department(self, department_id, recursive=False):
        """获取部门用户列表"""
        with self.database.get_session() as session:
            query = session.query(User).filter(
                User.department.contains(str(department_id))
            )
            
            if recursive:
                # 获取所有子部门
                child_departments = self.department_manager.get_child_departments(
                    department_id
                )
                
                # 构建查询条件
                conditions = [User.department.contains(str(dept_id)) 
                             for dept_id in child_departments]
                             
                if conditions:
                    query = query.union(
                        session.query(User).filter(or_(*conditions))
                    )
                    
            users = query.all()
            return [user.to_dict() for user in users]
```

### 7. 任务管理

任务管理器负责处理后台任务和定时任务。

```python
class TaskManager:
    """任务管理器"""
    
    def __init__(self, app_context):
        """初始化任务管理器"""
        self.app_context = app_context
        self.scheduler = TaskScheduler()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.tasks = {}
        self.running_tasks = {}
        
    def start(self):
        """启动任务管理器"""
        self.scheduler.start()
        self._init_recurring_tasks()
        
    def stop(self):
        """停止任务管理器"""
        self.scheduler.shutdown()
        self.executor.shutdown(wait=False)
        
    def _init_recurring_tasks(self):
        """初始化定期任务"""
        # 每天凌晨2点同步直播数据
        self.scheduler.add_job(
            self._sync_lives_task,
            'cron',
            hour=2,
            minute=0,
            id='sync_lives'
        )
        
        # 每小时同步用户数据
        self.scheduler.add_job(
            self._sync_users_task,
            'interval',
            hours=1,
            id='sync_users'
        )
        
    def submit_task(self, task_func, *args, **kwargs):
        """提交任务"""
        task_id = str(uuid.uuid4())
        future = self.executor.submit(task_func, *args, **kwargs)
        self.tasks[task_id] = future
        return task_id
        
    def get_task_status(self, task_id):
        """获取任务状态"""
        if task_id not in self.tasks:
            return {"status": "not_found"}
            
        future = self.tasks[task_id]
        if future.done():
            if future.exception():
                return {
                    "status": "error",
                    "error": str(future.exception())
                }
            else:
                return {
                    "status": "completed",
                    "result": future.result()
                }
        else:
            return {"status": "running"}
```

### 8. 导入导出管理

导入导出管理器负责处理数据的导入和导出。

```python
class ExportManager:
    """导出管理器"""
    
    def __init__(self, database, config):
        """初始化导出管理器"""
        self.database = database
        self.config = config
        self.export_path = config.get('system.export_path', 'exports')
        os.makedirs(self.export_path, exist_ok=True)
        self.template_manager = TemplateManager(config)
        
    def export_live_data(self, live_id, export_format="excel"):
        """导出直播数据"""
        try:
            with self.database.get_session() as session:
                # 获取直播信息
                live = session.query(Live).filter(Live.id == live_id).first()
                if not live:
                    raise ValueError(f"直播不存在: {live_id}")
                    
                # 获取观看者数据
                viewers = session.query(LiveViewer).filter(
                    LiveViewer.live_id == live_id
                ).all()
                
                # 准备导出数据
                export_data = {
                    "live_info": live.to_dict(),
                    "viewers": [viewer.to_dict() for viewer in viewers]
                }
                
                # 根据格式导出
                if export_format == "excel":
                    return self._export_to_excel(export_data, live.theme)
                elif export_format == "csv":
                    return self._export_to_csv(export_data, live.theme)
                elif export_format == "json":
                    return self._export_to_json(export_data, live.theme)
                else:
                    raise ValueError(f"不支持的导出格式: {export_format}")
                    
        except Exception as e:
            logger.error(f"导出直播数据失败: {str(e)}")
            raise
```

## 线程安全

核心模块设计时充分考虑了多线程环境下的安全性：

1. **线程安全的数据库会话**: 采用线程隔离的数据库会话
2. **互斥锁保护**: 对关键操作使用互斥锁保护
3. **线程池隔离**: 使用线程池管理后台任务
4. **原子操作**: 重要更新操作设计为原子操作
5. **无状态设计**: 大部分服务设计为无状态或线程安全

```python
class ThreadSafeService:
    """线程安全的服务基类"""
    
    def __init__(self):
        """初始化服务"""
        self._lock = threading.RLock()
        
    def _execute_with_lock(self, func, *args, **kwargs):
        """在锁保护下执行操作"""
        with self._lock:
            return func(*args, **kwargs)
    
    def _execute_in_session(self, session_func, *args, **kwargs):
        """在数据库会话中执行操作"""
        with self.database.get_session() as session:
            return session_func(session, *args, **kwargs)
```

## 主要接口

以下是核心模块的主要接口，供其他模块调用：

### 1. 应用上下文接口

```python
# 获取应用上下文
context = AppContext.instance()

# 初始化应用
success = context.initialize(config_path="config.json")

# 获取配置项
db_path = context.config.get("database.path")

# 获取数据库会话
with context.database.get_session() as session:
    # 数据库操作
    pass
```

### 2. 认证接口

```python
# 用户认证
success, result = context.auth_manager.authenticate("username", "password")

# 验证令牌
valid, user_info = context.auth_manager.validate_token("user-token")

# 检查权限
has_perm = context.auth_manager.permission_manager.check_permission(
    user_info["role"], "live.create"
)
```

### 3. 企业微信接口

```python
# 获取企业微信令牌
token = context.wecom_manager.get_access_token()

# 获取部门用户
users = context.wecom_manager.user_manager.get_department_users(1, True)

# 获取直播详情
live_info = context.wecom_manager.live_manager.get_live_info("livingid")
```

### 4. 直播管理接口

```python
# 同步直播数据
live_count = context.live_manager.sync_lives()

# 获取直播列表
lives = context.live_manager.get_lives(start_time, end_time)

# 处理直播签到
sign_record = context.live_manager.sign_manager.record_sign(
    live_id, user_id, sign_time, client_ip
)
```

### 5. 用户管理接口

```python
# 同步用户数据
user_count = context.user_manager.sync_users()

# 获取用户信息
user = context.user_manager.get_user("userid")

# 获取部门用户
users = context.user_manager.get_users_by_department(1, True)
```

### 6. 任务管理接口

```python
# 提交后台任务
task_id = context.task_manager.submit_task(
    context.live_manager.sync_lives, start_time, end_time
)

# 获取任务状态
status = context.task_manager.get_task_status(task_id)
```

### 7. 导入导出接口

```python
# 导出直播数据
file_path = context.export_manager.export_live_data(live_id, "excel")

# 导入用户数据
result = context.import_manager.import_users(file_path)
```

## 注意事项
1. 所有核心组件都设计为单例模式，通过应用上下文访问
2. 数据库操作应使用上下文管理器确保会话正确关闭
3. 长时间运行的操作应该在后台任务中执行
4. 同步企业微信数据时注意API调用频率限制
5. 确保在UI线程中不执行耗时操作
6. 所有异常应适当捕获并记录日志
7. 注意处理企业微信API调用可能的错误
8. 敏感操作应记录审计日志 