from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from src.utils.logger_utils import get_logger

logger = get_logger(__name__)

class StyleManager:
    """样式表管理器"""
    
    @staticmethod
    def get_main_style() -> str:
        """获取主窗口样式
        
        Returns:
            str: 样式表
        """
        return """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
                background-color: #1890ff;
                color: white;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
                color: #999999;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #1890ff;
            }
            QTableWidget {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
            QHeaderView::section {
                background-color: #fafafa;
                padding: 8px;
                border: 1px solid #d9d9d9;
                font-weight: bold;
            }
        """
    
    @staticmethod
    def get_live_booking_style() -> str:
        """获取直播预约页面样式
        
        Returns:
            str: 样式表
        """
        return """
            QWidget#liveBookingPage {
                background-color: #ffffff;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 20px;
            }
            QLabel#subtitleLabel {
                font-size: 16px;
                color: #666666;
                margin-bottom: 20px;
            }
            QPushButton#submitButton {
                padding: 12px 24px;
                font-size: 16px;
                background-color: #52c41a;
            }
            QPushButton#submitButton:hover {
                background-color: #73d13d;
            }
            QPushButton#submitButton:pressed {
                background-color: #389e0d;
            }
        """
    
    @staticmethod
    def get_live_list_style() -> str:
        """获取直播列表页面样式
        
        Returns:
            str: 样式表
        """
        return """
            QWidget#liveListPage {
                background-color: #ffffff;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 20px;
            }
            QPushButton#refreshButton {
                padding: 8px 16px;
                font-size: 14px;
                background-color: #1890ff;
            }
            QPushButton#refreshButton:hover {
                background-color: #40a9ff;
            }
            QPushButton#refreshButton:pressed {
                background-color: #096dd9;
            }
            QTableWidget#liveTable {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
            }
            QTableWidget#liveTable::item {
                padding: 12px;
            }
            QTableWidget#liveTable::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
        """
    
    @staticmethod
    def get_user_management_style() -> str:
        """获取用户管理页面样式
        
        Returns:
            str: 样式表
        """
        return """
            QWidget#userManagementPage {
                background-color: #ffffff;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 20px;
            }
            QPushButton#addButton {
                padding: 8px 16px;
                font-size: 14px;
                background-color: #52c41a;
            }
            QPushButton#addButton:hover {
                background-color: #73d13d;
            }
            QPushButton#addButton:pressed {
                background-color: #389e0d;
            }
            QTableWidget#userTable {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
            }
            QTableWidget#userTable::item {
                padding: 12px;
            }
            QTableWidget#userTable::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
        """
    
    @staticmethod
    def get_dark_style() -> str:
        """获取暗色主题样式
        
        Returns:
            str: 样式表
        """
        return """
            QMainWindow {
                background-color: #141414;
            }
            QWidget {
                color: #ffffff;
            }
            QPushButton {
                background-color: #1890ff;
                color: white;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #262626;
                color: #595959;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #262626;
                border: 1px solid #434343;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
            QComboBox {
                background-color: #262626;
                border: 1px solid #434343;
                color: #ffffff;
            }
            QComboBox:focus {
                border-color: #1890ff;
            }
            QTableWidget {
                background-color: #262626;
                border: 1px solid #434343;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #111b26;
                color: #1890ff;
            }
            QHeaderView::section {
                background-color: #1f1f1f;
                padding: 8px;
                border: 1px solid #434343;
                font-weight: bold;
            }
        """
    
    @staticmethod
    def get_light_style() -> str:
        """获取亮色主题样式
        
        Returns:
            str: 样式表
        """
        return """
            QMainWindow {
                background-color: #ffffff;
            }
            QWidget {
                color: #333333;
            }
            QPushButton {
                background-color: #1890ff;
                color: white;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                color: #333333;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                color: #333333;
            }
            QComboBox:focus {
                border-color: #1890ff;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                color: #333333;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
            QHeaderView::section {
                background-color: #fafafa;
                padding: 8px;
                border: 1px solid #d9d9d9;
                font-weight: bold;
            }
        """
    
    @staticmethod
    def get_login_style() -> str:
        """获取登录窗口样式
        
        Returns:
            str: 样式表
        """
        return """
            QMainWindow {
                background-color: #ffffff;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #1890ff;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
                background-color: #1890ff;
                color: white;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
                color: #999999;
            }
        """
    
    @staticmethod
    def apply_style(widget: QWidget):
        """应用样式到组件
        
        Args:
            widget: 要应用样式的组件
        """
        try:
            widget.setStyleSheet(StyleManager.get_main_style())
        except Exception as e:
            logger.error(f"应用样式失败: {str(e)}") 