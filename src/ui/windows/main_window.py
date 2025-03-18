# PySide6导入
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QTabWidget, QStackedWidget,
    QLineEdit, QComboBox, QMenuBar, QMenu, QStatusBar
)
from PySide6.QtCore import Qt

# UI相关导入
from ..managers.style import StyleManager
from ..pages.home_page import HomePage
from ..pages.stats_page import StatsPage
from ..pages.settings_page import SettingsPage
from ..pages.live_booking_page import LiveBookingPage
from ..pages.live_list_page import LiveListPage
from ..pages.user_management_page import UserManagementPage

# 核心功能导入
from src.core.database import DatabaseManager
from src.models.user import UserRole
from src.api.wecom import WeComAPI
from src.core.task_manager import TaskManager
from src.core.auth_manager import AuthManager

# 工具类导入
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, user, config_manager, db_manager, auth_manager):
        super().__init__()
        self.setWindowTitle("企业微信直播签到系统")
        self.setMinimumSize(1200, 800)
        
        # 保存用户信息和管理器
        self.user = user
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        
        # 获取企业信息
        corporations = self.config_manager.get_corporations()
        if corporations:
            corp = corporations[0]  # 使用第一个企业的信息
            self.wecom_api = WeComAPI(
                corpid=corp["corpid"],
                corpsecret=corp["corpsecret"]
            )
        else:
            self.wecom_api = None
            logger.warning("未找到企业配置信息")
        
        # 初始化任务管理器
        self.task_manager = TaskManager(self.wecom_api, self.db_manager)
        
        # 设置UI
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建左侧菜单
        self.create_left_menu()
        
        # 创建右侧内容区
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_main_style())
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 退出动作
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        
        # 用户管理动作
        user_management_action = settings_menu.addAction("用户管理")
        user_management_action.triggered.connect(self.show_user_management)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        # 关于动作
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)
        
    def create_left_menu(self):
        """创建左侧菜单"""
        # 创建左侧菜单容器
        left_menu = QWidget()
        left_menu.setFixedWidth(200)
        left_menu.setObjectName("leftMenu")
        
        # 创建左侧菜单布局
        layout = QVBoxLayout(left_menu)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建菜单按钮
        self.live_booking_btn = QPushButton("预约直播")
        self.live_booking_btn.setObjectName("menuButton")
        self.live_booking_btn.clicked.connect(self.show_live_booking)
        layout.addWidget(self.live_booking_btn)
        
        self.live_list_btn = QPushButton("直播列表")
        self.live_list_btn.setObjectName("menuButton")
        self.live_list_btn.clicked.connect(self.show_live_list)
        layout.addWidget(self.live_list_btn)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 将左侧菜单添加到主布局
        self.centralWidget().layout().insertWidget(0, left_menu)
        
    def show_live_booking(self):
        """显示直播预约页面"""
        # 检查权限
        if not self.check_permission("manage_live"):
            QMessageBox.warning(self, "警告", "您没有权限访问此功能")
            return
            
        # 创建页面
        page = LiveBookingPage(
            self.wecom_api,
            self.task_manager
        )
        self.content_stack.addWidget(page)
        self.content_stack.setCurrentWidget(page)
        
    def show_live_list(self):
        """显示直播列表页面"""
        # 检查权限
        if not self.check_permission("view_live"):
            QMessageBox.warning(self, "警告", "您没有权限访问此功能")
            return
            
        # 创建页面
        page = LiveListPage(
            self.wecom_api,
            self.task_manager
        )
        self.content_stack.addWidget(page)
        self.content_stack.setCurrentWidget(page)
        
    def show_user_management(self):
        """显示用户管理页面"""
        # 检查权限
        if not self.check_permission("manage_users"):
            QMessageBox.warning(self, "警告", "您没有权限访问此功能")
            return
            
        # 创建页面
        page = UserManagementPage(self.auth_manager)
        self.content_stack.addWidget(page)
        self.content_stack.setCurrentWidget(page)
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "企业微信直播签到系统 v0.0.1\n\n"
            "用于管理企业微信直播和签到信息的系统。"
        )
        
    def check_permission(self, permission: str) -> bool:
        """检查当前用户是否有指定权限
        
        Args:
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        # TODO: 获取当前登录用户
        current_user = "root-admin"  # 临时使用root-admin
        
        return self.auth_manager.has_permission(current_user, permission)

    def _get_page_title(self, page_name: str) -> str:
        """获取页面标题"""
        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.addTab(HomePage(self.db_manager), "首页")
        tab_widget.addTab(StatsPage(self.db_manager), "统计")
        tab_widget.addTab(SettingsPage(self.db_manager), "设置")
        return tab_widget.tabText(tab_widget.currentIndex()) 