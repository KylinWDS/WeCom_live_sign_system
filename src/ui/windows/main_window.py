# PySide6导入
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QTabWidget, QStackedWidget,
    QLineEdit, QComboBox, QMenuBar, QMenu, QStatusBar, QTabBar
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QIcon, QGuiApplication

# UI相关导入
from ..managers.style import StyleManager
from ..managers.theme_manager import ThemeManager
from ..utils.widget_utils import WidgetUtils
from ..managers.animation import AnimationManager
from ..pages.home_page import HomePage

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
        
        # 使用临时会话获取用户信息，不再持久保持会话对象
        with self.db_manager.get_session() as session:
            # 合并用户对象到会话
            user_obj = session.merge(user)
            
            # 存储用户ID和基本信息，而不是完整对象
            self.user_id = user_obj.userid
            self.user_name = user_obj.name
            self.user_login_name = user_obj.login_name
            self.user_role = user_obj.role
            self.corp_name = user_obj.corpname if user_obj.corpname else "系统管理"
            
            # 设置当前用户到认证管理器和配置管理器
            self.auth_manager.set_current_user(user_obj)
            self.config_manager.set_current_user(user_obj)
            
            # 获取企业信息
            try:
                # 从数据库获取企业信息
                corporations = session.query(Corporation).filter_by(status=True).all()
                if corporations:
                    # 获取企业基本信息
                    corp = corporations[0]  # 使用第一个企业的信息
                    corp_info = {
                        'corp_id': corp.corp_id,
                        'corp_secret': corp.corp_secret,
                        'agent_id': corp.agent_id
                    }
                    self.wecom_api = WeComAPI(
                        corpid=corp_info['corp_id'],
                        corpsecret=corp_info['corp_secret'],
                        agent_id=corp_info['agent_id']
                    )
                else:
                    # 如果数据库中没有企业信息，从配置文件获取
                    corporations = self.config_manager.get_corporations()
                    if corporations:
                        corp = corporations[0]  # 使用第一个企业的信息
                        self.wecom_api = WeComAPI(
                            corpid=corp["corpid"],
                            corpsecret=corp["corpsecret"],
                            agent_id=corp.get("agentid")
                        )
                    else:
                        self.wecom_api = None
                        logger.warning("未找到企业配置信息")
            except Exception as e:
                logger.error(f"获取企业信息失败: {str(e)}")
                self.wecom_api = None
        
        # 初始化任务管理器
        if self.wecom_api is None and self.user_login_name.lower() != 'root-admin':
            QMessageBox.warning(self, "警告", "未找到有效的企业配置信息，部分功能可能无法使用")
        
        # 只有在wecom_api可用或用户是root-admin时才初始化任务管理器
        if self.wecom_api is not None or self.user_login_name.lower() == 'root-admin':
            self.task_manager = TaskManager(self.wecom_api, self.db_manager)
        else:
            self.task_manager = None
        
        # 设置UI
        self.init_ui()
        
        # 应用主题设置
        self._apply_theme()
        
        # 更新UI状态
        self.update_ui()
        
    def _apply_theme(self):
        """应用主题设置"""
        try:
            # 从配置获取主题设置
            theme = self.config_manager.get_theme()
            
            # 应用主题
            logger.info(f"应用主题成功: {theme}")
            
        except Exception as e:
            logger.error(f"应用主题失败: {str(e)}")
        
    def init_ui(self):
        """初始化UI"""
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建状态栏中的信息标签
        self.corp_label = QLabel()
        self.corp_label.setObjectName("statusCorpLabel")
        
        self.user_label = QLabel()
        self.user_label.setObjectName("statusUserLabel")
        
        self.disclaimer_label = QLabel("免责声明：本系统仅用于企业内部使用，禁止用于任何商业用途。© 2025 企业微信直播签到系统")
        self.disclaimer_label.setObjectName("disclaimerLabel")
        
        # 添加标签到状态栏
        self.status_bar.addWidget(self.corp_label)
        self.status_bar.addWidget(self.user_label, 1)  # 1表示拉伸因子，让用户标签居中
        self.status_bar.addPermanentWidget(self.disclaimer_label)  # 永久部件，靠右显示
        
        # 创建中央窗口 - 使用HomePage
        self.home_page = HomePage(
            self.db_manager,
            self.auth_manager,
            self.wecom_api,
            self.task_manager,
            user_id=self.user_id  # 传递用户ID而不是对象
        )
        self.home_page.logout_requested.connect(self.relogin)
        self.setCentralWidget(self.home_page)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_main_style())
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        file_menu.setObjectName("fileMenu")
        
        # 重新登录动作
        relogin_action = file_menu.addAction("重新登录")
        relogin_action.triggered.connect(self.relogin)
        
        # 退出动作
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 系统管理菜单（原为"设置"）
        system_menu = menubar.addMenu("系统管理")
        
        # 系统设置动作
        system_settings_action = system_menu.addAction("系统设置")
        system_settings_action.triggered.connect(self.show_settings)
        
        # 添加分隔线
        system_menu.addSeparator()
        
        # 系统监控动作
        performance_action = system_menu.addAction("性能监控")
        performance_action.triggered.connect(self.show_performance_monitor)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.setObjectName("helpMenu")
        
        # 关于动作
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)
        
        # 使用手册动作
        manual_action = help_menu.addAction("使用手册")
        manual_action.triggered.connect(self.show_manual)
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "企业微信直播签到系统 v0.0.1\n\n"
            "用于管理企业微信直播和签到信息的系统。"
        )
    
    def show_manual(self):
        """显示使用手册"""
        QMessageBox.information(
            self, 
            "使用手册",
            "企业微信直播签到系统使用手册\n\n"
            "1. 首页仪表盘：显示系统概览和关键指标\n"
            "2. 预约直播：创建和管理直播预约\n"
            "3. 直播列表：查看和管理所有直播\n"
            "4. 数据统计：查看直播和签到统计数据\n\n"
            "详细使用说明请参考系统文档。"
        )

    def check_permission(self, permission: str) -> bool:
        """检查当前用户是否有指定权限"""
        try:
            # 使用新的会话和用户ID检查权限
            with self.db_manager.get_session() as session:
                return self.auth_manager.has_permission(self.user_login_name, permission, session)
        except Exception as e:
            logger.error(f"检查权限失败: {str(e)}")
            return False

    def closeEvent(self, event):
        """窗口关闭时的处理"""
        # 清理资源，但不再需要关闭会话
        super().closeEvent(event)

    def relogin(self):
        """重新登录，关闭当前窗口，打开登录窗口"""
        try:
            # 清除认证状态
            self.auth_manager.clear_current_user()
            
            # 导入QApplication来获取应用实例
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            # 创建登录窗口
            from ..windows.login_window import LoginWindow
            
            # 创建登录窗口并保存引用到应用程序的属性中
            app._login_window = LoginWindow(self.auth_manager, self.config_manager, self.db_manager)
            app._login_window.show()
            
            logger.info("用户请求重新登录")
            
            # 关闭当前窗口
            self.close()
            
        except Exception as e:
            logger.error(f"重新登录失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"重新登录失败: {str(e)}")

    def update_ui(self):
        """更新UI，使用存储的用户属性"""
        # 设置窗口标题
        self.setWindowTitle(f"企业微信直播签到系统 | 用户: {self.user_name}")
        
        # 获取角色名称
        role_names = {
            "ROOT_ADMIN": "超级管理员",
            "WECOM_ADMIN": "企业管理员",
            "NORMAL": "普通用户"
        }
        role_name = role_names.get(self.user_role, "未知角色")
        
        # 更新状态栏信息
        self.corp_label.setText(f"企业: {self.corp_name}")
        self.user_label.setText(f"用户: {self.user_name} ({role_name})")

    def show_settings(self):
        """显示系统设置页面"""
        # 调用home_page上的show_settings方法
        if hasattr(self.home_page, 'show_settings'):
            self.home_page.show_settings()
        else:
            logger.error("Home page没有show_settings方法")
            QMessageBox.warning(self, "警告", "系统设置功能不可用")
    
    def show_performance_monitor(self):
        """显示性能监控页面"""
        # 调用home_page上的show_performance_monitor方法
        if hasattr(self.home_page, 'show_performance_monitor'):
            self.home_page.show_performance_monitor()
        else:
            logger.error("Home page没有show_performance_monitor方法")
            QMessageBox.warning(self, "警告", "性能监控功能不可用")
    
    def show_stats_page(self):
        """显示数据统计页面"""
        # 调用home_page上的show_stats_page方法
        if hasattr(self.home_page, 'show_stats_page'):
            self.home_page.show_stats_page()
        else:
            logger.error("Home page没有show_stats_page方法")
            QMessageBox.warning(self, "警告", "数据统计功能不可用")