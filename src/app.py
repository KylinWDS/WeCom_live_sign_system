"""
应用全局上下文模块
提供对应用全局资源的访问
"""
from typing import Optional, Any

class AppContext:
    """应用上下文类
    
    提供对全局资源的访问，包括：
    - 数据库管理器
    - 配置管理器
    - 认证管理器
    等全局资源
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppContext, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.db_manager = None
            self.config_manager = None
            self.auth_manager = None
            self._initialized = True
    
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
        self.db_manager = db_manager
    
    def set_config_manager(self, config_manager):
        """设置配置管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
    
    def set_auth_manager(self, auth_manager):
        """设置认证管理器
        
        Args:
            auth_manager: 认证管理器实例
        """
        self.auth_manager = auth_manager

# 全局应用上下文实例
_app_context = None

def get_app_context() -> Optional[AppContext]:
    """获取全局应用上下文
    
    Returns:
        Optional[AppContext]: 应用上下文实例，如果尚未初始化则返回None
    """
    global _app_context
    if _app_context is None:
        _app_context = AppContext()
    return _app_context

def init_app_context(db_manager=None, config_manager=None, auth_manager=None) -> AppContext:
    """初始化应用上下文
    
    Args:
        db_manager: 数据库管理器实例
        config_manager: 配置管理器实例
        auth_manager: 认证管理器实例
        
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
    
    return app_context 