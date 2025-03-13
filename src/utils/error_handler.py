from typing import Optional, Callable, Any, Dict, List, Type
from functools import wraps
import traceback
import logging
import sys
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QWidget, QApplication, QDesktopServices
from PySide6.QtCore import QUrl, QObject, Signal
from src.utils.logger import get_logger
from src.utils.network import NetworkUtils
from src.core.database import DatabaseManager
from src.core.ip_record_manager import IPRecordManager

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
            QMessageBox.critical(None, "严重错误", f"{context}\n{error_info['message']}")
            
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
            QMessageBox.critical(None, "错误", f"{context}\n{str(error)}")
            
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
    def handle_error(error: Exception, parent: Optional[QWidget] = None, title: str = "错误") -> None:
        """处理错误
        
        Args:
            error: 异常对象
            parent: 父窗口
            title: 对话框标题
        """
        try:
            # 记录错误日志
            logger.error(f"发生错误: {str(error)}", exc_info=True)
            
            # 显示错误对话框
            QMessageBox.critical(
                parent,
                title,
                f"发生错误:\n{str(error)}"
            )
            
        except Exception as e:
            logger.error(f"处理错误时发生异常: {str(e)}", exc_info=True)
            
    @staticmethod
    def handle_warning(message: str, parent: Optional[QWidget] = None, title: str = "警告") -> None:
        """处理警告
        
        Args:
            message: 警告消息
            parent: 父窗口
            title: 对话框标题
        """
        try:
            # 记录警告日志
            logger.warning(message)
            
            # 显示警告对话框
            QMessageBox.warning(
                parent,
                title,
                message
            )
            
        except Exception as e:
            logger.error(f"处理警告时发生异常: {str(e)}", exc_info=True)
            
    @staticmethod
    def handle_info(message: str, parent: Optional[QWidget] = None, title: str = "提示") -> None:
        """处理信息
        
        Args:
            message: 信息消息
            parent: 父窗口
            title: 对话框标题
        """
        try:
            # 记录信息日志
            logger.info(message)
            
            # 显示信息对话框
            QMessageBox.information(
                parent,
                title,
                message
            )
            
        except Exception as e:
            logger.error(f"处理信息时发生异常: {str(e)}", exc_info=True)
            
    @staticmethod
    def handle_question(message: str, parent: Optional[QWidget] = None, title: str = "确认") -> bool:
        """处理确认对话框
        
        Args:
            message: 确认消息
            parent: 父窗口
            title: 对话框标题
            
        Returns:
            bool: 是否确认
        """
        try:
            # 记录确认日志
            logger.info(f"用户确认: {message}")
            
            # 显示确认对话框
            reply = QMessageBox.question(
                parent,
                title,
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            return reply == QMessageBox.StandardButton.Yes
            
        except Exception as e:
            logger.error(f"处理确认对话框时发生异常: {str(e)}", exc_info=True)
            return False
            
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
    def handle_ip_restriction_error(error: Exception, parent=None, db_manager: Optional[DatabaseManager] = None):
        """处理IP限制错误
        
        Args:
            error: 异常对象
            parent: 父窗口
            db_manager: 数据库管理器
        """
        error_msg = str(error)
        ip = NetworkUtils.extract_ip_from_error(error_msg)
        
        if ip and db_manager:
            # 记录IP
            ip_record_manager = IPRecordManager(db_manager.session)
            ip_record_manager.add_ip(ip, 'error')
        
        if ip:
            message = (
                f"检测到IP限制错误，您的IP地址为：{ip}\n\n"
                "请在企业微信后台配置可信任IP：\n"
                "1. 访问 https://work.weixin.qq.com/wework_admin/frame#apps/modApiApp\n"
                "2. 选择对应的应用\n"
                "3. 在"开发者接口"部分找到"IP白名单"\n"
                "4. 添加上述IP地址\n\n"
                "配置完成后，请等待5分钟后再试。\n\n"
                "注意：\n"
                "- 如果您的IP是动态的，建议使用IP段配置\n"
                "- 最多可配置120个IP地址\n"
                "- 配置后需要等待5-10分钟生效\n"
                "- 如果仍然无法访问，请检查IP是否正确"
            )
        else:
            message = (
                "检测到IP限制错误，但无法获取IP地址。\n\n"
                "请在企业微信后台检查IP白名单配置：\n"
                "https://work.weixin.qq.com/wework_admin/frame#apps/modApiApp\n\n"
                "配置步骤：\n"
                "1. 访问上述链接\n"
                "2. 选择对应的应用\n"
                "3. 在"开发者接口"部分找到"IP白名单"\n"
                "4. 添加您的服务器IP地址\n\n"
                "注意：\n"
                "- 最多可配置120个IP地址\n"
                "- 配置后需要等待5-10分钟生效"
            )
        
        # 创建自定义对话框
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("IP限制提示")
        dialog.setText(message)
        
        # 添加按钮
        copy_btn = dialog.addButton("复制IP", QMessageBox.ButtonRole.ActionRole)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(ip if ip else ""))
        
        open_btn = dialog.addButton("打开配置页面", QMessageBox.ButtonRole.ActionRole)
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://work.weixin.qq.com/wework_admin/frame#apps/modApiApp")))
        
        dialog.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        
        # 显示对话框
        dialog.exec() 