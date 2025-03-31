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
            /* 全局样式 */
            QWidget {
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                font-size: 14px;
            }
            
            /* 左侧菜单样式 */
            #leftMenu {
                background-color: #2c3e50;
                min-width: 160px;
                max-width: 160px;
            }
            
            #menuButton {
                background-color: transparent;
                color: #ecf0f1;
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 15px;
            }
            
            #menuButton:hover {
                background-color: #34495e;
            }
            
            #menuButton:pressed {
                background-color: #1abc9c;
            }
            
            #dangerButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 15px;
                text-align: center;
                font-size: 15px;
                border-radius: 4px;
                margin: 10px;
            }
            
            #dangerButton:hover {
                background-color: #c0392b;
            }
            
            /* 仪表盘样式 */
            #welcomeFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
            
            #welcomeLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            #timeLabel {
                font-size: 14px;
                color: #7f8c8d;
            }
            
            #statusFrame {
                margin-bottom: 15px;
            }
            
            #infoCard {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
                border: 1px solid #e0e0e0;
            }
            
            #infoCard:hover {
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            
            #cardTitle {
                font-size: 16px;
                color: #7f8c8d;
                margin-bottom: 5px;
            }
            
            #linksFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
            
            #dashboardButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                font-size: 15px;
            }
            
            #dashboardButton:hover {
                background-color: #2980b9;
            }
            
            #recentFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid #e0e0e0;
            }
            
            #sectionTitle {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            
            #versionLabel {
                font-size: 12px;
                color: #95a5a6;
            }
            
            /* 标签页样式 */
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #e0e0e0;
            }
            
            /* 主要按钮样式 */
            #primaryButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
            }
            
            #primaryButton:hover {
                background-color: #2980b9;
            }
            
            /* 次要按钮样式 */
            #secondaryButton {
                background-color: #f8f9fa;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 8px 15px;
            }
            
            #secondaryButton:hover {
                background-color: #e9ecef;
            }
            
            /* 链接按钮样式 */
            #linkButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px 12px;
                text-decoration: none;
                min-width: 60px;
                color: #000000;
            }
            
            #linkButton:hover {
                background-color: #e0e0e0;
                color: #000000;
            }
            
            #linkButton:disabled {
                color: #999999;
            }
            
            /* 确保linkButton文字在所有状态下都可见 */
            QPushButton#linkButton {
                color: #3498db !important;
                min-width: 60px;
                margin: 0 2px;
            }
            
            QPushButton#linkButton:hover {
                color: #2980b9 !important;
            }
            
            QPushButton#linkButton:disabled {
                color: #95a5a6 !important;
            }
            
            /* 状态栏样式 */
            QStatusBar {
                background-color: #f8f9fa;
                color: #7f8c8d;
                border-top: 1px solid #e0e0e0;
                padding: 3px;
                min-height: 25px;
            }
            
            #statusCorpLabel {
                font-size: 12px;
                color: #3498db;
                padding-left: 10px;
                font-weight: bold;
            }
            
            #statusUserLabel {
                font-size: 12px;
                color: #2c3e50;
                font-weight: bold;
            }
            
            #disclaimerLabel {
                font-size: 11px;
                color: #95a5a6;
                padding-right: 10px;
                font-style: italic;
            }
            
            /* 工具栏样式 */
            QToolBar {
                background-color: #f8f9fa;
                border: none;
                spacing: 10px;
                padding: 5px;
            }
            
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            
            QToolButton:hover {
                background-color: #e0e0e0;
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
        """获取登录页面样式
        
        Returns:
            str: 样式表
        """
        return """
            /* 登录页面样式 */
            #loginPage {
                background-color: #ecf0f1;
            }
            
            #loginForm {
                background-color: white;
                border-radius: 8px;
                padding: 30px;
                min-width: 400px;
                max-width: 450px;
                border: 1px solid #e0e0e0;
            }
            
            #loginTitle {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
                text-align: center;
            }
            
            #loginInput {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 15px;
                font-size: 16px;
            }
            
            #loginButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            
            #loginButton:hover {
                background-color: #2980b9;
            }
            
            #errorLabel {
                color: #e74c3c;
                font-size: 14px;
                margin-top: 10px;
            }
            
            #versionLabel {
                color: #95a5a6;
                font-size: 12px;
                margin-top: 20px;
                text-align: center;
            }
        """
    
    @staticmethod
    def get_settings_style() -> str:
        """获取设置页面样式
        
        Returns:
            str: 样式表
        """
        return """
            /* 设置页面样式 */
            #settingsPage {
                background-color: #ffffff;
            }
            
            #settingsForm {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                border: 1px solid #e0e0e0;
            }
            
            #settingsTitle {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 15px;
            }
            
            #settingsSection {
                font-size: 16px;
                font-weight: bold;
                color: #34495e;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            
            #settingsLabel {
                font-size: 14px;
                color: #2c3e50;
            }
            
            #settingsInput {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            
            #settingsButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
            }
            
            #settingsButton:hover {
                background-color: #2980b9;
            }
            
            #saveButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                font-size: 15px;
                font-weight: bold;
            }
            
            #saveButton:hover {
                background-color: #27ae60;
            }
            
            #resetButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                font-size: 15px;
            }
            
            #resetButton:hover {
                background-color: #c0392b;
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