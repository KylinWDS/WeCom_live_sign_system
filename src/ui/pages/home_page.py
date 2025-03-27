from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QToolBar,
                             QStackedWidget, QTabWidget, QTabBar, QFrame, QSplitter,
                             QGridLayout, QScrollArea)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QPixmap, QFont
from src.ui.managers.style import StyleManager
from src.ui.utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from src.ui.managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.core.database import DatabaseManager
from src.models.living import Living, LivingStatus
from src.ui.components.dialogs.io_dialog import IODialog
from src.core.auth_manager import AuthManager
from src.models.user import User
import pandas as pd
import os
import datetime
from src import __version__  # 添加导入 __version__

# 导入页面
from src.ui.pages.stats_page import StatsPage
from src.ui.pages.settings_page import SettingsPage
from src.ui.pages.live_booking_page import LiveBookingPage
from src.ui.pages.live_list_page import LiveListPage
from src.ui.pages.corp_manage_page import CorpManagePage  # 添加企业管理页面的导入

logger = get_logger(__name__)

class HomePage(QWidget):
    """
    首页 - 应用的核心页面
    集成了导航功能和内容管理
    """
    
    # 定义信号
    logout_requested = Signal()  # 用户请求登出
    
    def __init__(self, db_manager: DatabaseManager, auth_manager: AuthManager, wecom_api=None, task_manager=None, user_id=None):
        super().__init__()
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.wecom_api = wecom_api
        self.task_manager = task_manager
        self.user_id = user_id  # 存储用户ID而不是用户对象
        
        self.init_ui()
        self.load_dashboard_data()
        
        # 日志
        logger.info("首页初始化完成")
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("homePage")
        
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建左侧导航
        self.create_left_menu()
        main_layout.addWidget(self.left_menu)
        
        # 创建右侧内容区域
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.content_area)
        
        # 创建内容堆栈
        self.content_stack = QTabWidget()
        self.content_stack.setTabsClosable(True)
        self.content_stack.setMovable(True)
        self.content_stack.tabCloseRequested.connect(self.close_tab)
        self.content_layout.addWidget(self.content_stack)
        
        # 创建仪表盘作为第一个标签页
        self.dashboard = self.create_dashboard()
        self.content_stack.addTab(self.dashboard, "仪表盘")
        self.content_stack.tabBar().setTabButton(0, QTabBar.RightSide, None)  # 首页标签不可关闭
        
        # 设置内容区域和导航区域的比例为4:1
        main_layout.setStretch(0, 1)  # 导航区域
        main_layout.setStretch(1, 4)  # 内容区域
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_main_style())
        
        # 添加淡入动画
        AnimationManager.fade_in(self)
        
    def create_left_menu(self):
        """创建左侧菜单"""
        # 创建左侧菜单容器
        self.left_menu = QWidget()
        self.left_menu.setFixedWidth(160)
        self.left_menu.setObjectName("leftMenu")
        
        # 创建左侧菜单布局
        layout = QVBoxLayout(self.left_menu)
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
        
        # 添加统计信息按钮
        self.stats_btn = QPushButton("数据统计")
        self.stats_btn.setObjectName("menuButton")
        self.stats_btn.clicked.connect(self.show_stats_page)
        layout.addWidget(self.stats_btn)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 更新UI状态
        self.update_menu_ui()
    
    def update_menu_ui(self):
        """根据用户权限更新菜单UI"""
        # 创建临时会话检查权限
        with self.db_manager.get_session() as session:
            # 启用/禁用对应的按钮
            has_user_mgmt_perm = self.auth_manager.has_permission(self.user_id, "manage_users", session) if self.user_id else False
            has_live_mgmt_perm = self.auth_manager.has_permission(self.user_id, "manage_live", session) if self.user_id else False
            has_stats_perm = self.auth_manager.has_permission(self.user_id, "view_stats", session) if self.user_id else False
            
            # 用户管理
            self.live_booking_btn.setEnabled(has_live_mgmt_perm)
            self.live_list_btn.setEnabled(has_live_mgmt_perm)
            self.stats_btn.setEnabled(has_stats_perm)
    
    def create_dashboard(self) -> QWidget:
        """创建仪表盘页面"""
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_layout.setSpacing(15)
        
        # 设置仪表盘样式
        dashboard_widget.setObjectName("dashboardWidget")
        
        # 添加欢迎信息 - 使用临时会话获取用户名
        welcome_label = QLabel()
        welcome_label.setObjectName("welcomeLabel")
        
        with self.db_manager.get_session() as session:
            # 如果有用户ID则获取用户信息
            if self.user_id:
                from src.models.user import User
                user = session.query(User).filter_by(userid=self.user_id).first()
                if user:
                    welcome_label.setText(f"欢迎回来，{user.name}！")
                else:
                    welcome_label.setText("欢迎使用企业微信直播签到系统")
            else:
                welcome_label.setText("欢迎使用企业微信直播签到系统")
        
        dashboard_layout.addWidget(welcome_label)
        
        # 添加版本信息
        version_label = QLabel(f"版本: {__version__}")
        version_label.setObjectName("versionLabel")
        dashboard_layout.addWidget(version_label)
        
        # 添加统计信息
        stats_widget = self.create_stats_widget()
        dashboard_layout.addWidget(stats_widget)
        
        # 添加快捷操作
        quick_actions = self.create_quick_actions()
        dashboard_layout.addWidget(quick_actions)
        
        # 设置布局
        dashboard_widget.setLayout(dashboard_layout)
        return dashboard_widget
    
    def create_stats_widget(self):
        """创建统计信息小部件"""
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(20)
        
        # 设置样式
        stats_widget.setObjectName("statsWidget")
        
        # 使用临时会话获取统计数据
        with self.db_manager.get_session() as session:
            # 获取数据统计
            from src.models.living import Living
            from src.models.user import User
            from src.models.sign_record import SignRecord
            
            # 获取直播、用户和签到数量
            live_count = session.query(Living).count()
            user_count = session.query(User).count()
            sign_count = session.query(SignRecord).count()
            
            # 创建统计卡片
            stats_cards = [
                {"title": "总直播数", "value": str(live_count), "icon": "📺"},
                {"title": "总用户数", "value": str(user_count), "icon": "👥"},
                {"title": "总签到数", "value": str(sign_count), "icon": "✅"}
            ]
            
            # 添加统计卡片
            for card_data in stats_cards:
                card = self.create_stat_card(
                    card_data["title"],
                    card_data["value"],
                    card_data["icon"]
                )
                stats_layout.addWidget(card)
        
        return stats_widget
    
    def create_quick_actions(self):
        """创建快捷操作区域"""
        quick_actions_widget = QWidget()
        quick_actions_layout = QVBoxLayout(quick_actions_widget)
        quick_actions_layout.setContentsMargins(0, 10, 0, 10)
        
        # 标题
        title_label = QLabel("快捷操作")
        title_label.setObjectName("sectionTitle")
        quick_actions_layout.addWidget(title_label)
        
        # 创建按钮区域
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 10, 0, 10)
        buttons_layout.setSpacing(15)
        
        # 使用临时会话检查权限
        with self.db_manager.get_session() as session:
            # 根据用户权限创建快捷操作按钮
            has_live_mgmt_perm = self.auth_manager.has_permission(self.user_id, "manage_live", session) if self.user_id else False
            has_user_mgmt_perm = self.auth_manager.has_permission(self.user_id, "manage_users", session) if self.user_id else False
            
            # 添加快速创建直播按钮
            if has_live_mgmt_perm:
                create_live_btn = self.create_action_button(
                    "创建直播",
                    "fas.calendar-plus",
                    lambda: self.content_stack.setCurrentWidget(self.live_booking_page)
                )
                buttons_layout.addWidget(create_live_btn)
            
            # 添加查看统计按钮
            stats_btn = self.create_action_button(
                "查看统计",
                "fas.chart-line",
                lambda: self.show_stats_page()
            )
            buttons_layout.addWidget(stats_btn)
            
            # 添加用户管理按钮
            if has_user_mgmt_perm:
                user_mgmt_btn = self.create_action_button(
                    "用户管理",
                    "fas.users-cog",
                    lambda: self.content_stack.setCurrentWidget(self.user_management_page)
                )
                buttons_layout.addWidget(user_mgmt_btn)
        
        quick_actions_widget.setLayout(quick_actions_layout)
        quick_actions_layout.addWidget(buttons_widget)
        
        return quick_actions_widget
    
    def load_dashboard_data(self):
        """加载仪表盘数据"""
        try:
            # 这个方法需要更新，但目前仪表盘组件还不完整
            # 仅记录日志，不执行任何操作
            logger.info("仪表盘数据加载功能将在组件完善后实现")
            # 以下代码暂时注释掉，等UI组件开发完成后再启用
            """
            with self.db_manager.get_session() as session:
                # 获取直播总数
                live_count = session.query(Living).count()
                self.value_live_count.setText(str(live_count))
                
                # 获取活跃直播数
                active_live_count = session.query(Living).filter(Living.status == LivingStatus.LIVING).count()
                self.value_active_live_count.setText(str(active_live_count))
                
                # 获取用户总数
                user_count = session.query(User).count()
                self.value_user_count.setText(str(user_count))
                
                # 获取今日签到数
                from src.models.sign_record import SignRecord
                import datetime
                today = datetime.date.today()
                today_sign_count = session.query(SignRecord).filter(
                    SignRecord.sign_time >= today
                ).count()
                self.value_today_sign_count.setText(str(today_sign_count))
                
                # 获取本周直播数
                from datetime import datetime, timedelta
                week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
                week_live_count = session.query(Living).filter(
                    Living.living_start >= week_start
                ).count()
                self.value_week_live_count.setText(str(week_live_count))
                
                # 加载最近的直播
                recent_lives = session.query(Living).order_by(Living.living_start.desc()).limit(5).all()
                self.recent_table.setRowCount(0)
                for live in recent_lives:
                    row = self.recent_table.rowCount()
                    self.recent_table.insertRow(row)
                    
                    self.recent_table.setItem(row, 0, QTableWidgetItem(live.theme))
                    self.recent_table.setItem(row, 1, QTableWidgetItem(str(live.living_start)))
                    self.recent_table.setItem(row, 2, QTableWidgetItem(str(live.status)))
                    self.recent_table.setItem(row, 3, QTableWidgetItem(str(live.viewer_num)))
                    
                    # 获取签到人数
                    sign_count = session.query(SignRecord).filter(SignRecord.living_id == live.id).count()
                    self.recent_table.setItem(row, 4, QTableWidgetItem(str(sign_count)))
            """
        except Exception as e:
            logger.error(f"加载仪表盘数据失败: {str(e)}")
            # 不显示错误消息，避免影响用户体验
            pass
    
    def request_logout(self):
        """请求退出登录"""
        # 在会话中安全地记录用户登出信息
        with self.db_manager.get_session() as session:
            if self.user_id:
                logger.info(f"用户 {self.user_id} 请求退出登录")
                
        confirm = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出登录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.logout_requested.emit()
    
    def check_permission(self, permission: str) -> bool:
        """检查是否有指定权限
        
        Args:
            permission: 权限名称
            
        Returns:
            bool: 是否有权限
        """
        with self.db_manager.get_session() as session:
            return self.auth_manager.has_permission(self.user_id, permission, session) if self.user_id else False
    
    def close_tab(self, index):
        """关闭标签页
        
        Args:
            index: 标签页索引
        """
        # 不允许关闭仪表盘标签
        if index == 0:
            return
            
        # 关闭标签页
        widget = self.content_stack.widget(index)
        self.content_stack.removeTab(index)
        
        # 释放资源
        if widget:
            widget.deleteLater()
    
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
        
        # 检查是否已经打开了该页面
        for i in range(self.content_stack.count()):
            if self.content_stack.tabText(i) == "预约直播":
                self.content_stack.setCurrentIndex(i)
                return
            
        # 创建页面
        page = LiveBookingPage(
            self.db_manager,
            self.wecom_api,
            self.task_manager,
            user_id=self.user_id  # 传递用户ID
        )
        index = self.content_stack.addTab(page, "预约直播")
        self.content_stack.setCurrentIndex(index)
        
    def show_live_list(self):
        """显示直播列表页面"""
        # 检查权限
        if not self.check_permission("manage_live"):
            QMessageBox.warning(self, "警告", "您没有权限访问此功能")
            return
        
        # 检查是否已经打开了该页面
        for i in range(self.content_stack.count()):
            if self.content_stack.tabText(i) == "直播列表":
                self.content_stack.setCurrentIndex(i)
                return
            
        # 创建页面
        page = LiveListPage(
            self.db_manager,    # 数据库管理器
            self.wecom_api,     # 企业微信API
            auth_manager=self.auth_manager,  # 授权管理器
            user_id=self.user_id  # 用户ID
        )
        index = self.content_stack.addTab(page, "直播列表")
        self.content_stack.setCurrentIndex(index)
        
    def show_settings(self):
        """显示设置页面"""
        # 检查权限
        if not self.check_permission("manage_settings"):
            QMessageBox.warning(self, "警告", "您没有权限访问此功能")
            return
        
        # 检查是否已经打开了该页面
        for i in range(self.content_stack.count()):
            if self.content_stack.tabText(i) == "系统设置":
                self.content_stack.setCurrentIndex(i)
                return
            
        # 创建页面
        page = SettingsPage(
            self.auth_manager,
            self.db_manager,
            user_id=self.user_id
        )
        index = self.content_stack.addTab(page, "系统设置")
        self.content_stack.setCurrentIndex(index)
        
    def show_stats_page(self):
        """显示数据统计页面"""
        # 检查用户权限
        if not self.check_permission("view_stats"):
            ErrorHandler.handle_warning("您没有查看统计信息的权限", self, "权限错误")
            return
        
        # 查找是否已经打开了统计页面
        for i in range(self.content_stack.count()):
            if "statsPage" in self.content_stack.widget(i).objectName():
                self.content_stack.setCurrentIndex(i)
                return
        
        # 创建统计页面并添加到标签页
        stats_page = StatsPage(self.db_manager, self.auth_manager)
        self.content_stack.addTab(stats_page, "数据统计")
        self.content_stack.setCurrentWidget(stats_page)
    
    def show_corp_manage(self):
        """显示企业管理页面
        
        注意: 此方法保留但标记为内部方法，通过设置页面而非直接菜单访问
        企业管理已集成到系统设置中，此功能仅作为内部方法保留
        """
        # 检查权限
        if not self.check_permission("manage_corps"):
            QMessageBox.warning(self, "警告", "您没有权限访问此功能")
            return
            
        # 检查是否已有相同标签
        for i in range(self.content_stack.count()):
            if self.content_stack.tabText(i) == "企业管理":
                self.content_stack.setCurrentIndex(i)
                return
        
        # 创建企业管理页面
        corp_manage_page = CorpManagePage(
            self.db_manager,
            auth_manager=self.auth_manager,
            user_id=self.user_id
        )
        self.content_stack.addTab(corp_manage_page, "企业管理")
        self.content_stack.setCurrentWidget(corp_manage_page)
    
    def show_performance_monitor(self):
        """显示性能监控页面"""
        # 检查权限
        if not self.check_permission("view_system_monitor"):
            QMessageBox.warning(self, "警告", "您没有权限访问此功能")
            return
        
        # 检查是否已经打开了该页面
        for i in range(self.content_stack.count()):
            if self.content_stack.tabText(i) == "性能监控":
                self.content_stack.setCurrentIndex(i)
                return
            
        # 创建页面
        from src.ui.components.widgets.performance_monitor import PerformanceMonitor
        page = PerformanceMonitor()
        index = self.content_stack.addTab(page, "性能监控")
        self.content_stack.setCurrentIndex(index)

    def create_stat_card(self, title: str, value: str, icon: str) -> QWidget:
        """创建统计卡片

        Args:
            title: 卡片标题
            value: 卡片数值
            icon: 卡片图标名称

        Returns:
            QWidget: 统计卡片小部件
        """
        from src.ui.utils.icon_provider import get_icon
        
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(120)
        card.setMaximumHeight(150)
        
        # 创建布局
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 添加图标和标题
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)
        
        # 图标 
        icon_label = QLabel()
        icon_label.setObjectName("statIcon")
        
        # 如果提供了图标名称
        if icon:
            # 检查是否是Emoji (简单检查)
            if len(icon) == 1 or (len(icon) == 2 and ord(icon[0]) > 127):
                # 直接使用Emoji作为文本
                icon_label.setText(icon)
                icon_label.setStyleSheet("font-size: 24px;")  # 设置Emoji大小
            else:
                # 使用图标提供器获取图标
                icon_pixmap = get_icon(icon).pixmap(QSize(24, 24))
                icon_label.setPixmap(icon_pixmap)
                
        header.addWidget(icon_label)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # 添加数值
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(value_label)
        
        return card

    def create_action_button(self, text: str, icon_name: str = None, on_click=None) -> QPushButton:
        """创建操作按钮

        Args:
            text: 按钮文本
            icon_name: 图标名称（Font Awesome 类名）
            on_click: 点击回调函数

        Returns:
            QPushButton: 按钮控件
        """
        button = QPushButton(text)
        button.setObjectName("actionButton")
        button.setMinimumHeight(40)
        
        # 设置图标
        if icon_name:
            from src.ui.utils.icon_provider import get_icon
            icon = get_icon(icon_name)
            if icon:
                button.setIcon(icon)
                button.setIconSize(QSize(18, 18))
        
        # 设置点击回调
        if on_click:
            button.clicked.connect(on_click)
            
        return button

    def switchToLiveList(self):
        """切换到直播列表页面(用于从其他页面导航)"""
        try:
            logger.info("请求切换到直播列表页面")
            self.show_live_list()
        except Exception as e:
            logger.error(f"切换到直播列表页面时出错: {str(e)}")