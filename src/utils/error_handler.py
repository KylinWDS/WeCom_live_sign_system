from typing import Optional, Callable, Any, Dict, List, Type
from functools import wraps
import traceback
import logging
import sys
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QWidget, QApplication
from PySide6.QtCore import QUrl, QObject, Signal
from PySide6.QtGui import QDesktopServices
from .logger import get_logger
from .network import NetworkUtils
from ..core.database import DatabaseManager
from ..core.ip_record_manager import IPRecordManager

logger = get_logger(__name__)

class ErrorHandler(QObject):
    """错误处理管理器"""
    
    # 信号定义
    error_occurred = Signal(str, str)  # 错误发生信号(错误类型, 错误信息)
    warning_occurred = Signal(str, str)  # 警告发生信号(警告类型, 警告信息)
    critical_error = Signal(str, str)  # 严重错误信号(错误类型, 错误信息)
    
    def __init__(self):
        super().__init__()
        self._error_handlers: Dict[Type[Exception], Callable] = {}  # 错误处理器映射
        self._error_history: List[Dict[str, Any]] = []  # 错误历史记录
        self._max_history = 100  # 最大历史记录数
        
    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        """注册错误处理器
        
        Args:
            exception_type: 异常类型
            handler: 处理函数
        """
        self._error_handlers[exception_type] = handler
        
    def handle_error(self, error: Exception, context: str = ""):
        """处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        try:
            # 记录错误信息
            error_info = {
                "type": type(error).__name__,
                "message": str(error),
                "context": context,
                "timestamp": datetime.now(),
                "traceback": traceback.format_exc()
            }
            
            # 添加到历史记录
            self._error_history.append(error_info)
            if len(self._error_history) > self._max_history:
                self._error_history.pop(0)
                
            # 记录日志
            logger.error(f"错误发生 - 类型: {error_info['type']}, 上下文: {context}, 信息: {error_info['message']}")
            
            # 发送信号
            self.error_occurred.emit(error_info["type"], error_info["message"])
            
            # 调用对应的处理器
            handler = self._error_handlers.get(type(error))
            if handler:
                handler(error, context)
            else:
                self._handle_unknown_error(error, context)
                
        except Exception as e:
            logger.critical(f"错误处理过程中发生异常: {str(e)}")
            self.critical_error.emit("ErrorHandler", str(e))
            
    def handle_warning(self, warning: str, context: str = ""):
        """处理警告
        
        Args:
            warning: 警告信息
            context: 警告上下文
        """
        try:
            # 记录警告信息
            warning_info = {
                "type": "Warning",
                "message": warning,
                "context": context,
                "timestamp": datetime.now()
            }
            
            # 记录日志
            logger.warning(f"警告发生 - 上下文: {context}, 信息: {warning}")
            
            # 发送信号
            self.warning_occurred.emit("Warning", warning)
            
            # 显示警告对话框
            QMessageBox.warning(None, "警告", f"{context}\n{warning}")
            
        except Exception as e:
            logger.error(f"警告处理过程中发生异常: {str(e)}")
            
    def handle_critical_error(self, error: Exception, context: str = ""):
        """处理严重错误
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        try:
            # 记录错误信息
            error_info = {
                "type": type(error).__name__,
                "message": str(error),
                "context": context,
                "timestamp": datetime.now(),
                "traceback": traceback.format_exc()
            }
            
            # 记录日志
            logger.critical(f"严重错误发生 - 类型: {error_info['type']}, 上下文: {context}, 信息: {error_info['message']}")
            
            # 发送信号
            self.critical_error.emit(error_info["type"], error_info["message"])
            
            # 显示错误对话框
            QMessageBox.critical(
                None,  # 父窗口参数为 None
                "严重错误",
                f"{context}\n{error_info['message']}"
            )
            
        except Exception as e:
            logger.critical(f"严重错误处理过程中发生异常: {str(e)}")
            
    def _handle_unknown_error(self, error: Exception, context: str):
        """处理未知错误
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        try:
            # 显示错误对话框
            QMessageBox.critical(
                None,  # 父窗口参数为 None
                "错误",
                f"{context}\n{str(error)}"
            )
            
        except Exception as e:
            logger.error(f"未知错误处理过程中发生异常: {str(e)}")
            
    def get_error_history(self) -> List[Dict[str, Any]]:
        """获取错误历史记录
        
        Returns:
            错误历史记录列表
        """
        return self._error_history.copy()
        
    def clear_error_history(self):
        """清除错误历史记录"""
        self._error_history.clear()
        
    def error_handler(self, context: str = ""):
        """错误处理装饰器
        
        Args:
            context: 错误上下文
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.handle_error(e, context)
                    raise
            return wrapper
        return decorator
        
    def warning_handler(self, context: str = ""):
        """警告处理装饰器
        
        Args:
            context: 警告上下文
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.handle_warning(str(e), context)
                    return None
            return wrapper
        return decorator
        
    def critical_error_handler(self, context: str = ""):
        """严重错误处理装饰器
        
        Args:
            context: 错误上下文
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.handle_critical_error(e, context)
                    raise
            return wrapper
        return decorator

    @staticmethod
    def handle_error(error, parent=None, title="错误"):
        """处理错误
        
        Args:
            error: 错误对象
            parent: 父窗口
            title: 错误标题
        """
        error_message = str(error)
        traceback_str = traceback.format_exc()
        
        # 记录错误
        logger.error(f"{title}: {error_message}\n{traceback_str}")
        
        # 显示错误对话框
        if parent:
            QMessageBox.critical(parent, title, error_message)
        return False
    
    @staticmethod
    def handle_warning(message, parent=None, title="警告"):
        """处理警告
        
        Args:
            message: 警告消息
            parent: 父窗口
            title: 警告标题
        """
        # 记录警告
        logger.warning(f"{title}: {message}")
        
        # 显示警告对话框
        if parent:
            QMessageBox.warning(parent, title, message)
        return False
    
    @staticmethod
    def handle_info(message, parent=None, title="信息"):
        """处理信息
        
        Args:
            message: 信息消息
            parent: 父窗口
            title: 信息标题
        """
        # 记录信息
        logger.info(f"{title}: {message}")
        
        # 显示信息对话框
        if parent:
            QMessageBox.information(parent, title, message)
        return True
    
    @staticmethod
    def handle_question(message, parent=None, title="确认"):
        """处理确认问题
        
        Args:
            message: 问题消息
            parent: 父窗口
            title: 问题标题
            
        Returns:
            bool: 是否确认
        """
        # 显示问题对话框
        if parent:
            reply = QMessageBox.question(
                parent,
                title,
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return reply == QMessageBox.Yes
        return False
    
    @staticmethod
    def install_global_exception_handler():
        """安装全局异常处理器"""
        def exception_hook(exctype, value, tb):
            """全局异常钩子"""
            error_msg = ''.join(traceback.format_exception(exctype, value, tb))
            logger.critical(f"未捕获的异常: {error_msg}")
            
            # 使用QMessageBox显示未捕获的异常
            try:
                error_dialog = QMessageBox()
                error_dialog.setIcon(QMessageBox.Critical)
                error_dialog.setWindowTitle("系统错误")
                error_dialog.setText("程序遇到了一个未处理的错误:")
                error_dialog.setInformativeText(str(value))
                error_dialog.setDetailedText(error_msg)
                error_dialog.setStandardButtons(QMessageBox.Ok)
                error_dialog.exec()
            except:
                # 如果GUI显示失败，打印到控制台
                print(f"严重错误: {error_msg}", file=sys.stderr)
                
            # 调用原始的异常处理器
            sys.__excepthook__(exctype, value, tb)
        
        # 设置全局异常钩子
        sys.excepthook = exception_hook
        logger.info("已安装全局异常处理器")
        
    @staticmethod
    def try_operation(operation_func, error_msg="操作失败", parent=None, success_msg=None):
        """尝试执行操作，自动处理异常
        
        Args:
            operation_func: 要执行的操作函数
            error_msg: 错误提示消息
            parent: 父窗口
            success_msg: 成功提示消息
            
        Returns:
            result: 操作结果
        """
        try:
            result = operation_func()
            if success_msg:
                ErrorHandler.handle_info(success_msg, parent, "成功")
            return result
        except Exception as e:
            ErrorHandler.handle_error(e, parent, error_msg)
            return None

    @staticmethod
    def handle_critical(message: str, parent: Optional[QWidget] = None, title: str = "严重错误") -> None:
        """处理严重错误
        
        Args:
            message: 错误消息
            parent: 父窗口
            title: 对话框标题
        """
        try:
            # 记录严重错误日志
            logger.critical(message)
            
            # 显示严重错误对话框
            QMessageBox.critical(
                parent,
                title,
                f"发生严重错误:\n{message}\n\n程序可能无法继续运行。"
            )
            
        except Exception as e:
            logger.error(f"处理严重错误时发生异常: {str(e)}", exc_info=True)
            
    @staticmethod
    def handle_validation_error(message: str, parent: Optional[QWidget] = None) -> None:
        """处理验证错误
        
        Args:
            message: 验证错误消息
            parent: 父窗口
        """
        try:
            # 记录验证错误日志
            logger.warning(f"验证错误: {message}")
            
            # 显示验证错误对话框
            QMessageBox.warning(
                parent,
                "验证错误",
                message
            )
            
        except Exception as e:
            logger.error(f"处理验证错误时发生异常: {str(e)}", exc_info=True)
            
    @staticmethod
    def handle_permission_error(message: str, parent: Optional[QWidget] = None) -> None:
        """处理权限错误
        
        Args:
            message: 权限错误消息
            parent: 父窗口
        """
        try:
            # 记录权限错误日志
            logger.warning(f"权限错误: {message}")
            
            # 显示权限错误对话框
            QMessageBox.warning(
                parent,
                "权限错误",
                f"您没有权限执行此操作:\n{message}"
            )
            
        except Exception as e:
            logger.error(f"处理权限错误时发生异常: {str(e)}", exc_info=True)
            
    @staticmethod
    def handle_network_error(error: Exception, parent: Optional[QWidget] = None) -> None:
        """处理网络错误
        
        Args:
            error: 网络错误异常
            parent: 父窗口
        """
        try:
            # 记录网络错误日志
            logger.error(f"网络错误: {str(error)}", exc_info=True)
            
            # 显示网络错误对话框
            QMessageBox.critical(
                parent,
                "网络错误",
                f"发生网络错误:\n{str(error)}\n\n请检查网络连接后重试。"
            )
            
        except Exception as e:
            logger.error(f"处理网络错误时发生异常: {str(e)}", exc_info=True)
            
    @staticmethod
    def handle_database_error(error: Exception, parent: Optional[QWidget] = None) -> None:
        """处理数据库错误
        
        Args:
            error: 数据库错误异常
            parent: 父窗口
        """
        try:
            # 记录数据库错误日志
            logger.error(f"数据库错误: {str(error)}", exc_info=True)
            
            # 显示数据库错误对话框
            QMessageBox.critical(
                parent,
                "数据库错误",
                f"发生数据库错误:\n{str(error)}\n\n请检查数据库连接后重试。"
            )
            
        except Exception as e:
            logger.error(f"处理数据库错误时发生异常: {str(e)}", exc_info=True)

    @staticmethod
    def is_ip_whitelist_error(error_msg: str) -> bool:
        """判断是否为IP白名单错误
        
        Args:
            error_msg: 错误消息
            
        Returns:
            bool: 是否为IP白名单错误
        """
        return "not allow to access from your ip" in error_msg or "60020" in error_msg
    
    @staticmethod
    def handle_ip_restriction_error(error: Exception, parent=None, db_manager: Optional[DatabaseManager] = None):
        """处理IP限制错误
        
        Args:
            error: 异常对象
            parent: 父窗口
            db_manager: 数据库管理器
            
        Returns:
            bool: 用户是否选择继续使用
        """
        error_msg = str(error)
        
        # 优化的IP白名单错误判断条件
        if not ErrorHandler.is_ip_whitelist_error(error_msg):
            # 如果不是IP白名单错误，直接显示一般错误提示
            QMessageBox.warning(
                parent, 
                "API连接失败", 
                f"企业微信API连接失败，部分功能可能无法使用。\n\n错误详情: {error_msg}"
            )
            return True
            
        ip = NetworkUtils.extract_ip_from_error(error_msg)
        
        if ip and db_manager:
            try:
                # 使用get_session创建新会话而不是直接使用session属性
                with db_manager.get_session() as session:
                    ip_record_manager = IPRecordManager(session)
                    ip_record_manager.add_ip(ip, 'error')
                    logger.info(f"IP白名单错误，已将IP [{ip}] 记录到数据库(类型: error)")
            except Exception as e:
                logger.error(f"记录IP到数据库失败: {str(e)}")
        
        if ip:
            message = f"""检测到IP限制错误，您的IP地址为：{ip}

请在企业微信后台配置可信任IP：
1. 访问 https://work.weixin.qq.com/wework_admin/frame#apps/modApiApp
2. 选择对应的应用
3. 在"开发者接口"部分找到"IP白名单"
4. 添加上述IP地址

配置完成后，请等待5分钟后再试。

注意：
- 如果您的IP是动态的，建议使用IP段配置
- 最多可配置120个IP地址
- 配置后需要等待5-10分钟生效
- 如果仍然无法访问，请检查IP是否正确"""
        else:
            message = """检测到IP限制错误，但无法获取IP地址。

请在企业微信后台检查IP白名单配置：
https://work.weixin.qq.com/wework_admin/frame#apps/modApiApp

配置步骤：
1. 访问上述链接
2. 选择对应的应用
3. 在"开发者接口"部分找到"IP白名单"
4. 添加您的服务器IP地址

注意：
- 最多可配置120个IP地址
- 配置后需要等待5-10分钟生效"""
        
        # 创建自定义对话框
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("IP限制提示")
        dialog.setText(message)
        
        # 添加按钮
        copy_btn = dialog.addButton("复制IP", QMessageBox.ButtonRole.ActionRole)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(ip if ip else ""))
        
        open_btn = dialog.addButton("配置说明", QMessageBox.ButtonRole.ActionRole)
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://work.weixin.qq.com/wework_admin/frame#apps/modApiApp")))
        
        # 修改按钮名称
        dialog.addButton("继续使用", QMessageBox.ButtonRole.AcceptRole)
        dialog.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        
        # 显示对话框并返回结果
        result = dialog.exec()
        
        # 返回用户是否选择继续使用
        return result == QMessageBox.ButtonRole.AcceptRole
        
    # 添加一个实例方法，调用静态方法
    def handle_wecom_api_error(self, error: Exception, parent=None, db_manager: Optional[DatabaseManager] = None):
        """处理企业微信API错误
        
        Args:
            error: 异常对象
            parent: 父窗口
            db_manager: 数据库管理器
            
        Returns:
            bool: 用户是否选择继续使用
        """
        error_msg = str(error)
        
        # 记录错误信息
        logger.error(f"企业微信API错误: {error_msg}")
        
        # 发送信号
        self.error_occurred.emit("WeComAPIError", error_msg)
        
        # 检查是否为IP白名单错误
        if self.is_ip_whitelist_error(error_msg):
            # 如果是IP白名单错误，调用专门的处理方法
            return self.handle_ip_restriction_error(error, parent, db_manager)
        else:
            # 其他企业微信API错误
            QMessageBox.warning(
                parent, 
                "API连接失败", 
                f"企业微信API连接失败，部分功能可能无法使用。\n\n错误详情: {error_msg}"
            )
            return True 