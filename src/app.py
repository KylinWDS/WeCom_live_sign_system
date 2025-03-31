"""
应用全局上下文模块
提供对应用全局资源的访问
"""
from typing import Optional, Any, Union, Type, TypeVar
import logging
import threading
from functools import wraps

# 定义日志记录器
logger = logging.getLogger(__name__)

# 定义泛型类型变量，用于类型标注
T = TypeVar('T')

class AppContextError(Exception):
    """应用上下文相关错误的基类"""
    pass

class ResourceNotInitializedError(AppContextError):
    """资源未初始化错误"""
    pass

def ensure_initialized(attribute_name: str):
    """装饰器：确保指定的属性已初始化
    
    Args:
        attribute_name: 要检查的属性名
        
    Raises:
        ResourceNotInitializedError: 当属性未初始化时抛出
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if getattr(self, attribute_name) is None:
                raise ResourceNotInitializedError(f"资源 '{attribute_name}' 尚未初始化")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

class AppContext:
    """应用上下文类
    
    提供对全局资源的访问，包括：
    - 数据库管理器：管理数据库连接和会话
    - 配置管理器：管理应用配置
    - 认证管理器：管理用户认证和权限
    
    该类实现了单例模式，确保整个应用中只存在一个上下文实例。
    资源使用懒加载模式，仅在第一次访问时初始化。
    """
    
    _instance = None
    _lock = threading.RLock()  # 使用可重入锁确保线程安全
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AppContext, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._db_manager = None
            self._config_manager = None
            self._auth_manager = None
            self._initialized = True
            self._is_debug = False
            logger.info("应用上下文已创建")
    
    @classmethod
    def get_instance(cls) -> 'AppContext':
        """获取应用上下文实例
        
        Returns:
            AppContext: 应用上下文实例
        """
        return cls()
    
    def set_db_manager(self, db_manager):
        """设置数据库管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self._db_manager = db_manager
        logger.debug("数据库管理器已设置")
    
    def set_config_manager(self, config_manager):
        """设置配置管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager
        logger.debug("配置管理器已设置")
    
    def set_auth_manager(self, auth_manager):
        """设置认证管理器
        
        Args:
            auth_manager: 认证管理器实例
        """
        self._auth_manager = auth_manager
        logger.debug("认证管理器已设置")
    
    def set_debug(self, value: bool):
        """设置调试模式
        
        Args:
            value: 是否启用调试模式
        """
        self._is_debug = value
        logger.debug(f"调试模式已{'启用' if value else '禁用'}")
    
    @property
    @ensure_initialized("_db_manager")
    def db_manager(self):
        """获取数据库管理器
        
        Returns:
            数据库管理器实例
            
        Raises:
            ResourceNotInitializedError: 如果数据库管理器尚未初始化
        """
        return self._db_manager
    
    @property
    @ensure_initialized("_config_manager")
    def config_manager(self):
        """获取配置管理器
        
        Returns:
            配置管理器实例
            
        Raises:
            ResourceNotInitializedError: 如果配置管理器尚未初始化
        """
        return self._config_manager
    
    @property
    @ensure_initialized("_auth_manager")
    def auth_manager(self):
        """获取认证管理器
        
        Returns:
            认证管理器实例
            
        Raises:
            ResourceNotInitializedError: 如果认证管理器尚未初始化
        """
        return self._auth_manager
    
    @property
    def is_debug(self) -> bool:
        """获取调试模式状态
        
        Returns:
            bool: 是否处于调试模式
        """
        return self._is_debug
    
    def is_initialized(self, resource_name: str) -> bool:
        """检查指定资源是否已初始化
        
        Args:
            resource_name: 资源名称，可选值为 'db_manager', 'config_manager', 'auth_manager'
            
        Returns:
            bool: 资源是否已初始化
            
        Raises:
            ValueError: 当指定的资源名称无效时抛出
        """
        if resource_name == 'db_manager':
            return self._db_manager is not None
        elif resource_name == 'config_manager':
            return self._config_manager is not None
        elif resource_name == 'auth_manager':
            return self._auth_manager is not None
        else:
            raise ValueError(f"无效的资源名称: {resource_name}")
    
    def get_resource_status(self) -> dict:
        """获取所有资源的初始化状态
        
        Returns:
            dict: 包含资源初始化状态的字典
        """
        return {
            'db_manager': self._db_manager is not None,
            'config_manager': self._config_manager is not None,
            'auth_manager': self._auth_manager is not None,
            'debug_mode': self._is_debug
        }
    
    def __str__(self) -> str:
        status = self.get_resource_status()
        return f"AppContext(db_manager={status['db_manager']}, config_manager={status['config_manager']}, auth_manager={status['auth_manager']}, debug_mode={status['debug_mode']})"

# 全局应用上下文实例
_app_context = None
_context_lock = threading.RLock()

def get_app_context() -> AppContext:
    """获取全局应用上下文
    
    如果应用上下文尚未初始化，则会自动创建一个新的实例。
    
    Returns:
        AppContext: 应用上下文实例
    """
    global _app_context
    with _context_lock:
        if _app_context is None:
            _app_context = AppContext()
            logger.debug("创建了新的应用上下文实例")
    return _app_context

def init_app_context(db_manager=None, config_manager=None, auth_manager=None, debug=False) -> AppContext:
    """初始化应用上下文
    
    设置应用上下文中的各种管理器。
    
    Args:
        db_manager: 数据库管理器实例
        config_manager: 配置管理器实例
        auth_manager: 认证管理器实例
        debug: 是否启用调试模式
        
    Returns:
        AppContext: 初始化后的应用上下文实例
    """
    app_context = get_app_context()
    
    if db_manager:
        app_context.set_db_manager(db_manager)
    
    if config_manager:
        app_context.set_config_manager(config_manager)
    
    if auth_manager:
        app_context.set_auth_manager(auth_manager)
    
    app_context.set_debug(debug)
    
    logger.info("应用上下文初始化完成")
    return app_context

def get_db_manager():
    """获取数据库管理器的便捷方法
    
    Returns:
        数据库管理器实例
        
    Raises:
        ResourceNotInitializedError: 如果数据库管理器尚未初始化
    """
    return get_app_context().db_manager

def get_config_manager():
    """获取配置管理器的便捷方法
    
    Returns:
        配置管理器实例
        
    Raises:
        ResourceNotInitializedError: 如果配置管理器尚未初始化
    """
    return get_app_context().config_manager

def get_auth_manager():
    """获取认证管理器的便捷方法
    
    Returns:
        认证管理器实例
        
    Raises:
        ResourceNotInitializedError: 如果认证管理器尚未初始化
    """
    return get_app_context().auth_manager

def is_debug_mode() -> bool:
    """检查应用是否处于调试模式
    
    Returns:
        bool: 是否处于调试模式
    """
    return get_app_context().is_debug 