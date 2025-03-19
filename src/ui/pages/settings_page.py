from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QCheckBox, QSpinBox,
                             QToolBar, QSpacerItem, QSizePolicy, QScrollArea, QFrame,
                             QAbstractItemView, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..managers.theme_manager import ThemeManager
from ..utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from ..managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.core.auth_manager import AuthManager
from src.core.database import DatabaseManager
from src.core.config_manager import ConfigManager
from src.models.user import UserRole
from src.models.settings import Settings
from ..components.dialogs.io_dialog import IODialog
from src.models.corporation import Corporation
from src.models.user import User
from ..components.dialogs.init_wizard import InitWizard
import pandas as pd
import os
import json
import shutil

from ...models import SignRecord

logger = get_logger(__name__)

class SettingsPage(QWidget):
    """设置页面"""
    
    def __init__(self, auth_manager: AuthManager, db_manager: DatabaseManager):
        super().__init__()
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.theme_manager = ThemeManager()
        self.config_manager = ConfigManager()
        
        # 初始化表单控件
        self.corp_name = None
        self.corp_id = None
        self.corp_secret = None
        self.agent_id = None
        self.corp_status = None
        self.user_name = None
        self.user_role = None
        self.user_is_admin = None
        self.user_status = None
        self.user_wecom_code = None
        self.user_corp = None
        
        # 获取配置路径
        default_config_dir = os.path.join(os.path.expanduser("~"), ".wecom_live_sign")
        default_config_file = os.path.join(default_config_dir, "config.json")
        
        # 确保默认配置目录存在
        os.makedirs(default_config_dir, exist_ok=True)
        
        # 如果默认配置文件不存在，创建默认配置
        if not os.path.exists(default_config_file):
            config_dir = default_config_dir
        
        # 读取默认配置文件
        try:
            with open(default_config_file, 'r', encoding='utf-8') as f:
                default_config = json.load(f)
                initialized = default_config.get('initialized', False)
                
                # 如果已经初始化，检查所有路径是否都已配置
                if initialized:
                    paths = default_config.get('paths', {})
                    if all(paths.values()) and all(os.path.exists(path) for path in paths.values()):
                        config_dir = paths['config']
                    else:
                        config_dir = default_config_dir
                else:
                    config_dir = default_config_dir
                    
        except Exception as e:
            logger.error(f"读取默认配置文件失败: {str(e)}")
            config_dir = default_config_dir
            
        # 初始化配置管理器
        self.config_manager.initialize(config_dir)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("settingsPage")
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建企业信息列表
        corp_group = QGroupBox("企业信息管理")
        corp_layout = QVBoxLayout(corp_group)
        corp_layout.setSpacing(10)
        corp_layout.setContentsMargins(10, 10, 10, 10)
        
        # 设置企业表格
        self.corp_table = QTableWidget()
        self.corp_table.setColumnCount(7)
        self.corp_table.setHorizontalHeaderLabels([
            "企业名称", "企业ID", "应用Secret", "应用ID",
            "企业状态", "更新时间", "操作"
        ])
        
        # 设置列宽
        header = self.corp_table.horizontalHeader()
        for i in range(6):  # 除了操作列外的其他列
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # 操作列固定宽度
        self.corp_table.setColumnWidth(6, 200)  # 设置操作列宽度
        
        self._setup_table(self.corp_table)
        corp_layout.addWidget(self.corp_table)
        
        # 企业管理按钮布局
        corp_btn_layout = QHBoxLayout()
        corp_btn_layout.setSpacing(10)
        
        add_corp_btn = QPushButton("新增企业")
        add_corp_btn.setObjectName("primaryButton")
        add_corp_btn.setFixedWidth(120)
        add_corp_btn.clicked.connect(self.add_corp)
        
        save_corp_btn = QPushButton("保存企业信息")
        save_corp_btn.setObjectName("primaryButton")
        save_corp_btn.setFixedWidth(120)
        save_corp_btn.clicked.connect(self._save_corp_settings)
        
        corp_btn_layout.addStretch()
        corp_btn_layout.addWidget(add_corp_btn)
        corp_btn_layout.addWidget(save_corp_btn)
        corp_layout.addLayout(corp_btn_layout)
        
        # 用户管理列表
        user_group = QGroupBox("用户管理")
        user_layout = QVBoxLayout(user_group)
        user_layout.setSpacing(10)
        user_layout.setContentsMargins(10, 10, 10, 10)
        
        # 设置用户表格
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(11)
        self.user_table.setHorizontalHeaderLabels([
            "登录名", "用户名", "角色", "企业名称", "是否管理员",
            "状态", "企业微信账号", "上次登录", "创建时间", "更新时间", "操作"
        ])
        
        # 设置列宽
        header = self.user_table.horizontalHeader()
        for i in range(10):  # 除了操作列外的其他列
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.Fixed)  # 操作列固定宽度
        self.user_table.setColumnWidth(10, 250)  # 设置操作列宽度
        
        self._setup_table(self.user_table)
        user_layout.addWidget(self.user_table)
        
        # 用户管理按钮布局
        user_btn_layout = QHBoxLayout()
        user_btn_layout.setSpacing(10)
        
        add_user_btn = QPushButton("新增用户")
        add_user_btn.setObjectName("primaryButton")
        add_user_btn.setFixedWidth(120)
        add_user_btn.clicked.connect(self.add_user)
        
        save_user_btn = QPushButton("保存用户信息")
        save_user_btn.setObjectName("primaryButton")
        save_user_btn.setFixedWidth(120)
        save_user_btn.clicked.connect(self._save_user_settings)
        
        user_btn_layout.addStretch()
        user_btn_layout.addWidget(add_user_btn)
        user_btn_layout.addWidget(save_user_btn)
        user_layout.addLayout(user_btn_layout)
        
        # 系统设置和数据管理布局
        settings_container = QWidget()
        settings_layout = QHBoxLayout(settings_container)
        settings_layout.setSpacing(20)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # 系统设置组
        system_group = QGroupBox("系统设置")
        system_layout = QFormLayout(system_group)
        system_layout.setSpacing(15)
        system_layout.setContentsMargins(15, 15, 15, 15)
        
        # 设置最小宽度
        system_group.setMinimumWidth(600)
        
        # 设置标签宽度
        system_layout.setLabelAlignment(Qt.AlignRight)
        system_layout.setFormAlignment(Qt.AlignLeft)
        
        # 主题设置
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["跟随系统", "明亮", "暗色"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.theme_combo.setMinimumWidth(400)
        system_layout.addRow("主题设置:", self.theme_combo)
        
        # 数据库设置
        db_container = QWidget()
        db_layout = QHBoxLayout(db_container)
        db_layout.setContentsMargins(0, 0, 0, 0)
        db_layout.setSpacing(10)
        
        self.db_path = QLineEdit()
        self.db_path.setMinimumWidth(400)
        browse_db_btn = QPushButton("浏览")
        browse_db_btn.setFixedWidth(60)
        browse_db_btn.clicked.connect(self.browse_db_path)
        
        db_layout.addWidget(self.db_path)
        db_layout.addWidget(browse_db_btn)
        system_layout.addRow("数据库路径:", db_container)
        
        # 备份文件路径
        backup_container = QWidget()
        backup_layout = QHBoxLayout(backup_container)
        backup_layout.setContentsMargins(0, 0, 0, 0)
        backup_layout.setSpacing(10)
        
        self.backup_path = QLineEdit()
        self.backup_path.setMinimumWidth(400)
        browse_backup_btn = QPushButton("浏览")
        browse_backup_btn.setFixedWidth(60)
        browse_backup_btn.clicked.connect(self.browse_backup_path)
        
        backup_layout.addWidget(self.backup_path)
        backup_layout.addWidget(browse_backup_btn)
        system_layout.addRow("备份文件路径:", backup_container)
        
        # 日志设置
        log_container = QWidget()
        log_layout = QHBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(10)
        
        self.log_path = QLineEdit()
        self.log_path.setMinimumWidth(400)
        browse_log_btn = QPushButton("浏览")
        browse_log_btn.setFixedWidth(60)
        browse_log_btn.clicked.connect(self.browse_log_path)
        
        log_layout.addWidget(self.log_path)
        log_layout.addWidget(browse_log_btn)
        system_layout.addRow("日志路径:", log_container)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setMinimumWidth(400)
        system_layout.addRow("日志级别:", self.log_level)
        
        # 重新初始化按钮
        reinit_btn = QPushButton("重新初始化系统")
        reinit_btn.setObjectName("warningButton")
        reinit_btn.setMinimumWidth(400)
        reinit_btn.clicked.connect(self.show_init_wizard)
        system_layout.addRow("系统初始化:", reinit_btn)
        
        # 数据管理设置组
        data_group = QGroupBox("数据管理")
        data_layout = QFormLayout(data_group)
        data_layout.setSpacing(15)
        data_layout.setContentsMargins(15, 15, 15, 15)
        
        # 设置最小宽度
        data_group.setMinimumWidth(400)
        
        self.data_cleanup = QCheckBox("启用自动清理")
        data_layout.addRow("数据清理:", self.data_cleanup)
        
        self.cleanup_period = QSpinBox()
        self.cleanup_period.setRange(1, 365)
        self.cleanup_period.setValue(30)
        self.cleanup_period.setSuffix(" 天")
        data_layout.addRow("清理周期:", self.cleanup_period)
        
        self.cleanup_scope = QComboBox()
        self.cleanup_scope.addItems(["全部数据", "仅签到记录", "仅日志记录"])
        data_layout.addRow("清理范围:", self.cleanup_scope)
        
        cleanup_btn = QPushButton("立即清理")
        cleanup_btn.setObjectName("warningButton")
        cleanup_btn.clicked.connect(self.cleanup_data)
        data_layout.addRow("", cleanup_btn)
        
        # 添加系统设置和数据管理到水平布局
        settings_layout.addWidget(system_group)
        settings_layout.addWidget(data_group)
        settings_layout.addStretch()
        
        # 添加所有组件到内容布局
        content_layout.addWidget(corp_group)
        content_layout.addWidget(user_group)
        content_layout.addWidget(settings_container)
        
        # 添加保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedWidth(120)
        save_btn.clicked.connect(self.save_settings)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        content_layout.addLayout(btn_layout)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
            QPushButton#primaryButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                min-width: 60px;
                min-height: 30px;
            }
            QPushButton#primaryButton:hover {
                background-color: #106ebe;
            }
            QPushButton#secondaryButton {
                background-color: #e0e0e0;
                color: #000000;
                border: none;
                padding: 3px 8px;
                border-radius: 3px;
                min-width: 40px;
                min-height: 20px;
            }
            QPushButton#secondaryButton:hover {
                background-color: #cccccc;
            }
            QPushButton#warningButton {
                background-color: #d83b01;
                color: white;
                border: none;
                padding: 3px 8px;
                border-radius: 3px;
                min-width: 60px;
                min-height: 20px;
            }
            QPushButton#warningButton:hover {
                background-color: #a62e01;
            }
            QPushButton#dangerButton {
                background-color: #e81123;
                color: white;
                border: none;
                padding: 3px 8px;
                border-radius: 3px;
                min-width: 40px;
                min-height: 20px;
            }
            QPushButton#dangerButton:hover {
                background-color: #c50f1f;
            }
            QTableWidget {
                border: 1px solid #cccccc;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 4px 8px;
                border: none;
                border-right: 1px solid #cccccc;
            }
            QTableWidget::item {
                padding: 4px 8px;
                border: none;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
        """)
        
        # 添加淡入动画
        AnimationManager.fade_in(self)
        
        # 加载数据
        self.load_data()
        
        # 根据用户权限控制UI
        self._update_ui_by_permission()
        
    def _setup_table(self, table: QTableWidget):
        """设置表格的通用属性"""
        # 设置表格样式
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setAlternatingRowColors(True)
        
        # 设置默认行高
        table.verticalHeader().setDefaultSectionSize(50)  # 增加默认行高
        # 禁止用户调整行高
        table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        
        # 设置最小高度
        table.setMinimumHeight(300)  # 设置最小高度
        
        WidgetUtils.set_table_style(table)
        
    def _update_ui_by_permission(self):
        """根据用户权限更新UI"""
        try:
            with self.db_manager.get_session() as session:
                current_user = self.auth_manager.get_current_user()
                if not current_user:
                    self.error_handler.handle_warning("未登录或登录已过期", self)
                    self.setEnabled(False)
                    return
                    
                # 在 session 范围内获取用户角色
                user_role = session.merge(current_user).role
                
                # 只有超级管理员可以访问设置页面
                if user_role != UserRole.ROOT_ADMIN.value:
                    self.error_handler.handle_warning("只有超级管理员可以访问系统设置", self)
                    self.setEnabled(False)
                    return
                
        except Exception as e:
            self.error_handler.handle_error(e, self, "更新UI权限失败")
            
    def _create_search_group(self) -> QGroupBox:
        """创建搜索区域"""
        group = QGroupBox("搜索条件")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 第一行
        row1_layout = QHBoxLayout()
        
        # 设置名称
        row1_layout.addWidget(QLabel("设置名称:"))
        self.setting_name = QLineEdit()
        WidgetUtils.set_input_style(self.setting_name)
        row1_layout.addWidget(self.setting_name)
        
        # 设置类型
        row1_layout.addWidget(QLabel("设置类型:"))
        self.setting_type = QComboBox()
        self.setting_type.addItems(["全部", "系统", "用户", "其他"])
        WidgetUtils.set_combo_style(self.setting_type)
        row1_layout.addWidget(self.setting_type)
        
        layout.addLayout(row1_layout)
        
        # 第二行
        row2_layout = QHBoxLayout()
        
        # 设置值
        row2_layout.addWidget(QLabel("设置值:"))
        self.setting_value = QLineEdit()
        WidgetUtils.set_input_style(self.setting_value)
        row2_layout.addWidget(self.setting_value)
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("primaryButton")
        search_btn.clicked.connect(self.search)
        row2_layout.addWidget(search_btn)
        
        layout.addLayout(row2_layout)
        
        return group
        
    def _create_corp_group(self) -> QGroupBox:
        """创建企业信息设置组"""
        group = QGroupBox("企业信息设置")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 设置标签的对齐方式和宽度
        layout.setLabelAlignment(Qt.AlignRight)
        layout.setFormAlignment(Qt.AlignLeft)
        
        # 企业名称
        self.corp_name = QLineEdit()
        self.corp_name.setFixedWidth(300)
        WidgetUtils.set_input_style(self.corp_name)
        layout.addRow("企业名称:", self.corp_name)
        
        # 企业ID
        self.corp_id = QLineEdit()
        self.corp_id.setFixedWidth(300)
        WidgetUtils.set_input_style(self.corp_id)
        layout.addRow("企业ID:", self.corp_id)
        
        # 企业应用Secret
        self.corp_secret = QLineEdit()
        self.corp_secret.setFixedWidth(300)
        self.corp_secret.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.corp_secret)
        layout.addRow("企业应用Secret:", self.corp_secret)
        
        # 应用ID
        self.agent_id = QLineEdit()
        self.agent_id.setFixedWidth(300)
        WidgetUtils.set_input_style(self.agent_id)
        layout.addRow("应用ID:", self.agent_id)
        
        # 企业状态
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        self.corp_status = QCheckBox("启用")
        self.corp_status.setChecked(True)
        status_layout.addWidget(self.corp_status)
        status_layout.addStretch()
        layout.addRow("企业状态:", status_container)
        
        return group
        
    def _create_user_group(self):
        """创建用户管理组"""
        group = QGroupBox("用户管理")
        layout = QVBoxLayout()
        
        # 创建工具栏
        toolbar = QHBoxLayout()
        add_btn = QPushButton("添加用户")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self.add_user)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 创建表格
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(10)
        self.user_table.setHorizontalHeaderLabels([
            "登录名", "用户名", "角色", "企业名称", "是否管理员",
            "状态", "企业微信账号", "上次登录", "创建时间", "更新时间"
        ])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.user_table.horizontalHeader().setStretchLastSection(True)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.user_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.user_table.setAlternatingRowColors(True)
        layout.addWidget(self.user_table)
        
        group.setLayout(layout)
        return group
        
    def _create_system_group(self) -> QGroupBox:
        """创建系统设置组"""
        group = QGroupBox("系统设置")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        
        # 主题设置
        self.theme = QComboBox()
        self.theme.addItems(["跟随系统", "明亮", "暗色"])
        self.theme.currentTextChanged.connect(self._on_theme_changed)
        WidgetUtils.set_combo_style(self.theme)
        layout.addRow("主题设置:", self.theme)
        
        # 数据库路径
        db_layout = QHBoxLayout()
        self.db_path = QLineEdit()
        WidgetUtils.set_input_style(self.db_path)
        db_layout.addWidget(self.db_path)
        
        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.clicked.connect(self.browse_db_path)
        db_layout.addWidget(browse_btn)
        
        layout.addRow("数据库路径:", db_layout)
        
        # 日志路径
        log_layout = QHBoxLayout()
        self.log_path = QLineEdit()
        WidgetUtils.set_input_style(self.log_path)
        log_layout.addWidget(self.log_path)
        
        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.clicked.connect(self.browse_log_path)
        log_layout.addWidget(browse_btn)
        
        layout.addRow("日志路径:", log_layout)
        
        # 日志级别
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        WidgetUtils.set_combo_style(self.log_level)
        layout.addRow("日志级别:", self.log_level)
        
        # 日志保留天数
        self.log_retention = QSpinBox()
        self.log_retention.setRange(1, 365)
        self.log_retention.setValue(30)
        self.log_retention.setSuffix(" 天")
        WidgetUtils.set_spin_style(self.log_retention)
        layout.addRow("日志保留天数:", self.log_retention)
        
        return group
        
    def _create_data_group(self) -> QGroupBox:
        """创建数据管理设置组"""
        group = QGroupBox("数据管理设置")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        
        # 数据清理
        self.data_cleanup = QCheckBox("启用自动清理")
        self.data_cleanup.setChecked(True)
        layout.addRow("数据清理:", self.data_cleanup)
        
        # 清理周期
        self.cleanup_period = QSpinBox()
        self.cleanup_period.setRange(1, 365)
        self.cleanup_period.setValue(30)
        self.cleanup_period.setSuffix(" 天")
        WidgetUtils.set_spin_style(self.cleanup_period)
        layout.addRow("清理周期:", self.cleanup_period)
        
        # 清理范围
        self.cleanup_scope = QComboBox()
        self.cleanup_scope.addItems(["全部数据", "仅签到记录", "仅日志记录"])
        WidgetUtils.set_combo_style(self.cleanup_scope)
        layout.addRow("清理范围:", self.cleanup_scope)
        
        # 清理按钮
        cleanup_btn = QPushButton("立即清理")
        cleanup_btn.setObjectName("secondaryButton")
        cleanup_btn.setIcon(QIcon(":/icons/cleanup.png"))
        cleanup_btn.clicked.connect(self.cleanup_data)
        layout.addRow("", cleanup_btn)
        
        return group
        
    def _on_theme_changed(self, theme: str):
        """主题改变处理"""
        try:
            # 转换主题名称
            theme_map = {
                "跟随系统": "system",
                "明亮": "light",
                "暗色": "dark"
            }
            theme_value = theme_map.get(theme, "light")
            
            # 应用主题
            self.theme_manager.apply_theme(theme_value)
            
            # 保存设置
            self.save_settings()
            
        except Exception as e:
            self.error_handler.handle_error(e, self, "切换主题失败")
            
    def load_data(self):
        """加载设置数据到表格"""
        try:
            # 从数据库加载设置
            with self.db_manager.get_session() as session:
                # 加载企业信息
                corps = session.query(Corporation).all()
                self.corp_table.setRowCount(0)
                for corp in corps:
                    row = self.corp_table.rowCount()
                    self.corp_table.insertRow(row)
                    
                    # 企业名称
                    self.corp_table.setItem(row, 0, QTableWidgetItem(corp.name))
                    
                    # 企业ID
                    self.corp_table.setItem(row, 1, QTableWidgetItem(corp.corp_id))
                    
                    # 应用Secret
                    self.corp_table.setItem(row, 2, QTableWidgetItem('*' * 10))
                    
                    # 应用ID
                    self.corp_table.setItem(row, 3, QTableWidgetItem(corp.agent_id))
                    
                    # 企业状态
                    self.corp_table.setItem(row, 4, QTableWidgetItem('启用' if corp.status else '禁用'))
                    
                    # 更新时间
                    self.corp_table.setItem(row, 5, QTableWidgetItem(str(corp.updated_at)))
                    
                    # 操作按钮
                    btn_widget = QWidget()
                    btn_layout = QHBoxLayout(btn_widget)
                    btn_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
                    btn_layout.setSpacing(10)  # 设置按钮间距
                    
                    edit_btn = QPushButton("修改信息")
                    edit_btn.setObjectName("secondaryButton")
                    font = edit_btn.font()
                    font.setPointSize(8)
                    edit_btn.setFont(font)
                    edit_btn.clicked.connect(lambda checked, c=corp: self.edit_corp(c))
                    btn_layout.addWidget(edit_btn)  # 添加修改按钮到布局
                    
                    delete_btn = QPushButton("删除")
                    delete_btn.setObjectName("dangerButton")
                    delete_btn.setFont(font)
                    delete_btn.clicked.connect(lambda checked, c=corp: self.delete_corp(c))
                    btn_layout.addWidget(delete_btn)  # 添加删除按钮到布局
                    
                    self.corp_table.setCellWidget(row, 6, btn_widget)
                    
                # 加载用户信息
                users = session.query(User).all()
                self.user_table.setRowCount(0)
                for user in users:
                    row = self.user_table.rowCount()
                    self.user_table.insertRow(row)
                    
                    # 登录名
                    self.user_table.setItem(row, 0, QTableWidgetItem(user.login_name))
                    
                    # 用户名
                    self.user_table.setItem(row, 1, QTableWidgetItem(user.name))
                    
                    # 角色
                    self.user_table.setItem(row, 2, QTableWidgetItem(user.role))
                    
                    # 企业名称
                    self.user_table.setItem(row, 3, QTableWidgetItem(user.corpname))
                    
                    # 是否管理员
                    self.user_table.setItem(row, 4, QTableWidgetItem('是' if user.is_admin else '否'))
                    
                    # 状态
                    self.user_table.setItem(row, 5, QTableWidgetItem('启用' if user.is_active else '禁用'))
                    
                    # 企业微信账号
                    self.user_table.setItem(row, 6, QTableWidgetItem(user.wecom_code or user.login_name))
                    
                    # 上次登录时间
                    self.user_table.setItem(row, 7, QTableWidgetItem(str(user.last_login) if user.last_login else ''))
                    
                    # 创建时间
                    self.user_table.setItem(row, 8, QTableWidgetItem(str(user.created_at)))
                    
                    # 更新时间
                    self.user_table.setItem(row, 9, QTableWidgetItem(str(user.updated_at)))
                    
                    # 操作按钮
                    btn_widget = QWidget()
                    btn_layout = QHBoxLayout(btn_widget)
                    btn_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
                    btn_layout.setSpacing(10)  # 设置按钮间距
                    
                    # 只为非root-admin用户显示修改信息按钮
                    if user.role != UserRole.ROOT_ADMIN.value:
                        edit_btn = QPushButton("修改信息")
                        edit_btn.setObjectName("secondaryButton")
                        font = edit_btn.font()
                        font.setPointSize(8)
                        edit_btn.setFont(font)
                        edit_btn.clicked.connect(lambda checked, name=user.login_name: self.edit_user(name))
                        btn_layout.addWidget(edit_btn)
                        
                        # 显示重置密码按钮
                        reset_pwd_btn = QPushButton("重置密码")
                        reset_pwd_btn.setObjectName("warningButton")
                        reset_pwd_btn.setFont(font)
                        reset_pwd_btn.clicked.connect(lambda checked, name=user.login_name: self.reset_user_password(name))
                        btn_layout.addWidget(reset_pwd_btn)
                        
                        delete_btn = QPushButton("删除")
                        delete_btn.setObjectName("dangerButton")
                        delete_btn.setFont(font)
                        delete_btn.clicked.connect(lambda checked, name=user.login_name: self.delete_user(name))
                        btn_layout.addWidget(delete_btn)
                    
                    self.user_table.setCellWidget(row, 10, btn_widget)
                    
                # 加载系统设置
                self._load_system_settings()
                    
        except Exception as e:
            self.error_handler.handle_error(e, self, "加载设置数据失败")
            
    def edit_setting(self, setting: Settings):
        """编辑设置
        
        Args:
            setting: 设置对象
        """
        try:
            # 创建编辑对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("编辑设置")
            dialog.setModal(True)
            
            # 创建表单布局
            layout = QFormLayout(dialog)
            layout.setSpacing(10)
            
            # 设置名称
            name_edit = QLineEdit(setting.name)
            WidgetUtils.set_input_style(name_edit)
            layout.addRow("设置名称:", name_edit)
            
            # 设置值
            value_edit = QLineEdit(str(setting.value))
            WidgetUtils.set_input_style(value_edit)
            layout.addRow("设置值:", value_edit)
            
            # 设置类型
            type_combo = QComboBox()
            type_combo.addItems(["系统", "用户", "其他"])
            type_combo.setCurrentText(setting.type)
            WidgetUtils.set_combo_style(type_combo)
            layout.addRow("设置类型:", type_combo)
            
            # 设置描述
            desc_edit = QLineEdit(setting.description)
            WidgetUtils.set_input_style(desc_edit)
            layout.addRow("设置描述:", desc_edit)
            
            # 按钮布局
            button_layout = QHBoxLayout()
            save_btn = QPushButton("保存")
            save_btn.setObjectName("primaryButton")
            save_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(save_btn)
            
            cancel_btn = QPushButton("取消")
            cancel_btn.setObjectName("secondaryButton")
            cancel_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(save_btn)
            button_layout.addWidget(cancel_btn)
            
            layout.addRow("", button_layout)
            
            # 显示对话框
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 更新设置
                setting.name = name_edit.text()
                setting.value = value_edit.text()
                setting.type = type_combo.currentText()
                setting.description = desc_edit.text()
                
                # 保存到数据库
                with self.db_manager.get_session() as session:
                    session.merge(setting)
                    session.commit()
                    
                # 刷新表格
                self.load_data()
                
                self.error_handler.handle_info("保存设置成功", self, "成功")
                
        except Exception as e:
            self.error_handler.handle_error(e, self, "编辑设置失败")
            
    def load_settings(self):
        """加载设置"""
        try:
            # 从数据库加载设置
            with self.db_manager.get_session() as session:
                settings = session.query(Settings).first()
                if settings:
                    # 企业信息
                    self.corp_name.setText(settings.corp_name)
                    self.corp_id.setText(settings.corp_id)
                    self.corp_secret.setText(settings.corp_secret)
                    self.agent_id.setText(settings.agent_id)
                    self.corp_status.setChecked(settings.corp_status)
                    
                    # 用户管理
                    self.default_role.setCurrentText({
                        "超级管理员": "超级管理员",
                        "企业管理员": "企业管理员",
                        "普通用户": "普通用户"
                    }.get(settings.default_role, "普通用户"))
                    self.user_status.setChecked(settings.user_status)
                    self.password_policy.setCurrentText({
                        "simple": "简单",
                        "medium": "中等",
                        "complex": "复杂"
                    }.get(settings.password_policy, "中等"))
                    self.password_expire.setValue(settings.password_expire)
                    self.login_fail_limit.setValue(settings.login_fail_limit)
                    
                    # 系统设置
                    theme_map = {
                        "system": "跟随系统",
                        "light": "明亮",
                        "dark": "暗色"
                    }
                    self.theme.setCurrentText(theme_map.get(settings.theme, "跟随系统"))
                    self.db_path.setText(settings.db_path)
                    self.log_path.setText(settings.log_path)
                    self.log_level.setCurrentText(settings.log_level)
                    self.log_retention.setValue(settings.log_retention)
                    
                    # 数据管理
                    self.data_cleanup.setChecked(settings.data_cleanup)
                    self.cleanup_period.setValue(settings.cleanup_days)
                    self.cleanup_scope.setCurrentText({
                        "all": "全部数据",
                        "sign": "仅签到记录",
                        "log": "仅日志记录"
                    }.get(settings.cleanup_scope, "全部数据"))
                    
        except Exception as e:
            self.error_handler.handle_error(e, self, "加载设置失败")
            
    def save_settings(self):
        """保存设置"""
        try:
            if not self._validate_settings():
                return
                
            # 保存所有设置
            self._save_system_settings()  # 保存系统设置
            self._save_corp_settings()    # 保存企业信息
            self._save_user_settings()    # 保存用户管理
            
            self.error_handler.handle_info("保存设置成功", self, "成功")
            
        except Exception as e:
            self.error_handler.handle_error(e, self, "保存设置失败")
            
    def _save_corp_settings(self):
        """保存企业信息设置"""
        try:
            with self.db_manager.get_session() as session:
                # 获取表格中的所有企业数据
                for row in range(self.corp_table.rowCount()):
                    corp_name = self.corp_table.item(row, 0).text()
                    corp_id = self.corp_table.item(row, 1).text()
                    agent_id = self.corp_table.item(row, 3).text()
                    status = self.corp_table.item(row, 4).text() == '启用'
                    
                    # 获取或创建企业对象
                    corp = session.query(Corporation).filter_by(name=corp_name).first()
                    if not corp:
                        corp = Corporation(name=corp_name)
                        session.add(corp)
                    
                    # 更新企业信息
                    corp.corp_id = corp_id
                    corp.agent_id = agent_id
                    corp.status = status
                    
                session.commit()
                
        except Exception as e:
            raise Exception(f"保存企业信息失败: {str(e)}")

    def _save_user_settings(self):
        """保存用户管理设置"""
        try:
            with self.db_manager.get_session() as session:
                # 获取表格中的所有用户数据
                for row in range(self.user_table.rowCount()):
                    login_name = self.user_table.item(row, 0).text()
                    name = self.user_table.item(row, 1).text()
                    role = self.user_table.item(row, 2).text()
                    corp_name = self.user_table.item(row, 3).text()
                    is_admin = self.user_table.item(row, 4).text() == '是'
                    is_active = self.user_table.item(row, 5).text() == '启用'
                    wecom_code = self.user_table.item(row, 6).text()
                    
                    # 获取用户对象
                    user = session.query(User).filter_by(login_name=login_name).first()
                    if not user:
                        continue  # 跳过不存在的用户
                    
                    # 跳过root-admin用户的修改
                    if user.role == UserRole.ROOT_ADMIN.value:
                        continue
                    
                    # 根据是否管理员设置角色
                    if is_admin:
                        user_role = UserRole.WECOM_ADMIN.value
                    else:
                        user_role = UserRole.NORMAL.value
                    
                    # 获取关联企业信息
                    corp = session.query(Corporation).filter_by(name=corp_name).first()
                    if not corp and user_role != UserRole.ROOT_ADMIN.value:
                        continue  # 非root-admin用户必须关联企业
                    
                    # 更新用户信息
                    user.name = name
                    user.role = user_role  # 使用根据is_admin计算的角色
                    user.is_admin = is_admin
                    user.is_active = is_active
                    user.wecom_code = wecom_code if wecom_code != login_name else None
                    
                    # 更新企业关联信息
                    if corp and user_role != UserRole.ROOT_ADMIN.value:
                        user.corpname = corp.name
                        user.corpid = corp.corp_id
                        user.corpsecret = corp.corp_secret
                        user.agentid = corp.agent_id
                    else:
                        user.corpname = None
                        user.corpid = None
                        user.corpsecret = None
                        user.agentid = None
                    
                session.commit()
                
        except Exception as e:
            raise Exception(f"保存用户管理设置失败: {str(e)}")
            
    def reset_settings(self):
        """重置设置"""
        try:
            # 确认重置
            if not ErrorHandler.handle_question(
                "确定要重置所有设置吗？",
                self,
                "确认重置"
            ):
                return
                
            # 重置所有输入框
            self.corp_name.clear()
            self.corp_id.clear()
            self.corp_secret.clear()
            self.agent_id.clear()
            self.corp_status.setChecked(True)
            self.default_role.setCurrentIndex(0)
            self.user_status.setChecked(True)
            self.password_policy.setCurrentIndex(1)
            self.password_expire.setValue(90)
            self.login_fail_limit.setValue(5)
            self.theme.setCurrentIndex(0)
            self.db_path.clear()
            self.log_path.clear()
            self.log_level.setCurrentText(1)
            self.log_retention.setValue(30)
            self.data_cleanup.setChecked(True)
            self.cleanup_period.setValue(30)
            self.cleanup_scope.setCurrentIndex(0)
            
            ErrorHandler.handle_info("重置设置成功", self, "成功")
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "重置设置失败")
            
    def browse_db_path(self):
        """浏览数据库路径"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "选择数据库文件",
                "",
                "SQLite Files (*.db)"
            )
            if file_path:
                self.db_path.setText(file_path)
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "选择数据库路径失败")
            
    def browse_log_path(self):
        """浏览日志路径"""
        try:
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "选择日志目录"
            )
            if dir_path:
                self.log_path.setText(dir_path)
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "选择日志路径失败")
            
    def browse_backup_path(self):
        """浏览备份文件路径"""
        try:
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "选择备份文件目录"
            )
            if dir_path:
                self.backup_path.setText(dir_path)
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "选择备份文件路径失败")
            
    def cleanup_data(self):
        """清理数据"""
        try:
            # 确认清理
            if not ErrorHandler.handle_question(
                "确定要清理数据吗？此操作不可恢复！",
                self,
                "确认清理"
            ):
                return
                
            # 获取清理范围
            scope = self.cleanup_scope.currentText()
            
            # 执行清理
            with self.db_manager.get_session() as session:
                if scope == "全部数据" or scope == "仅签到记录":
                    # 清理签到记录
                    session.query(SignRecord).delete()
                    
                if scope == "全部数据" or scope == "仅日志记录":
                    # 清理日志文件
                    log_path = self.log_path.text()
                    if os.path.exists(log_path):
                        for file in os.listdir(log_path):
                            if file.endswith(".log"):
                                file_path = os.path.join(log_path, file)
                                try:
                                    os.remove(file_path)
                                except Exception as e:
                                    logger.error(f"删除日志文件失败: {str(e)}")
                                    
            ErrorHandler.handle_info("清理数据成功", self, "成功")
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "清理数据失败")
            
    def _validate_settings(self) -> bool:
        """验证设置
        
        Returns:
            是否验证通过
        """
        # 验证企业信息
        if not self.corp_name.text():
            ErrorHandler.handle_warning("请输入企业名称", self)
            return False
            
        if not self.corp_id.text():
            ErrorHandler.handle_warning("请输入企业ID", self)
            return False
            
        if not self.corp_secret.text():
            ErrorHandler.handle_warning("请输入企业应用Secret", self)
            return False
            
        if not self.agent_id.text():
            ErrorHandler.handle_warning("请输入应用ID", self)
            return False
            
        # 验证路径
        if not self.db_path.text():
            ErrorHandler.handle_warning("请选择数据库路径", self)
            return False
            
        if not self.log_path.text():
            ErrorHandler.handle_warning("请选择日志路径", self)
            return False
            
        return True

    def add_corp(self):
        """添加新企业"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新增企业")
        dialog.setModal(True)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 企业名称
        corp_name = QLineEdit()
        corp_name.setFixedWidth(300)
        layout.addRow("企业名称:", corp_name)
        
        # 企业ID
        corp_id = QLineEdit()
        corp_id.setFixedWidth(300)
        layout.addRow("企业ID:", corp_id)
        
        # 应用Secret
        corp_secret = QLineEdit()
        corp_secret.setFixedWidth(300)
        corp_secret.setEchoMode(QLineEdit.Password)
        layout.addRow("应用Secret:", corp_secret)
        
        # 应用ID
        agent_id = QLineEdit()
        agent_id.setFixedWidth(300)
        layout.addRow("应用ID:", agent_id)
        
        # 企业状态
        status = QCheckBox("启用")
        status.setChecked(True)
        layout.addRow("企业状态:", status)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow("", btn_layout)
        
        if dialog.exec() == QDialog.Accepted:
            try:
                with self.db_manager.get_session() as session:
                    # 检查企业名称是否重复
                    if session.query(Corporation).filter_by(name=corp_name.text()).first():
                        self.error_handler.handle_warning("企业名称已存在", self)
                        return
                    
                    # 创建新企业
                    corp = Corporation(
                        name=corp_name.text(),
                        corp_id=corp_id.text(),
                        corp_secret=corp_secret.text(),
                        agent_id=agent_id.text(),
                        status=status.isChecked()
                    )
                    session.add(corp)
                    session.commit()
                    
                    self.error_handler.handle_info("添加企业成功", self)
                    self.load_data()  # 刷新数据
                    
            except Exception as e:
                self.error_handler.handle_error(e, self, "添加企业失败")
                
    def add_user(self):
        """添加新用户"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新增用户")
        dialog.setModal(True)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 登录名
        login_name = QLineEdit()
        login_name.setFixedWidth(300)
        layout.addRow("登录名:", login_name)
        
        # 用户名
        name = QLineEdit()
        name.setFixedWidth(300)
        layout.addRow("用户名:", name)
        
        # 密码
        password = QLineEdit()
        password.setFixedWidth(300)
        password.setEchoMode(QLineEdit.Password)
        layout.addRow("密码:", password)
        
        # 确认密码
        confirm_password = QLineEdit()
        confirm_password.setFixedWidth(300)
        confirm_password.setEchoMode(QLineEdit.Password)
        layout.addRow("确认密码:", confirm_password)
        
        # 企业选择
        corp_combo = QComboBox()
        corp_combo.setFixedWidth(300)
        layout.addRow("关联企业:", corp_combo)
        
        # 加载企业列表
        try:
            with self.db_manager.get_session() as session:
                corps = session.query(Corporation).filter_by(status=True).all()
                corp_combo.addItems([corp.name for corp in corps])
        except Exception as e:
            self.error_handler.handle_error(e, self, "加载企业列表失败")
        
        # 是否管理员
        is_admin = QCheckBox("是")
        layout.addRow("是否管理员:", is_admin)
        
        # 状态
        status = QCheckBox("启用")
        status.setChecked(True)
        layout.addRow("状态:", status)
        
        # 企业微信账号
        wecom_code = QLineEdit()
        wecom_code.setFixedWidth(300)
        layout.addRow("企业微信账号:", wecom_code)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow("", btn_layout)
        
        if dialog.exec() == QDialog.Accepted:
            try:
                # 验证密码
                if password.text() != confirm_password.text():
                    self.error_handler.handle_warning("两次输入的密码不一致", self)
                    return
                    
                if not password.text():
                    self.error_handler.handle_warning("请输入密码", self)
                    return
                    
                with self.db_manager.get_session() as session:
                    # 检查用户名是否重复
                    if session.query(User).filter_by(login_name=login_name.text()).first():
                        self.error_handler.handle_warning("登录名已存在", self)
                        return
                    
                    # 获取关联企业信息
                    corp = session.query(Corporation).filter_by(name=corp_combo.currentText()).first()
                    if not corp:
                        self.error_handler.handle_warning("请选择关联企业", self)
                        return
                    
                    # 根据是否管理员设置角色
                    user_role = UserRole.WECOM_ADMIN.value if is_admin.isChecked() else UserRole.NORMAL.value
                    
                    # 创建新用户
                    user = User(
                        login_name=login_name.text(),
                        name=name.text(),
                        role=user_role,
                        is_admin=is_admin.isChecked(),
                        is_active=status.isChecked(),
                        wecom_code=wecom_code.text() or None,
                        corpname=corp.name,
                        corpid=corp.corp_id,
                        corpsecret=corp.corp_secret,
                        agentid=corp.agent_id
                    )
                    
                    # 设置密码
                    user.set_password(password.text())
                    
                    session.add(user)
                    session.commit()
                    
                    self.error_handler.handle_info("添加用户成功", self)
                    self.load_data()  # 刷新数据
                    
            except Exception as e:
                self.error_handler.handle_error(e, self, "添加用户失败")
                
    def edit_corp(self, corp: Corporation):
        """编辑企业信息
        
        Args:
            corp: 企业对象
        """
        try:
            with self.db_manager.get_session() as session:
                # 获取企业对象
                corp = session.merge(corp)
                
                dialog = QDialog(self)
                dialog.setWindowTitle("编辑企业")
                dialog.setModal(True)
                
                layout = QFormLayout(dialog)
                layout.setSpacing(15)
                layout.setContentsMargins(20, 20, 20, 20)
                
                # 企业名称
                corp_name = QLineEdit(corp.name)
                corp_name.setFixedWidth(300)
                layout.addRow("企业名称:", corp_name)
                
                # 企业ID
                corp_id = QLineEdit(corp.corp_id)
                corp_id.setFixedWidth(300)
                layout.addRow("企业ID:", corp_id)
                
                # 应用Secret
                corp_secret = QLineEdit(corp.corp_secret)
                corp_secret.setFixedWidth(300)
                corp_secret.setEchoMode(QLineEdit.Password)
                layout.addRow("应用Secret:", corp_secret)
                
                # 应用ID
                agent_id = QLineEdit(corp.agent_id)
                agent_id.setFixedWidth(300)
                layout.addRow("应用ID:", agent_id)
                
                # 企业状态
                status = QCheckBox("启用")
                status.setChecked(corp.status)
                layout.addRow("企业状态:", status)
                
                # 按钮
                btn_layout = QHBoxLayout()
                save_btn = QPushButton("保存")
                save_btn.setObjectName("primaryButton")
                save_btn.clicked.connect(dialog.accept)
                cancel_btn = QPushButton("取消")
                cancel_btn.clicked.connect(dialog.reject)
                btn_layout.addWidget(save_btn)
                btn_layout.addWidget(cancel_btn)
                layout.addRow("", btn_layout)
                
                if dialog.exec() == QDialog.Accepted:
                    # 检查企业名称是否重复
                    if corp_name.text() != corp.name and \
                            session.query(Corporation).filter_by(name=corp_name.text()).first():
                        self.error_handler.handle_warning("企业名称已存在", self)
                        return
                    
                    # 更新企业信息
                    corp.name = corp_name.text()
                    corp.corp_id = corp_id.text()
                    corp.corp_secret = corp_secret.text()
                    corp.agent_id = agent_id.text()
                    corp.status = status.isChecked()
                    
                    session.commit()
                    
                    self.error_handler.handle_info("更新企业成功", self)
                    self.load_data()  # 刷新数据
                    
        except Exception as e:
            self.error_handler.handle_error(e, self, "更新企业失败")
                
    def delete_corp(self, corp: Corporation):
        """删除企业
        
        Args:
            corp: 企业对象
        """
        try:
            # 创建确认对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("删除确认")
            dialog.setModal(True)
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 警告图标和文字
            warning_layout = QHBoxLayout()
            warning_icon = QLabel("[X]")
            warning_icon.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")
            warning_layout.addWidget(warning_icon)
            
            warning_text = QLabel(f'您确定要删除企业 "{corp.name}" 吗？\n此操作不可恢复，请谨慎操作！')
            warning_text.setWordWrap(True)
            warning_layout.addWidget(warning_text)
            layout.addLayout(warning_layout)
            
            # 分隔线
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            layout.addWidget(line)
            
            # 按钮
            btn_layout = QHBoxLayout()
            delete_btn = QPushButton("确认删除")
            delete_btn.setObjectName("dangerButton")
            delete_btn.clicked.connect(dialog.accept)
            
            cancel_btn = QPushButton("取消")
            cancel_btn.setObjectName("secondaryButton")
            cancel_btn.clicked.connect(dialog.reject)
            
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(delete_btn)
            layout.addLayout(btn_layout)
            
            if dialog.exec() == QDialog.Accepted:
                with self.db_manager.get_session() as session:
                    session.delete(corp)
                    session.commit()
                    
                    self.error_handler.handle_info("删除企业成功", self)
                    self.load_data()  # 刷新数据
                    
        except Exception as e:
            self.error_handler.handle_error(e, self, "删除企业失败")
            
    def edit_user(self, login_name: str):
        """编辑用户
        
        Args:
            login_name: 用户登录名
        """
        try:
            with self.db_manager.get_session() as session:
                # 获取用户对象
                user = session.query(User).filter_by(login_name=login_name).first()
                if not user:
                    self.error_handler.handle_warning("用户不存在", self)
                    return
                    
                dialog = QDialog(self)
                dialog.setWindowTitle("编辑用户")
                dialog.setModal(True)
                
                layout = QFormLayout(dialog)
                layout.setSpacing(15)
                layout.setContentsMargins(20, 20, 20, 20)
                
                # 登录名
                login_name_edit = QLineEdit(user.login_name)
                login_name_edit.setFixedWidth(300)
                layout.addRow("登录名:", login_name_edit)
                
                # 用户名
                name = QLineEdit(user.name)
                name.setFixedWidth(300)
                layout.addRow("用户名:", name)
                
                # 企业选择
                corp_combo = QComboBox()
                corp_combo.setFixedWidth(300)
                layout.addRow("关联企业:", corp_combo)
                
                # 加载企业列表
                corps = session.query(Corporation).filter_by(status=True).all()
                corp_combo.addItems([corp.name for corp in corps])
                if user.corpname:
                    corp_combo.setCurrentText(user.corpname)
                
                # 是否管理员
                is_admin = QCheckBox("是")
                is_admin.setChecked(user.is_admin)
                layout.addRow("是否管理员:", is_admin)
                
                # 状态
                status = QCheckBox("启用")
                status.setChecked(user.is_active)
                layout.addRow("状态:", status)
                
                # 企业微信账号
                wecom_code = QLineEdit(user.wecom_code or '')
                wecom_code.setFixedWidth(300)
                layout.addRow("企业微信账号:", wecom_code)
                
                # 按钮
                btn_layout = QHBoxLayout()
                save_btn = QPushButton("保存")
                save_btn.setObjectName("primaryButton")
                save_btn.clicked.connect(dialog.accept)
                cancel_btn = QPushButton("取消")
                cancel_btn.clicked.connect(dialog.reject)
                btn_layout.addWidget(save_btn)
                btn_layout.addWidget(cancel_btn)
                layout.addRow("", btn_layout)
                
                if dialog.exec() == QDialog.Accepted:
                    # 检查用户名是否重复
                    if login_name_edit.text() != user.login_name and \
                            session.query(User).filter_by(login_name=login_name_edit.text()).first():
                        self.error_handler.handle_warning("登录名已存在", self)
                        return
                    
                    # 获取关联企业信息
                    corp = session.query(Corporation).filter_by(name=corp_combo.currentText()).first()
                    if not corp:
                        self.error_handler.handle_warning("请选择关联企业", self)
                        return
                    
                    # 根据是否管理员设置角色
                    user_role = UserRole.WECOM_ADMIN.value if is_admin.isChecked() else UserRole.NORMAL.value
                    
                    # 更新用户信息
                    user.login_name = login_name_edit.text()
                    user.name = name.text()
                    user.role = user_role
                    user.is_admin = is_admin.isChecked()
                    user.is_active = status.isChecked()
                    user.wecom_code = wecom_code.text() or None
                    user.corpname = corp.name
                    user.corpid = corp.corp_id
                    user.corpsecret = corp.corp_secret
                    user.agentid = corp.agent_id
                    
                    session.commit()
                    
                    self.error_handler.handle_info("更新用户成功", self)
                    self.load_data()  # 刷新数据
                    
        except Exception as e:
            self.error_handler.handle_error(e, self, "更新用户失败")
            
    def reset_user_password(self, login_name: str):
        """重置用户密码
        
        Args:
            login_name: 用户登录名
        """
        try:
            with self.db_manager.get_session() as session:
                # 获取用户对象
                user = session.query(User).filter_by(login_name=login_name).first()
                if not user:
                    self.error_handler.handle_warning("用户不存在", self)
                    return
                    
                # 创建重置密码对话框
                dialog = QDialog(self)
                dialog.setWindowTitle("重置密码")
                dialog.setModal(True)
                
                layout = QFormLayout(dialog)
                layout.setSpacing(15)
                layout.setContentsMargins(20, 20, 20, 20)
                
                # 新密码
                new_password = QLineEdit()
                new_password.setFixedWidth(300)
                new_password.setEchoMode(QLineEdit.Password)
                layout.addRow("新密码:", new_password)
                
                # 确认新密码
                confirm_password = QLineEdit()
                confirm_password.setFixedWidth(300)
                confirm_password.setEchoMode(QLineEdit.Password)
                layout.addRow("确认新密码:", confirm_password)
                
                # 按钮
                btn_layout = QHBoxLayout()
                save_btn = QPushButton("保存")
                save_btn.setObjectName("primaryButton")
                save_btn.clicked.connect(dialog.accept)
                cancel_btn = QPushButton("取消")
                cancel_btn.clicked.connect(dialog.reject)
                btn_layout.addWidget(save_btn)
                btn_layout.addWidget(cancel_btn)
                layout.addRow("", btn_layout)
                
                if dialog.exec() == QDialog.Accepted:
                    # 验证密码
                    if new_password.text() != confirm_password.text():
                        self.error_handler.handle_warning("两次输入的密码不一致", self)
                        return
                        
                    if not new_password.text():
                        self.error_handler.handle_warning("请输入新密码", self)
                        return
                        
                    # 更新密码
                    user.set_password(new_password.text())
                    session.commit()
                    
                    self.error_handler.handle_info("重置密码成功", self)
                    
        except Exception as e:
            self.error_handler.handle_error(e, self, "重置密码失败")
            
    def delete_user(self, login_name: str):
        """删除用户
        
        Args:
            login_name: 用户登录名
        """
        try:
            with self.db_manager.get_session() as session:
                # 获取用户对象
                user = session.query(User).filter_by(login_name=login_name).first()
                if not user:
                    self.error_handler.handle_warning("用户不存在", self)
                    return
                    
                # 创建确认对话框
                dialog = QDialog(self)
                dialog.setWindowTitle("删除确认")
                dialog.setModal(True)
                
                layout = QVBoxLayout(dialog)
                layout.setSpacing(15)
                layout.setContentsMargins(20, 20, 20, 20)
                
                # 警告图标和文字
                warning_layout = QHBoxLayout()
                warning_icon = QLabel("[X]")
                warning_icon.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")
                warning_layout.addWidget(warning_icon)
                
                warning_text = QLabel(f'您确定要删除用户 "{user.name}({user.login_name})" 吗？\n此操作不可恢复，请谨慎操作！')
                warning_text.setWordWrap(True)
                warning_layout.addWidget(warning_text)
                layout.addLayout(warning_layout)
                
                # 分隔线
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                layout.addWidget(line)
                
                # 按钮
                btn_layout = QHBoxLayout()
                delete_btn = QPushButton("确认删除")
                delete_btn.setObjectName("dangerButton")
                delete_btn.clicked.connect(dialog.accept)
                
                cancel_btn = QPushButton("取消")
                cancel_btn.setObjectName("secondaryButton")
                cancel_btn.clicked.connect(dialog.reject)
                
                btn_layout.addWidget(cancel_btn)
                btn_layout.addWidget(delete_btn)
                layout.addLayout(btn_layout)
                
                if dialog.exec() == QDialog.Accepted:
                    session.delete(user)
                    session.commit()
                    
                    self.error_handler.handle_info("删除用户成功", self)
                    self.load_data()  # 刷新数据
                    
        except Exception as e:
            self.error_handler.handle_error(e, self, "删除用户失败")

    def show_init_wizard(self):
        """显示初始化配置向导"""
        try:
            # 创建确认对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("重新初始化确认")
            dialog.setModal(True)
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 警告图标和文字
            warning_layout = QHBoxLayout()
            warning_icon = QLabel("[X]")
            warning_icon.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")
            warning_layout.addWidget(warning_icon)
            
            warning_text = QLabel("您确定要重新初始化系统吗？\n此操作将重新配置系统的基本设置，请谨慎操作！")
            warning_text.setWordWrap(True)
            warning_layout.addWidget(warning_text)
            layout.addLayout(warning_layout)
            
            # 分隔线
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            layout.addWidget(line)
            
            # 按钮
            btn_layout = QHBoxLayout()
            confirm_btn = QPushButton("确认重新初始化")
            confirm_btn.setObjectName("dangerButton")
            confirm_btn.clicked.connect(dialog.accept)
            
            cancel_btn = QPushButton("取消")
            cancel_btn.setObjectName("secondaryButton")
            cancel_btn.clicked.connect(dialog.reject)
            
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(confirm_btn)
            layout.addLayout(btn_layout)
            
            if dialog.exec() == QDialog.Accepted:
                # 显示初始化向导
                wizard = InitWizard(self.db_manager)
                if wizard.exec() == QDialog.Accepted:
                    self.error_handler.handle_info("系统重新初始化成功", self)
                    self.load_data()  # 刷新数据
                
        except Exception as e:
            self.error_handler.handle_error(e, self, "显示初始化向导失败")

    def _load_system_settings(self):
        """加载系统设置
        优先级：数据库 > 用户自定义配置 > 系统默认配置
        """
        try:
            # 1. 首先尝试从数据库获取配置
            with self.db_manager.get_session() as session:
                settings = session.query(Settings).first()
                if settings:
                    logger.info("从数据库加载系统设置")
                    # 主题设置
                    theme_map = {"light": "浅色", "dark": "深色", "system": "跟随系统"}
                    current_theme = settings.theme or "system"
                    self.theme_combo.setCurrentText(theme_map.get(current_theme, "跟随系统"))
                    
                    # 数据库路径
                    if settings.db_path:
                        self.db_path.setText(settings.db_path)
                    
                    # 备份文件路径
                    if settings.backup_path:
                        self.backup_path.setText(settings.backup_path)
                    
                    # 日志设置
                    if settings.log_path:
                        self.log_path.setText(settings.log_path)
                    if settings.log_level:
                        self.log_level.setCurrentText(settings.log_level)
                    
                    # 数据管理设置
                    self.data_cleanup.setChecked(settings.data_cleanup)
                    if settings.cleanup_days:
                        self.cleanup_period.setValue(settings.cleanup_days)
                    
                    cleanup_scope_map = {
                        "all": "全部数据",
                        "logs": "仅日志",
                        "temp": "仅临时文件"
                    }
                    if settings.cleanup_scope:
                        self.cleanup_scope.setCurrentText(
                            cleanup_scope_map.get(settings.cleanup_scope, "全部数据")
                        )
                    return

            # 2. 如果数据库中没有，尝试从用户配置文件获取
            logger.info("从用户配置文件加载系统设置")
            config = self.config_manager.get_config()
            if config and "system" in config:
                system_config = config["system"]
                
                # 主题设置
                theme_map = {"light": "浅色", "dark": "深色", "system": "跟随系统"}
                current_theme = system_config.get("theme", "system")
                self.theme_combo.setCurrentText(theme_map.get(current_theme, "跟随系统"))
                
                # 数据库路径
                if "database" in config and "path" in config["database"]:
                    self.db_path.setText(config["database"]["path"])
                
                # 备份文件路径
                if "backup_path" in system_config:
                    self.backup_path.setText(system_config["backup_path"])
                
                # 日志设置
                if "log_path" in system_config:
                    self.log_path.setText(system_config["log_path"])
                if "log_level" in system_config:
                    self.log_level.setCurrentText(system_config["log_level"])
                
                # 数据管理设置
                self.data_cleanup.setChecked(system_config.get("auto_cleanup", True))
                self.cleanup_period.setValue(system_config.get("cleanup_days", 30))
                
                cleanup_scope_map = {
                    "all": "全部数据",
                    "logs": "仅日志",
                    "temp": "仅临时文件"
                }
                cleanup_scope = system_config.get("cleanup_scope", "all")
                self.cleanup_scope.setCurrentText(
                    cleanup_scope_map.get(cleanup_scope, "全部数据")
                )
                return

            # 3. 如果用户配置也没有，使用系统默认配置
            logger.info("使用系统默认配置")
            self.theme_combo.setCurrentText("跟随系统")
            self.db_path.setText(os.path.join(self.config_manager.config_dir, "data", "data.db"))
            self.backup_path.setText(os.path.join(self.config_manager.config_dir, "backups"))
            self.log_path.setText(os.path.join(self.config_manager.config_dir, "logs"))
            self.log_level.setCurrentText("INFO")
            self.data_cleanup.setChecked(True)
            self.cleanup_period.setValue(30)
            self.cleanup_scope.setCurrentText("全部数据")

        except Exception as e:
            logger.error(f"加载系统设置失败: {str(e)}")
            ErrorHandler.handle_error(f"加载系统设置失败: {str(e)}", self)

    def _save_system_settings(self):
        """保存系统设置"""
        try:
            with self.db_manager.get_session() as session:
                # 获取或创建设置对象
                settings = session.query(Settings).first()
                if not settings:
                    settings = Settings()
                    session.add(settings)
                
                # 获取旧的路径配置
                old_db_path = settings.db_path
                old_backup_path = settings.backup_path
                old_log_path = settings.log_path
                
                # 主题设置
                theme_map = {
                    "跟随系统": "system",
                    "明亮": "light",
                    "暗色": "dark"
                }
                settings.theme = theme_map.get(self.theme_combo.currentText(), "system")
                
                # 路径设置
                settings.db_path = self.db_path.text()
                settings.backup_path = self.backup_path.text()
                settings.log_path = self.log_path.text()
                
                # 日志设置
                settings.log_level = self.log_level.currentText()
                
                # 数据管理设置
                settings.data_cleanup = self.data_cleanup.isChecked()
                settings.cleanup_days = self.cleanup_period.value()
                
                cleanup_scope_map = {
                    "全部数据": "all",
                    "仅日志": "logs",
                    "仅临时文件": "temp"
                }
                settings.cleanup_scope = cleanup_scope_map.get(
                    self.cleanup_scope.currentText(), "all"
                )
                
                # 迁移文件
                try:
                    # 创建新的目录
                    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
                    os.makedirs(settings.backup_path, exist_ok=True)
                    os.makedirs(settings.log_path, exist_ok=True)
                    
                    # 迁移数据库文件
                    if old_db_path and os.path.exists(old_db_path) and old_db_path != settings.db_path:
                        shutil.copy2(old_db_path, settings.db_path)
                        logger.info(f"数据库文件已从 {old_db_path} 迁移到 {settings.db_path}")
                    
                    # 迁移备份文件
                    if old_backup_path and os.path.exists(old_backup_path) and old_backup_path != settings.backup_path:
                        for item in os.listdir(old_backup_path):
                            s = os.path.join(old_backup_path, item)
                            d = os.path.join(settings.backup_path, item)
                            if os.path.isfile(s):
                                shutil.copy2(s, d)
                            else:
                                shutil.copytree(s, d, dirs_exist_ok=True)
                        logger.info(f"备份文件已从 {old_backup_path} 迁移到 {settings.backup_path}")
                    
                    # 迁移日志文件
                    if old_log_path and os.path.exists(old_log_path) and old_log_path != settings.log_path:
                        for item in os.listdir(old_log_path):
                            if item.endswith('.log'):
                                s = os.path.join(old_log_path, item)
                                d = os.path.join(settings.log_path, item)
                                shutil.copy2(s, d)
                        logger.info(f"日志文件已从 {old_log_path} 迁移到 {settings.log_path}")
                    
                except Exception as e:
                    logger.error(f"文件迁移失败: {str(e)}")
                    raise Exception(f"文件迁移失败: {str(e)}")
                
                session.commit()
                
                # 更新配置文件
                # 1. 获取当前配置
                config = self.config_manager.get_config()
                if not config:
                    config = {}
                
                # 2. 更新系统配置
                if "system" not in config:
                    config["system"] = {}
                
                # 只更新用户相关的配置项
                config["system"].update({
                    "theme": settings.theme,
                    "log_level": settings.log_level,
                    "log_retention": 30,  # 默认值
                    "backup_retention": 30,  # 默认值
                    "auto_cleanup": settings.data_cleanup,
                    "cleanup_days": settings.cleanup_days
                })
                
                # 3. 更新路径配置
                if "paths" not in config:
                    config["paths"] = {}
                
                config["paths"].update({
                    "data": settings.db_path,
                    "log": settings.log_path,
                    "backup": settings.backup_path
                })
                
                # 4. 更新数据库配置
                if "database" not in config:
                    config["database"] = {}
                
                config["database"].update({
                    "path": settings.db_path,
                    "backup_path": settings.backup_path
                })
                
                # 5. 保存配置
                self.config_manager.save_config(config)
                
                # 6. 询问是否删除旧文件
                if any([
                    old_db_path and os.path.exists(old_db_path) and old_db_path != settings.db_path,
                    old_backup_path and os.path.exists(old_backup_path) and old_backup_path != settings.backup_path,
                    old_log_path and os.path.exists(old_log_path) and old_log_path != settings.log_path
                ]):
                    if ErrorHandler.handle_question(
                        "文件已迁移到新位置，是否删除旧文件？",
                        self,
                        "删除确认"
                    ):
                        try:
                            # 删除旧文件
                            if old_db_path and os.path.exists(old_db_path) and old_db_path != settings.db_path:
                                os.remove(old_db_path)
                            
                            if old_backup_path and os.path.exists(old_backup_path) and old_backup_path != settings.backup_path:
                                shutil.rmtree(old_backup_path)
                            
                            if old_log_path and os.path.exists(old_log_path) and old_log_path != settings.log_path:
                                shutil.rmtree(old_log_path)
                                
                            logger.info("旧文件已删除")
                            
                        except Exception as e:
                            logger.error(f"删除旧文件失败: {str(e)}")
                            ErrorHandler.handle_error(f"删除旧文件失败: {str(e)}", self)
                
        except Exception as e:
            raise Exception(f"保存系统设置失败: {str(e)}")