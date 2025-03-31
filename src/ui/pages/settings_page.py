# 此文件已优化，移除了企业和用户管理功能的直接实现
# 取而代之的是使用UserManagementPage和CorpManagePage组件
# 此重构使代码更加模块化，遵循了单一职责原则，提高了可维护性

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QCheckBox,
                             QSpinBox, QTabWidget, QSlider, QGridLayout, QFrame,
                             QScrollArea, QToolBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.ui.managers.style import StyleManager
from src.ui.managers.theme_manager import ThemeManager
from src.ui.utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from src.ui.managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.core.auth_manager import AuthManager
from src.core.database import DatabaseManager
from src.core.config_manager import ConfigManager
from src.models.settings import Settings
from src.models.user import User, UserRole
from src.ui.pages.corp_manage_page import CorpManagePage
from src.ui.pages.user_management_page import UserManagementPage
import os
import json
import shutil
from datetime import datetime

from src.models.config_change import ConfigChange
from src.models.operation_log import OperationLog

logger = get_logger(__name__)

class SettingsPage(QWidget):
    """设置页面"""
    
    def __init__(self, auth_manager: AuthManager, db_manager: DatabaseManager, user_id=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.user_id = user_id
        self.error_handler = ErrorHandler()
        self.performance_manager = PerformanceManager()
        self.theme_manager = ThemeManager()
        self.config_manager = ConfigManager()
        
        # 初始化UI
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setObjectName("settingsPage")
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建标签页控件
        self.tabs = QTabWidget()
        
        # 创建各个标签页
        system_tab = QWidget()
        self.setup_system_tab(system_tab)
        self.tabs.addTab(system_tab, "系统设置")
        
        # 用户管理标签页 - 使用UserManagementPage组件
        user_tab = QWidget()
        user_tab_layout = QVBoxLayout(user_tab)
        user_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.user_management_page = UserManagementPage(
            self.db_manager, 
            auth_manager=self.auth_manager, 
            user_id=self.user_id
        )
        user_tab_layout.addWidget(self.user_management_page)
        self.tabs.addTab(user_tab, "用户管理")
        
        # 企业管理标签页 - 使用CorpManagePage组件
        corp_tab = QWidget()
        corp_tab_layout = QVBoxLayout(corp_tab)
        corp_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.corp_manage_page = CorpManagePage(
            self.db_manager, 
            auth_manager=self.auth_manager, 
            user_id=self.user_id
        )
        corp_tab_layout.addWidget(self.corp_manage_page)
        self.tabs.addTab(corp_tab, "企业管理")
        
        # 权限标签页
        perm_tab = QWidget()
        self.setup_permission_tab(perm_tab)
        self.tabs.addTab(perm_tab, "权限设置")
        
        # 添加标签页控件到主布局
        layout.addWidget(self.tabs)
        
        # 创建按钮区域
        buttons_layout = QHBoxLayout()
        
        # 添加保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.save_button)
        
        # 添加重置按钮
        self.reset_button = QPushButton("重置")
        self.reset_button.setObjectName("secondaryButton")
        self.reset_button.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(self.reset_button)
        
        # 添加弹性空间
        buttons_layout.addStretch()
        
        # 添加按钮布局到主布局
        layout.addLayout(buttons_layout)
        
        # 添加淡入动画
        AnimationManager.fade_in(self)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_settings_style())
        
        # 更新权限UI
        self._update_ui_by_permission()
        
        # 加载设置数据
        self.load_data()
        
    def setup_system_tab(self, tab):
        """设置系统设置标签页"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建工具栏
        toolbar = QToolBar()
        toolbar.setObjectName("settingsToolbar")
        
        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_settings)
        toolbar.addWidget(save_btn)
        
        # 重置按钮
        reset_btn = QPushButton("重置设置")
        reset_btn.setObjectName("secondaryButton")
        reset_btn.clicked.connect(self.reset_settings)
        toolbar.addWidget(reset_btn)
        
        # 初始化向导按钮
        wizard_btn = QPushButton("初始化向导")
        wizard_btn.setObjectName("secondaryButton")
        wizard_btn.clicked.connect(self.show_init_wizard)
        toolbar.addWidget(wizard_btn)
        
        layout.addWidget(toolbar)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("settingsScrollArea")
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # 创建系统设置组
        system_group = self._create_system_group()
        content_layout.addWidget(system_group)
        
        # 创建数据设置组
        data_group = self._create_data_group()
        content_layout.addWidget(data_group)
        
        # 创建日志设置组
        log_group = self._create_log_group()
        content_layout.addWidget(log_group)
        
        # 创建企业微信设置组
        wecom_group = self._create_wecom_group()
        content_layout.addWidget(wecom_group)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
    
    def setup_user_tab(self, tab):
        """设置用户管理标签页
        
        Args:
            tab: 标签页控件
        """
        # 这个方法不再需要具体实现，但保留方法签名以保持兼容性
        # 因为用户管理功能已经迁移到UserManagementPage组件
        pass

    def setup_permission_tab(self, tab):
        """设置权限配置标签页"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建工具栏
        toolbar = QToolBar()
        toolbar.setObjectName("permissionToolbar")
        
        # 添加角色选择下拉框
        role_label = QLabel("选择角色:")
        toolbar.addWidget(role_label)
        
        self.role_combo = QComboBox()
        self.role_combo.setMinimumWidth(200)
        WidgetUtils.set_combo_style(self.role_combo)
        self.role_combo.currentIndexChanged.connect(self.on_role_changed)
        toolbar.addWidget(self.role_combo)
        
        toolbar.addSeparator()
        
        # 保存按钮
        save_btn = QPushButton("保存权限")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_permissions)
        toolbar.addWidget(save_btn)
        
        # 重置按钮
        reset_btn = QPushButton("重置权限")
        reset_btn.setObjectName("secondaryButton")
        reset_btn.clicked.connect(self.reset_permissions)
        toolbar.addWidget(reset_btn)
        
        layout.addWidget(toolbar)
        
        # 创建权限表格
        self.perm_table = QTableWidget()
        self.perm_table.setColumnCount(3)
        self.perm_table.setHorizontalHeaderLabels(["权限", "描述", "允许"])
        self._setup_table(self.perm_table)
        layout.addWidget(self.perm_table)
        
        # 初始化角色下拉框
        self.init_role_combo()

    def _setup_table(self, table: QTableWidget):
        """设置表格通用样式
        
        Args:
            table: 表格控件
        """
        # 自动调整列宽
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 设置样式
        WidgetUtils.set_table_style(table)
        
        # 设置选择模式
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 禁止编辑
        table.setEditTriggers(QTableWidget.NoEditTriggers)
    
    def _update_ui_by_permission(self):
        """根据用户权限更新UI"""
        with self.db_manager.get_session() as session:
            # 检查是否有管理用户的权限
            has_manage_users = self.auth_manager.has_permission(self.user_id, "manage_users", session)
            
            # 检查是否有管理企业的权限
            has_manage_corps = self.auth_manager.has_permission(self.user_id, "manage_corps", session)
            
            # 检查是否有管理系统设置的权限
            has_manage_settings = self.auth_manager.has_permission(self.user_id, "manage_settings", session)
            
            # 检查是否有管理权限设置的权限
            has_manage_permissions = self.auth_manager.has_permission(self.user_id, "manage_permissions", session)
            
            # 更新标签页可见性
            for i in range(self.tabs.count()):
                tab_text = self.tabs.tabText(i)
                
                if tab_text == "用户管理" and not has_manage_users:
                    self.tabs.setTabVisible(i, False)
                    
                elif tab_text == "企业管理" and not has_manage_corps:
                    self.tabs.setTabVisible(i, False)
                    
                elif tab_text == "系统设置" and not has_manage_settings:
                    self.tabs.setTabVisible(i, False)
                    
                elif tab_text == "权限设置" and not has_manage_permissions:
                    self.tabs.setTabVisible(i, False)

    def filter_users(self):
        """过滤用户列表"""
        # 这个方法不再需要，由UserManagementPage组件自行实现
        pass

    def init_role_combo(self):
        """初始化角色下拉框"""
        try:
            # 获取所有角色
            with self.db_manager.get_session() as session:
                roles = self.auth_manager.get_all_roles()
                
                # 添加角色到下拉框
                self.role_combo.clear()
                for role in roles:
                    self.role_combo.addItem(role["name"], role["id"])
                    
        except Exception as e:
            self.error_handler.handle_error(e, self, "加载角色数据失败")
    
    def on_role_changed(self, index):
        """角色选择改变事件处理"""
        if index < 0:
            return
            
        # 获取选中的角色ID
        role_id = self.role_combo.currentData()
        
        # 加载对应角色的权限
        self.load_role_permissions_by_role(role_id)

    def load_role_permissions_by_role(self, role_id):
        """根据选定角色加载权限数据"""
        try:
            # 使用新会话查询角色权限
            with self.db_manager.get_session() as session:
                # 获取所有角色和权限
                role_permissions = self.auth_manager.get_all_role_permissions(session)
                
                # 查找指定角色的权限
                selected_role_perm = None
                for role_perm in role_permissions:
                    if role_perm["role_id"] == role_id:
                        selected_role_perm = role_perm
                        break
                
                # 如果找不到选定角色的权限，清空表格并返回
                if not selected_role_perm:
                    self.perm_table.setRowCount(0)
                    return
                
                # 更新权限表格
                perms = selected_role_perm["permissions"]
                self.perm_table.setRowCount(len(perms))
                
                # 检查是否为root-admin角色（超级管理员）
                is_root_admin = role_id == UserRole.ROOT_ADMIN.value
                
                # 填充表格
                for row_idx, perm in enumerate(perms):
                    # 权限名称
                    perm_item = QTableWidgetItem(perm["name"])
                    self.perm_table.setItem(row_idx, 0, perm_item)
                    
                    # 权限描述
                    desc_item = QTableWidgetItem(perm["description"])
                    self.perm_table.setItem(row_idx, 1, desc_item)
                    
                    # 允许复选框
                    perm_cell = QWidget()
                    perm_layout = QHBoxLayout(perm_cell)
                    perm_layout.setContentsMargins(0, 0, 0, 0)
                    perm_layout.setAlignment(Qt.AlignCenter)
                    
                    perm_checkbox = QCheckBox()
                    
                    # 如果是root-admin角色，强制选中所有权限并禁用复选框
                    if is_root_admin:
                        perm_checkbox.setChecked(True)
                        perm_checkbox.setEnabled(False)
                    else:
                        perm_checkbox.setChecked(perm["allowed"])
                        
                    perm_layout.addWidget(perm_checkbox)
                    
                    self.perm_table.setCellWidget(row_idx, 2, perm_cell)
                    
                    # 保存权限数据
                    perm_item.setData(Qt.UserRole, {"perm_id": perm["id"], "role_id": role_id})
        
        except Exception as e:
            self.error_handler.handle_error(e, self, "加载权限数据失败")

    def load_role_permissions(self):
        """加载角色权限数据"""
        try:
            # 初始化角色下拉框
            self.init_role_combo()
            
            # 如果有选中的角色，则加载该角色的权限
            if self.role_combo.count() > 0:
                role_id = self.role_combo.currentData()
                self.load_role_permissions_by_role(role_id)
                
        except Exception as e:
            self.error_handler.handle_error(e, self, "加载权限数据失败")
    
    def save_permissions(self):
        """保存权限设置"""
        try:
            # 检查权限
            if not self._validate_permission("manage_permissions"):
                self.error_handler.handle_warning("您没有权限修改权限设置", self)
                return
                
            # 获取当前选中的角色ID
            role_id = self.role_combo.currentData()
            if not role_id:
                self.error_handler.handle_warning("请先选择一个角色", self)
                return
                
            # 判断是否为root-admin角色，如果是则不允许修改
            if role_id == UserRole.ROOT_ADMIN.value:
                self.error_handler.handle_warning("超级管理员角色的权限不能修改", self)
                return
                
            # 收集权限数据
            permissions_data = []
            
            # 遍历表格获取权限设置
            for row in range(self.perm_table.rowCount()):
                # 获取权限ID
                perm_item = self.perm_table.item(row, 0)
                
                if perm_item:
                    perm_data = perm_item.data(Qt.UserRole)
                    
                    if perm_data:
                        # 获取复选框状态
                        perm_cell = self.perm_table.cellWidget(row, 2)
                        if perm_cell:
                            checkbox = perm_cell.findChild(QCheckBox)
                            if checkbox:
                                allowed = checkbox.isChecked()
                                
                                # 添加到权限数据列表
                                permissions_data.append({
                                    "role_id": perm_data["role_id"],
                                    "perm_id": perm_data["perm_id"],
                                    "allowed": allowed
                                })
            
            # 使用AuthManager更新权限
            with self.db_manager.get_session() as session:
                for perm_data in permissions_data:
                    self.auth_manager.set_role_permission(
                        perm_data["role_id"],
                        perm_data["perm_id"],
                        perm_data["allowed"],
                        session
                    )
                
                # 提交事务
                session.commit()
            
            # 记录操作
            self._log_operation("保存权限", f"成功更新角色 '{self.role_combo.currentText()}' 的权限")
            
            # 提示用户
            self.error_handler.handle_info("权限设置已保存", self, "成功")
            
        except Exception as e:
            self.error_handler.handle_error(e, self, "保存权限失败")
    
    def reset_permissions(self):
        """重置权限设置"""
        try:
            # 检查权限
            if not self._validate_permission("manage_permissions"):
                self.error_handler.handle_warning("您没有权限修改权限设置", self)
                return
            
            # 确认重置
            confirm = QMessageBox.question(
                self,
                "确认重置",
                "确定要重置所有权限设置吗？这将恢复到系统默认值。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return
            
            # 重置权限
            with self.db_manager.get_session() as session:
                self.auth_manager.reset_permissions(session)
            
            # 重新加载权限数据
            self.load_role_permissions()
            
            # 记录操作
            self._log_operation("重置权限", "将所有权限重置为默认值")
            
            # 提示用户
            self.error_handler.handle_info("权限设置已重置为默认值", self, "成功")
            
        except Exception as e:
            self.error_handler.handle_error(e, self, "重置权限失败")
    
    def _log_operation(self, operation_type: str, description: str):
        """记录操作日志
        
        Args:
            operation_type: 操作类型
            description: 操作描述
        """
        try:
            # 创建操作日志
            log_entry = OperationLog(
                user_id=self.user_id,
                operation_type=operation_type,
                description=description,
                ip_address=self._get_client_ip(),
                timestamp=datetime.now()
            )
            
            # 保存到数据库
            with self.db_manager.get_session() as session:
                session.add(log_entry)
                session.commit()
                
        except Exception as e:
            logger.error(f"记录操作日志失败: {str(e)}")
    
    def _get_client_ip(self) -> str:
        """获取客户端IP地址
        
        Returns:
            str: IP地址
        """
        import socket
        try:
            # 获取本机主机名
            host_name = socket.gethostname()
            # 获取本机IP
            host_ip = socket.gethostbyname(host_name)
            return host_ip
        except Exception:
            return "127.0.0.1"
    
    def _validate_permission(self, operation: str) -> bool:
        """验证当前用户是否有权限执行操作
        
        Args:
            operation: 操作名称
            
        Returns:
            bool: 是否有权限
        """
        # 权限映射表
        permission_map = {
            "manage_users": "管理用户",
            "manage_corps": "管理企业",
            "manage_permissions": "管理权限",
            "manage_settings": "管理系统设置"
        }
        
        try:
            # 检查用户是否有权限
            with self.db_manager.get_session() as session:
                has_permission = self.auth_manager.has_permission(
                    self.user_id,
                    operation,
                    session
                )
                
            # 如果没有权限，记录日志
            if not has_permission:
                # 获取操作描述
                operation_desc = permission_map.get(operation, operation)
                
                # 记录日志
                self._log_operation(
                    "权限拒绝",
                    f"尝试执行无权限操作: {operation_desc}"
                )
                
            return has_permission
            
        except Exception as e:
            logger.error(f"验证权限失败: {str(e)}")
            return False
    
    def load_data(self):
        """加载设置数据"""
        try:
            # 立即加载权限数据，确保在任何标签页都能看到权限数据
            self.load_role_permissions()
            
            # 根据当前标签页加载数据
            current_tab = self.tabs.tabText(self.tabs.currentIndex())
            
            if current_tab == "系统设置":
                self._load_system_settings()
            # 企业管理和用户管理页面有自己的数据加载逻辑
                
        except Exception as e:
            self.error_handler.handle_error(e, self, "加载设置数据失败")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 确保配置目录存在
            import os
            config_dir = os.path.dirname(self.config_manager.config_dir)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # 保存设置
            self._save_system_settings()
            self._log_operation("save_settings", "保存系统设置")
            ErrorHandler.handle_info("设置保存成功", self, "成功")
        except Exception as e:
            logger.error(f"保存设置失败: {str(e)}")
            ErrorHandler.handle_error(e, self, "保存设置失败")
    
    def reset_settings(self):
        """重置设置"""
        try:
            # 获取当前标签页
            current_tab = self.tabs.tabText(self.tabs.currentIndex())
            
            # 根据当前标签页重置对应的设置
            if current_tab == "系统设置":
                self._load_system_settings()  # 重新加载系统设置
            elif current_tab == "权限设置":
                self.reset_permissions()  # 重置权限设置
            elif current_tab == "企业管理":
                # 企业管理页面有自己的重置逻辑
                self.corp_manage_page.refresh_data()
            elif current_tab == "用户管理":
                # 用户管理页面有自己的重置逻辑
                self.user_management_page.refresh_data()
                
        except Exception as e:
            self.error_handler.handle_error(e, self, "重置设置失败")
            
    def _create_system_group(self) -> QGroupBox:
        """创建系统设置组
        
        Returns:
            QGroupBox: 系统设置组控件
        """
        group = QGroupBox("基本设置")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        # 主题设置
        layout.addWidget(QLabel("界面主题:"), 0, 0)
        self.theme = QComboBox()
        self.theme.addItems(["浅色", "深色", "跟随系统"])
        WidgetUtils.set_combo_style(self.theme)
        layout.addWidget(self.theme, 0, 1)
        
        return group
    
    def _create_data_group(self) -> QGroupBox:
        """创建数据设置组
        
        Returns:
            QGroupBox: 数据设置组控件
        """
        group = QGroupBox("数据设置")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        # 数据库路径
        layout.addWidget(QLabel("数据库路径:"), 0, 0)
        db_path_layout = QHBoxLayout()
        self.db_path = QLineEdit()
        WidgetUtils.set_input_style(self.db_path)
        db_path_layout.addWidget(self.db_path)
        
        self.db_path_browse = QPushButton("浏览...")
        self.db_path_browse.setObjectName("secondaryButton")
        self.db_path_browse.clicked.connect(lambda: self._browse_path(self.db_path))
        db_path_layout.addWidget(self.db_path_browse)
        layout.addLayout(db_path_layout, 0, 1)
        
        # 数据备份路径
        layout.addWidget(QLabel("备份路径:"), 1, 0)
        backup_layout = QHBoxLayout()
        self.backup_path = QLineEdit()
        WidgetUtils.set_input_style(self.backup_path)
        backup_layout.addWidget(self.backup_path)
        
        self.backup_browse = QPushButton("浏览...")
        self.backup_browse.setObjectName("secondaryButton")
        self.backup_browse.clicked.connect(lambda: self._browse_path(self.backup_path))
        backup_layout.addWidget(self.backup_browse)
        layout.addLayout(backup_layout, 1, 1)
        
        # 自动备份
        layout.addWidget(QLabel("自动备份:"), 2, 0)
        self.auto_backup = QCheckBox("启用自动备份")
        self.auto_backup.setChecked(True)
        layout.addWidget(self.auto_backup, 2, 1)
        
        # 备份频率
        layout.addWidget(QLabel("备份频率:"), 3, 0)
        self.backup_frequency = QComboBox()
        self.backup_frequency.addItems(["每天", "每周", "每月"])
        WidgetUtils.set_combo_style(self.backup_frequency)
        layout.addWidget(self.backup_frequency, 3, 1)
        
        # 备份保留时间
        layout.addWidget(QLabel("备份保留(天):"), 4, 0)
        self.backup_retention = QSpinBox()
        self.backup_retention.setMinimum(7)
        self.backup_retention.setMaximum(365)
        self.backup_retention.setValue(30)
        WidgetUtils.set_input_style(self.backup_retention)
        layout.addWidget(self.backup_retention, 4, 1)
        
        # 数据清理
        layout.addWidget(QLabel("数据清理:"), 5, 0)
        self.data_cleanup = QCheckBox("启用自动数据清理")
        self.data_cleanup.setChecked(True)
        layout.addWidget(self.data_cleanup, 5, 1)
        
        return group
        
    def _create_log_group(self) -> QGroupBox:
        """创建日志设置组
        
        Returns:
            QGroupBox: 日志设置组控件
        """
        group = QGroupBox("日志设置")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        # 日志路径
        layout.addWidget(QLabel("日志路径:"), 0, 0)
        log_path_layout = QHBoxLayout()
        self.log_path = QLineEdit()
        WidgetUtils.set_input_style(self.log_path)
        log_path_layout.addWidget(self.log_path)
        
        self.log_path_browse = QPushButton("浏览...")
        self.log_path_browse.setObjectName("secondaryButton")
        self.log_path_browse.clicked.connect(lambda: self._browse_path(self.log_path))
        log_path_layout.addWidget(self.log_path_browse)
        layout.addLayout(log_path_layout, 0, 1)
        
        # 日志级别
        layout.addWidget(QLabel("日志级别:"), 1, 0)
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        WidgetUtils.set_combo_style(self.log_level)
        layout.addWidget(self.log_level, 1, 1)
        
        # 日志保留时间
        layout.addWidget(QLabel("日志保留(天):"), 2, 0)
        self.log_retention = QSpinBox()
        self.log_retention.setMinimum(7)
        self.log_retention.setMaximum(365)
        self.log_retention.setValue(30)
        WidgetUtils.set_input_style(self.log_retention)
        layout.addWidget(self.log_retention, 2, 1)
        
        return group
    
    def _create_wecom_group(self) -> QGroupBox:
        """创建企业微信设置组
        
        Returns:
            QGroupBox: 企业微信设置组控件
        """
        group = QGroupBox("企业微信设置")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        # 企业微信API超时
        layout.addWidget(QLabel("API超时(秒):"), 0, 0)
        self.api_timeout = QSpinBox()
        self.api_timeout.setMinimum(5)
        self.api_timeout.setMaximum(60)
        self.api_timeout.setValue(10)
        WidgetUtils.set_input_style(self.api_timeout)
        layout.addWidget(self.api_timeout, 0, 1)
        
        # 重试次数
        layout.addWidget(QLabel("重试次数:"), 1, 0)
        self.retry_count = QSpinBox()
        self.retry_count.setMinimum(0)
        self.retry_count.setMaximum(5)
        self.retry_count.setValue(3)
        WidgetUtils.set_input_style(self.retry_count)
        layout.addWidget(self.retry_count, 1, 1)
        
        return group
    
    def _browse_path(self, line_edit):
        """浏览文件路径
        
        Args:
            line_edit: 文本框控件
        """
        # 选择目录
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择目录",
            os.path.expanduser("~")
        )
        if dir_path:
            line_edit.setText(dir_path)
    
    def _load_system_settings(self):
        """加载系统设置"""
        try:
            # 创建默认设置字典
            default_settings = {
                "theme": "浅色",
                "db_path": "",
                "backup_path": "",
                "auto_backup": "True",
                "backup_frequency": "每周",
                "backup_retention": "30",
                "data_cleanup": "True",
                "log_path": "",
                "log_level": "INFO",
                "log_retention": "30",
                "api_timeout": "10",
                "retry_count": "3"
            }
            
            # 从配置文件加载设置（如果存在）
            user_settings = {}
            try:
                # 使用正确的配置文件路径
                default_config_dir = os.path.join(os.path.expanduser("~"), ".wecom_live_sign")
                default_config_file = os.path.join(default_config_dir, "config.json")
                
                if os.path.exists(default_config_file):
                    with open(default_config_file, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        
                        # 提取系统部分设置
                        if "system" in config_data:
                            system_config = config_data["system"]
                            if isinstance(system_config, dict):
                                # 转换系统配置中的设置
                                if "theme" in system_config:
                                    user_settings["theme"] = system_config["theme"]
                                if "log_level" in system_config:
                                    user_settings["log_level"] = system_config["log_level"]
                                if "log_retention" in system_config:
                                    user_settings["log_retention"] = str(system_config["log_retention"])
                                if "log_path" in system_config:
                                    user_settings["log_path"] = system_config["log_path"]
                                if "backup_retention" in system_config:
                                    user_settings["backup_retention"] = str(system_config["backup_retention"])
                        
                        # 提取数据库部分设置
                        if "database" in config_data:
                            db_config = config_data["database"]
                            if isinstance(db_config, dict):
                                if "path" in db_config:
                                    user_settings["db_path"] = db_config["path"]
                                if "backup_path" in db_config:
                                    user_settings["backup_path"] = db_config["backup_path"]
                        
                        # 提取路径部分设置
                        if "paths" in config_data:
                            paths = config_data["paths"]
                            if isinstance(paths, dict):
                                if "log" in paths:
                                    user_settings["log_path"] = paths["log"]
                                if "backup" in paths:
                                    user_settings["backup_path"] = paths["backup"]
                        
                        # 提取企业微信API设置
                        if "wecom_api" in config_data:
                            api_config = config_data["wecom_api"]
                            if isinstance(api_config, dict):
                                if "timeout" in api_config:
                                    user_settings["api_timeout"] = str(api_config["timeout"])
                                if "retry_count" in api_config:
                                    user_settings["retry_count"] = str(api_config["retry_count"])
                        
                        # 直接存在于config.json根级别的设置
                        for key in default_settings.keys():
                            if key in config_data:
                                user_settings[key] = str(config_data[key])
                                
                    logger.info(f"从系统配置文件加载设置: {default_config_file}")
            except json.JSONDecodeError:
                logger.error(f"配置文件格式错误: {default_config_file}")
            except Exception as e:
                logger.error(f"加载系统配置文件失败: {str(e)}")
            
            # 从数据库加载设置
            db_settings = {}
            try:
                with self.db_manager.get_session() as session:
                    # 获取所有设置
                    settings = session.query(Settings).all()
                    
                    # 创建设置字典方便查找
                    db_settings = {s.name: s.value for s in settings if s.name in default_settings}
            except Exception as e:
                logger.error(f"从数据库加载设置失败: {str(e)}")
            
            # 合并设置，按优先级：数据库 > 用户配置文件 > 系统默认配置
            merged_settings = {**default_settings, **user_settings, **db_settings}
            
            # 安全设置控件值，使用try-except避免控件访问错误
            self._safely_set_settings_values(merged_settings)
                
        except Exception as e:
            self.error_handler.handle_error(e, self, "加载系统设置失败")
            
    def _safely_set_settings_values(self, settings):
        """安全地设置设置控件值
        
        Args:
            settings: 合并后的设置字典
        """
        try:
            # 基本设置
            self._safely_set_combobox(self.theme, settings.get("theme", "浅色"))
            
            # 数据设置
            self._safely_set_text(self.db_path, settings.get("db_path", ""))
            self._safely_set_text(self.backup_path, settings.get("backup_path", ""))
            self._safely_set_checkbox(self.auto_backup, settings.get("auto_backup", "True") == "True")
            self._safely_set_combobox(self.backup_frequency, settings.get("backup_frequency", "每周"))
            self._safely_set_spinbox(self.backup_retention, settings.get("backup_retention", "30"))
            self._safely_set_checkbox(self.data_cleanup, settings.get("data_cleanup", "True") == "True")
            
            # 日志设置
            self._safely_set_text(self.log_path, settings.get("log_path", ""))
            self._safely_set_combobox(self.log_level, settings.get("log_level", "INFO"))
            self._safely_set_spinbox(self.log_retention, settings.get("log_retention", "30"))
            
            # 企业微信设置
            self._safely_set_spinbox(self.api_timeout, settings.get("api_timeout", "10"))
            self._safely_set_spinbox(self.retry_count, settings.get("retry_count", "3"))
                
        except Exception as e:
            logger.error(f"设置控件值失败: {str(e)}")
            
    def _safely_set_combobox(self, combobox, value):
        """安全设置下拉框值
        
        Args:
            combobox: 下拉框控件
            value: 要设置的值
        """
        try:
            if combobox and value:
                index = combobox.findText(value)
                if index >= 0:
                    combobox.setCurrentIndex(index)
        except Exception as e:
            logger.error(f"设置下拉框值失败: {str(e)}")
    
    def _safely_set_checkbox(self, checkbox, checked):
        """安全设置复选框值
        
        Args:
            checkbox: 复选框控件
            checked: 是否选中
        """
        try:
            if checkbox:
                checkbox.setChecked(checked)
        except Exception as e:
            logger.error(f"设置复选框值失败: {str(e)}")
    
    def _safely_set_spinbox(self, spinbox, value):
        """安全设置数字框值
        
        Args:
            spinbox: 数字框控件
            value: 要设置的值
        """
        try:
            if spinbox and value:
                spinbox.setValue(int(value))
        except ValueError:
            # 如果无法转换为整数，使用最小值
            if spinbox:
                spinbox.setValue(spinbox.minimum())
                logger.error(f"无法将'{value}'转换为整数，使用最小值")
        except Exception as e:
            logger.error(f"设置数字框值失败: {str(e)}")
    
    def _safely_set_text(self, text_edit, text):
        """安全设置文本框值
        
        Args:
            text_edit: 文本框控件
            text: 要设置的文本
        """
        try:
            if text_edit:
                text_edit.setText(text)
        except Exception as e:
            logger.error(f"设置文本框值失败: {str(e)}")
    
    def _save_system_settings(self):
        """保存系统设置"""
        try:
            # 检查权限
            if not self._validate_permission("manage_settings"):
                self.error_handler.handle_warning("您没有权限修改系统设置", self)
                return
            
            # 收集设置数据
            settings_data = {
                # 基本设置
                "theme": self.theme.currentText(),
                
                # 数据设置
                "db_path": self.db_path.text(),
                "backup_path": self.backup_path.text(),
                "auto_backup": str(self.auto_backup.isChecked()),
                "backup_frequency": self.backup_frequency.currentText(),
                "backup_retention": str(self.backup_retention.value()),
                "data_cleanup": str(self.data_cleanup.isChecked()),
                
                # 日志设置
                "log_path": self.log_path.text(),
                "log_level": self.log_level.currentText(),
                "log_retention": str(self.log_retention.value()),
                
                # 企业微信设置
                "api_timeout": str(self.api_timeout.value()),
                "retry_count": str(self.retry_count.value())
            }
            
            # 更新设置到数据库
            with self.db_manager.get_session() as session:
                for key, value in settings_data.items():
                    # 检查设置是否存在
                    setting = session.query(Settings).filter_by(name=key).first()
                    
                    if setting:
                        # 更新现有设置
                        setting.value = value
                    else:
                        # 创建新设置
                        setting = Settings(
                            name=key,
                            value=value,
                            type="system",
                            description=""
                        )
                        session.add(setting)
                
                # 提交更改
                session.commit()
            
            # 保存设置到系统配置文件
            try:
                # 使用正确的配置文件路径
                default_config_dir = os.path.join(os.path.expanduser("~"), ".wecom_live_sign")
                if not os.path.exists(default_config_dir):
                    os.makedirs(default_config_dir)
                
                default_config_file = os.path.join(default_config_dir, "config.json")
                
                # 读取现有配置（如果存在）
                config_data = {}
                if os.path.exists(default_config_file):
                    try:
                        with open(default_config_file, "r", encoding="utf-8") as f:
                            config_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.error(f"配置文件格式错误: {default_config_file}，将创建新文件")
                        config_data = {"initialized": True}
                    except Exception as e:
                        logger.error(f"读取配置文件失败: {str(e)}，将创建新文件")
                        config_data = {"initialized": True}
                else:
                    # 如果文件不存在，创建基本结构
                    config_data = {"initialized": True}
                
                # 确保各部分配置结构存在
                if "system" not in config_data:
                    config_data["system"] = {}
                if "database" not in config_data:
                    config_data["database"] = {}
                if "paths" not in config_data:
                    config_data["paths"] = {}
                if "wecom_api" not in config_data:
                    config_data["wecom_api"] = {}
                
                # 更新各部分配置
                # 系统设置
                config_data["system"]["theme"] = settings_data["theme"]
                config_data["system"]["log_level"] = settings_data["log_level"]
                config_data["system"]["log_retention"] = int(settings_data["log_retention"])
                config_data["system"]["backup_retention"] = int(settings_data["backup_retention"])
                
                # 数据库设置
                config_data["database"]["type"] = "SQLite"  # 固定使用SQLite
                config_data["database"]["path"] = settings_data["db_path"]
                config_data["database"]["backup_path"] = settings_data["backup_path"]
                
                # 路径设置
                config_data["paths"]["log"] = settings_data["log_path"]
                config_data["paths"]["backup"] = settings_data["backup_path"]
                
                # 企业微信API设置
                config_data["wecom_api"]["timeout"] = int(settings_data["api_timeout"])
                config_data["wecom_api"]["retry_count"] = int(settings_data["retry_count"])
                config_data["wecom_api"]["enable_cache"] = False  # 固定不使用缓存
                
                # 保存配置
                with open(default_config_file, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=4)
                logger.info(f"设置已保存到系统配置文件: {default_config_file}")
            except Exception as e:
                logger.error(f"保存系统配置文件失败: {str(e)}")
            
            # 应用主题变化
            self.theme_manager.set_theme(settings_data["theme"])
            
            # 记录设置变更
            self._log_operation("更新系统设置", "保存系统设置配置")
            
            # 记录配置变更
            config_change = ConfigChange(
                user_id=self.user_id,
                change_type="系统设置",
                changes=json.dumps(settings_data, ensure_ascii=False),
                timestamp=datetime.now()
            )
            
            with self.db_manager.get_session() as session:
                session.add(config_change)
                session.commit()
            
            # 提示成功
            self.error_handler.handle_info("系统设置已保存", self, "成功")
            
        except Exception as e:
            self.error_handler.handle_error(e, self, "保存系统设置失败")
    
    def show_init_wizard(self):
        """显示初始化向导"""
        try:
            # 导入InitWizard类
            try:
                from src.ui.dialogs.init_wizard import InitWizard
            except ImportError:
                from src.ui.components.dialogs.init_wizard import InitWizard
            
            # 显示确认对话框
            confirm = QMessageBox.question(
                self,
                "确认操作",
                "初始化向导将引导您重新配置系统。是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if confirm != QMessageBox.StandardButton.Yes:
                return
                
            # 创建并显示向导
            wizard = InitWizard(self.db_manager, self.config_manager, self.auth_manager)
            if wizard.exec() == QDialog.DialogCode.Accepted:
                # 重新加载设置
                self.load_data()
                # 记录操作
                self._log_operation("系统初始化", "完成系统初始化向导")
                # 提示用户
                self.error_handler.handle_info("系统初始化完成", self, "成功")
            
        except Exception as e:
            logger.error(f"初始化向导启动失败: {str(e)}")
            self.error_handler.handle_error(e, self, "初始化向导启动失败")
