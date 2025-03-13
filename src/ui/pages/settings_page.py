from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QCheckBox, QSpinBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from ..managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.core.auth_manager import AuthManager
from src.core.database import DatabaseManager
from src.models.user import UserRole
from src.models.settings import Settings
from ..components.dialogs.io_dialog import IODialog
import pandas as pd
import os

logger = get_logger(__name__)

class SettingsPage(QWidget):
    """设置页面"""
    
    def __init__(self, auth_manager: AuthManager, db_manager: DatabaseManager):
        super().__init__()
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("settingsPage")
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 创建工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # 创建搜索区域
        search_group = self._create_search_group()
        layout.addWidget(search_group)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "设置ID", "设置名称", "设置值", "设置类型",
            "设置描述", "更新时间", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        WidgetUtils.set_table_style(self.table)
        layout.addWidget(self.table)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_main_style())
        
        # 添加淡入动画
        AnimationManager.fade_in(self)
        
        # 加载数据
        self.load_data()
        
        # 根据用户权限控制UI
        self._update_ui_by_permission()
        
    def _update_ui_by_permission(self):
        """根据用户权限更新UI"""
        try:
            current_user = self.auth_manager.get_current_user()
            if not current_user:
                return
                
            # 超级管理员可以访问所有设置
            if current_user.role == UserRole.ROOT_ADMIN:
                return
                
            # 企业管理员可以访问企业信息和用户管理设置
            if current_user.role == UserRole.CORP_ADMIN:
                # 禁用系统设置和数据管理
                self.system_group.setEnabled(False)
                self.data_group.setEnabled(False)
                
            # 普通用户只能查看企业信息
            if current_user.role == UserRole.USER:
                # 禁用所有设置组
                self.corp_group.setEnabled(False)
                self.user_group.setEnabled(False)
                self.system_group.setEnabled(False)
                self.data_group.setEnabled(False)
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "更新UI权限失败")
            
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
        layout.setSpacing(10)
        
        # 企业名称
        self.corp_name = QLineEdit()
        WidgetUtils.set_input_style(self.corp_name)
        layout.addRow("企业名称:", self.corp_name)
        
        # 企业ID
        self.corp_id = QLineEdit()
        WidgetUtils.set_input_style(self.corp_id)
        layout.addRow("企业ID:", self.corp_id)
        
        # 企业应用Secret
        self.corp_secret = QLineEdit()
        self.corp_secret.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.corp_secret)
        layout.addRow("企业应用Secret:", self.corp_secret)
        
        # 应用ID
        self.agent_id = QLineEdit()
        WidgetUtils.set_input_style(self.agent_id)
        layout.addRow("应用ID:", self.agent_id)
        
        # 企业状态
        self.corp_status = QCheckBox("启用")
        self.corp_status.setChecked(True)
        layout.addRow("企业状态:", self.corp_status)
        
        return group
        
    def _create_user_group(self) -> QGroupBox:
        """创建用户管理设置组"""
        group = QGroupBox("用户管理设置")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        
        # 默认用户角色
        self.default_role = QComboBox()
        self.default_role.addItems(["超级管理员", "企业管理员", "普通用户"])
        WidgetUtils.set_combo_style(self.default_role)
        layout.addRow("默认用户角色:", self.default_role)
        
        # 用户状态
        self.user_status = QCheckBox("默认启用")
        self.user_status.setChecked(True)
        layout.addRow("用户状态:", self.user_status)
        
        # 密码策略
        self.password_policy = QComboBox()
        self.password_policy.addItems(["简单", "中等", "复杂"])
        WidgetUtils.set_combo_style(self.password_policy)
        layout.addRow("密码策略:", self.password_policy)
        
        # 密码有效期
        self.password_expire = QSpinBox()
        self.password_expire.setRange(0, 365)
        self.password_expire.setValue(90)
        self.password_expire.setSuffix(" 天")
        WidgetUtils.set_spin_style(self.password_expire)
        layout.addRow("密码有效期:", self.password_expire)
        
        # 登录失败限制
        self.login_fail_limit = QSpinBox()
        self.login_fail_limit.setRange(0, 10)
        self.login_fail_limit.setValue(5)
        self.login_fail_limit.setSuffix(" 次")
        WidgetUtils.set_spin_style(self.login_fail_limit)
        layout.addRow("登录失败限制:", self.login_fail_limit)
        
        return group
        
    def _create_system_group(self) -> QGroupBox:
        """创建系统设置组"""
        group = QGroupBox("系统设置")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        
        # 主题设置
        self.theme = QComboBox()
        self.theme.addItems(["跟随系统", "明亮", "暗色"])
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
        
    @PerformanceManager.measure_operation("load_settings")
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
                        "root-admin": "超级管理员",
                        "corp-admin": "企业管理员",
                        "user": "普通用户"
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
                    self.theme.setCurrentText({
                        "system": "跟随系统",
                        "light": "明亮",
                        "dark": "暗色"
                    }.get(settings.theme, "跟随系统"))
                    self.db_path.setText(settings.db_path)
                    self.log_path.setText(settings.log_path)
                    self.log_level.setCurrentText(settings.log_level)
                    self.log_retention.setValue(settings.log_retention)
                    
                    # 数据管理
                    self.data_cleanup.setChecked(settings.data_cleanup)
                    self.cleanup_period.setValue(settings.cleanup_period)
                    self.cleanup_scope.setCurrentText({
                        "all": "全部数据",
                        "sign": "仅签到记录",
                        "log": "仅日志记录"
                    }.get(settings.cleanup_scope, "全部数据"))
                    
        except Exception as e:
            ErrorHandler.handle_error(e, self, "加载设置失败")
            
    @PerformanceManager.measure_operation("save_settings")
    def save_settings(self):
        """保存设置"""
        try:
            # 验证设置
            if not self._validate_settings():
                return
                
            # 保存到数据库
            with self.db_manager.get_session() as session:
                settings = session.query(Settings).first()
                if not settings:
                    settings = Settings()
                    session.add(settings)
                    
                # 企业信息
                settings.corp_name = self.corp_name.text()
                settings.corp_id = self.corp_id.text()
                settings.corp_secret = self.corp_secret.text()
                settings.agent_id = self.agent_id.text()
                settings.corp_status = self.corp_status.isChecked()
                
                # 用户管理
                settings.default_role = {
                    "超级管理员": "root-admin",
                    "企业管理员": "corp-admin",
                    "普通用户": "user"
                }[self.default_role.currentText()]
                settings.user_status = self.user_status.isChecked()
                settings.password_policy = {
                    "简单": "simple",
                    "中等": "medium",
                    "复杂": "complex"
                }[self.password_policy.currentText()]
                settings.password_expire = self.password_expire.value()
                settings.login_fail_limit = self.login_fail_limit.value()
                
                # 系统设置
                settings.theme = {
                    "跟随系统": "system",
                    "明亮": "light",
                    "暗色": "dark"
                }[self.theme.currentText()]
                settings.db_path = self.db_path.text()
                settings.log_path = self.log_path.text()
                settings.log_level = self.log_level.currentText()
                settings.log_retention = self.log_retention.value()
                
                # 数据管理
                settings.data_cleanup = self.data_cleanup.isChecked()
                settings.cleanup_period = self.cleanup_period.value()
                settings.cleanup_scope = {
                    "全部数据": "all",
                    "仅签到记录": "sign",
                    "仅日志记录": "log"
                }[self.cleanup_scope.currentText()]
                
                session.commit()
                
            ErrorHandler.handle_info("保存设置成功", self, "成功")
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存设置失败")
            
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
            self.log_level.setCurrentIndex(1)
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
            
    @PerformanceManager.measure_operation("cleanup_data")
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