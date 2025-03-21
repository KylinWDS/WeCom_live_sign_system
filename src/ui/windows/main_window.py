# PySide6导入
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QTabWidget, QStackedWidget,
    QLineEdit, QComboBox, QMenuBar, QMenu, QStatusBar
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QIcon, QGuiApplication

# UI相关导入
from ..managers.style import StyleManager
from ..managers.theme_manager import ThemeManager
from ..utils.widget_utils import WidgetUtils
from ..managers.animation import AnimationManager
from ..pages.home_page import HomePage
from ..pages.stats_page import StatsPage
from ..pages.settings_page import SettingsPage
from ..pages.live_booking_page import LiveBookingPage
from ..pages.live_list_page import LiveListPage
from ..pages.user_management_page import UserManagementPage

# 核心功能导入
from ...core.config_manager import ConfigManager
from ...core.database import DatabaseManager
from ...core.auth_manager import AuthManager
from ...core.token_manager import TokenManager
from ...core.task_manager import TaskManager
from ...api.wecom import WeComAPI

# 模型导入
from ...models.corporation import Corporation

# 工具类导入
from ...utils.logger import get_logger

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, user, config_manager, db_manager, auth_manager):
        super().__init__()
        self.setWindowTitle("企业微信直播签到系统")
        
        # 获取屏幕尺寸
        screen = QGuiApplication.primaryScreen().geometry()
        width = int(screen.width() * 4 / 5)
        height = int(screen.height() * 2 / 3)
        
        # 设置窗口大小
        self.resize(width, height)
        
        # 将窗口移动到屏幕中央
        self.move(int((screen.width() - width) / 2),
                 int((screen.height() - height) / 2))
        
        # 保存管理器
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.auth_manager = auth_manager
        
        # 创建新的会话并重新获取用户对象
        self.db_session = self.db_manager.Session()
        self.user = self.db_session.merge(user)
        
        # 设置当前用户到配置管理器
        self.config_manager.set_current_user(self.user)
        
        # 初始化主题管理器
        self.theme_manager = ThemeManager()
        
        # 获取企业信息
        try:
            # 先从数据库获取企业信息
            corporations = self.db_session.query(Corporation).filter_by(status=True).all()
            if corporations:
                # 在会话关闭前获取所有需要的数据
                corp = corporations[0]  # 使用第一个企业的信息
                corp_info = {
                    'corp_id': corp.corp_id,
                    'corp_secret': corp.corp_secret
                }
                self.wecom_api = WeComAPI(
                    corpid=corp_info['corp_id'],
                    corpsecret=corp_info['corp_secret']
                )
            else:
                # 如果数据库中没有企业信息，从配置文件获取
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
        except Exception as e:
            logger.error(f"获取企业信息失败: {str(e)}")
            self.wecom_api = None
        
        # 初始化任务管理器
        if self.wecom_api is None and self.user.login_name.lower() != 'root-admin':
            QMessageBox.warning(self, "警告", "未找到有效的企业配置信息，部分功能可能无法使用")
        
        # 只有在wecom_api可用或用户是root-admin时才初始化任务管理器
        if self.wecom_api is not None or self.user.login_name.lower() == 'root-admin':
            self.task_manager = TaskManager(self.wecom_api, self.db_manager)
        else:
            self.task_manager = None
        
        # 设置UI
        self.init_ui()
        
        # 应用主题设置
        self._apply_theme()
        
    def _apply_theme(self):
        """应用主题设置"""
        try:
            # 从配置获取主题设置
            theme = self.config_manager.get_theme()
            
            # 应用主题
            self.theme_manager.apply_theme(theme)
            
        except Exception as e:
            logger.error(f"应用主题失败: {str(e)}")
        
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
        
        # 如果是root-admin或者wecom_api可用，启用所有按钮
        buttons_enabled = self.user.login_name.lower() == 'root-admin' or self.wecom_api is not None
        self.live_booking_btn.setEnabled(buttons_enabled)
        self.live_list_btn.setEnabled(buttons_enabled)
        
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
        
        # 添加设置按钮
        self.settings_btn = QPushButton("系统设置")
        self.settings_btn.setObjectName("menuButton")
        self.settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(self.settings_btn)
        
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
            
        # 检查task_manager是否可用
        if self.task_manager is None:
            QMessageBox.warning(self, "警告", "任务管理器未初始化，无法使用此功能")
            return
            
        # 创建页面
        page = LiveBookingPage(
            self.db_manager,
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
            
        # 检查task_manager是否可用
        if self.task_manager is None:
            QMessageBox.warning(self, "警告", "任务管理器未初始化，无法使用此功能")
            return
            
        # 创建页面
        page = LiveListPage(
            self.wecom_api,
            self.task_manager
        )
        self.content_stack.addWidget(page)
        self.content_stack.setCurrentWidget(page)
        
    def show_settings(self):
        """显示设置页面"""
        # 检查权限
        if not self.check_permission("manage_settings"):
            QMessageBox.warning(self, "警告", "您没有权限访问此功能")
            return
            
        # 创建页面
        page = SettingsPage(
            self.auth_manager,
            self.db_manager
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
        try:
             # 刷新用户对象以确保状态最新
            self._refresh_user()
            
            # 使用当前登录用户
            if self.user:
                return self.auth_manager.has_permission(self.user.login_name, permission)
            return False
        except Exception as e:
            logger.error(f"检查权限失败: {str(e)}")
            return False

    def _get_page_title(self, page_name: str) -> str:
        """获取页面标题"""
        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.addTab(HomePage(self.db_manager), "首页")
        tab_widget.addTab(StatsPage(self.db_manager), "统计")
        tab_widget.addTab(SettingsPage(self.db_manager), "设置")
        return tab_widget.tabText(tab_widget.currentIndex())

    def _refresh_user(self):
        """刷新用户对象，确保与会话绑定"""
        try:
            if self.db_session and self.user:
                self.user = self.db_session.merge(self.user)
                self.db_session.refresh(self.user)
        except Exception as e:
            logger.error(f"刷新用户对象失败: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭时的处理"""
        try:
            if self.db_session:
                self.db_session.close()
        except Exception as e:
            logger.error(f"关闭数据库会话时发生错误: {str(e)}")
        super().closeEvent(event)