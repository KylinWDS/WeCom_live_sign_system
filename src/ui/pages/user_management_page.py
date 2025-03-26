from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QCheckBox,
                             QToolBar, QAbstractItemView, QApplication, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from src.core.auth_manager import AuthManager
from src.utils.logger import get_logger
from ..managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.core.database import DatabaseManager
from src.models.user import User, UserRole
from src.models.corporation import Corporation as Corp
import pandas as pd
import os

logger = get_logger(__name__)

class UserDialog(QDialog):
    """用户编辑对话框"""
    
    def __init__(self, auth_manager: AuthManager, db_manager: DatabaseManager, user_data=None, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.user_data = user_data
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑用户" if self.user_data else "添加用户")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        layout.setSpacing(10)
        
        # 登录名
        self.login_name_edit = QLineEdit()
        if self.user_data:
            login_name = self.user_data.get('login_name', '') or self.user_data.get('username', '')
            if isinstance(self.user_data, dict):
                login_name = self.user_data.get('login_name', '') or self.user_data.get('username', '')
            else:
                login_name = getattr(self.user_data, 'login_name', '') or getattr(self.user_data, 'username', '')
            self.login_name_edit.setText(login_name)
            self.login_name_edit.setEnabled(False)  # 登录名不可修改
        WidgetUtils.set_input_style(self.login_name_edit)
        layout.addRow("登录名:", self.login_name_edit)
        
        # 显示名称
        self.name_edit = QLineEdit()
        if self.user_data:
            name = ""
            if isinstance(self.user_data, dict):
                name = self.user_data.get('name', '')
            else:
                name = getattr(self.user_data, 'name', '')
            self.name_edit.setText(name)
        WidgetUtils.set_input_style(self.name_edit)
        layout.addRow("显示名称:", self.name_edit)
        
        # 企业微信ID
        self.wecom_code_edit = QLineEdit()
        if self.user_data:
            wecom_code = ""
            if isinstance(self.user_data, dict):
                wecom_code = self.user_data.get('wecom_code', '')
            else:
                wecom_code = getattr(self.user_data, 'wecom_code', '')
            self.wecom_code_edit.setText(wecom_code)
        WidgetUtils.set_input_style(self.wecom_code_edit)
        layout.addRow("企业微信ID:", self.wecom_code_edit)
        
        # 密码修改区域
        self.change_password_check = QCheckBox("修改密码")
        if not self.user_data:  # 如果是新用户，默认勾选且不可修改
            self.change_password_check.setChecked(True)
            self.change_password_check.setEnabled(False)
        self.change_password_check.stateChanged.connect(self.toggle_password_fields)
        layout.addRow("", self.change_password_check)
        
        # 密码组
        password_group = QGroupBox("密码设置")
        password_layout = QFormLayout(password_group)
        
        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("请输入新密码")
        self.password_edit.setClearButtonEnabled(True)  # 添加清除按钮
        WidgetUtils.set_input_style(self.password_edit)
        password_layout.addRow("密码:", self.password_edit)
        
        # 确认密码
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setPlaceholderText("请再次输入新密码")
        self.confirm_password_edit.setClearButtonEnabled(True)  # 添加清除按钮
        WidgetUtils.set_input_style(self.confirm_password_edit)
        password_layout.addRow("确认密码:", self.confirm_password_edit)
        
        layout.addRow("", password_group)
        self.password_group = password_group
        
        # 如果是编辑模式且未选择修改密码，则禁用密码字段
        if self.user_data:
            # 确保初始状态为未勾选
            self.change_password_check.setChecked(False)
            # 显式调用状态变更处理函数
            self.toggle_password_fields(Qt.CheckState.Unchecked)
            
            # 额外确保密码字段被禁用
            self.password_edit.setReadOnly(True)
            self.password_edit.setEnabled(False)
            self.confirm_password_edit.setReadOnly(True)
            self.confirm_password_edit.setEnabled(False)
        else:
            # 新用户默认勾选且启用密码字段
            self.change_password_check.setChecked(True)
            self.toggle_password_fields(Qt.CheckState.Checked)
            
            # 额外确保密码字段被启用
            self.password_edit.setReadOnly(False)
            self.password_edit.setEnabled(True)
            self.confirm_password_edit.setReadOnly(False)
            self.confirm_password_edit.setEnabled(True)
        
        # 角色
        self.role_combo = QComboBox()
        roles = [
            {"id": UserRole.ROOT_ADMIN.value, "name": "超级管理员"},
            {"id": UserRole.WECOM_ADMIN.value, "name": "企业管理员"},
            {"id": UserRole.NORMAL.value, "name": "普通用户"}
        ]
        for role in roles:
            self.role_combo.addItem(role["name"], role["id"])
        
        if self.user_data:
            # 根据用户角色值设置下拉框当前值
            role_index = 0  # 默认为普通用户
            user_role = ""
            if isinstance(self.user_data, dict):
                user_role = self.user_data.get('role', '')
            else:
                user_role = getattr(self.user_data, 'role', '')
                
            for i, role in enumerate(roles):
                if role["id"] == user_role:
                    role_index = i
                    break
            self.role_combo.setCurrentIndex(role_index)
            
        WidgetUtils.set_combo_style(self.role_combo)
        layout.addRow("角色:", self.role_combo)
        
        # 企业选择下拉框
        self.corp_combo = QComboBox()
        self.load_corps()
        
        if self.user_data:
            corpname = ""
            corpid = ""
            if isinstance(self.user_data, dict):
                corpname = self.user_data.get('corpname', '')
                corpid = self.user_data.get('corpid', '')
            else:
                corpname = getattr(self.user_data, 'corpname', '')
                corpid = getattr(self.user_data, 'corpid', '')
            
            # 设置当前选中的企业
            for i in range(self.corp_combo.count()):
                if self.corp_combo.itemText(i) == corpname or self.corp_combo.itemData(i) == corpid:
                    self.corp_combo.setCurrentIndex(i)
                    break
                    
        WidgetUtils.set_combo_style(self.corp_combo)
        layout.addRow("所属企业:", self.corp_combo)
        
        # 状态 - 使用is_active
        self.status = QCheckBox("启用")
        if self.user_data:
            is_active = True
            if isinstance(self.user_data, dict):
                is_active = self.user_data.get('is_active', True)
            else:
                is_active = getattr(self.user_data, 'is_active', True)
            self.status.setChecked(is_active)
        else:
            self.status.setChecked(True)
        layout.addRow("状态:", self.status)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.validate_and_accept)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow("", btn_layout)
    
    def load_corps(self):
        """加载企业列表"""
        try:
            self.corp_combo.clear()
            # 添加空选项
            self.corp_combo.addItem("请选择企业", "")
            
            with self.db_manager.get_session() as session:
                corps = session.query(Corp).filter_by(status=True).all()
                
                # 在会话内处理数据
                for corp in corps:
                    self.corp_combo.addItem(corp.name, corp.corp_id)
        except Exception as e:
            logger.error(f"加载企业列表失败: {str(e)}")
    
    def toggle_password_fields(self, state):
        """切换密码字段的启用状态"""
        # 使用Qt.CheckState.Checked替代Qt.Checked
        enabled = state == Qt.CheckState.Checked
        
        # 首先设置密码组的状态
        self.password_group.setEnabled(enabled)
        
        # 直接使用setReadOnly而不是setEnabled来控制输入字段
        # 这比setEnabled更强力，确保用户可以点击和编辑
        self.password_edit.setReadOnly(not enabled)
        self.confirm_password_edit.setReadOnly(not enabled)
        
        # 同时也设置enabled属性
        self.password_edit.setEnabled(enabled)
        self.confirm_password_edit.setEnabled(enabled)
        
        # 如果启用，则清空密码字段
        if enabled:
            self.password_edit.clear()
            self.confirm_password_edit.clear()
            # 给密码字段设置焦点，确保用户可以立即输入
            self.password_edit.setFocus()
        
        # 强制刷新UI状态
        QApplication.processEvents()
        
    def validate_and_accept(self):
        """验证输入并接受"""
        # 验证必填项
        if not self.login_name_edit.text():
            ErrorHandler.handle_warning("登录名不能为空", self)
            return
            
        if not self.name_edit.text():
            ErrorHandler.handle_warning("显示名称不能为空", self)
            return
        
        # 验证密码
        if self.change_password_check.isChecked():
            if not self.password_edit.text():
                ErrorHandler.handle_warning("密码不能为空", self)
                return
                
            if self.password_edit.text() != self.confirm_password_edit.text():
                ErrorHandler.handle_warning("两次输入的密码不一致", self)
                return
                
        # 验证企业选择
        if self.corp_combo.currentData() == "":
            ErrorHandler.handle_warning("请选择所属企业", self)
            return
        
        self.accept()
        
    def get_data(self) -> dict:
        """获取表单数据
        
        Returns:
            表单数据
        """
        data = {
            "login_name": self.login_name_edit.text(),
            "name": self.name_edit.text(),
            "wecom_code": self.wecom_code_edit.text(),
            "role": self.role_combo.currentData(),
            "corpname": self.corp_combo.currentText(),
            "corpid": self.corp_combo.currentData(),
            "is_active": self.status.isChecked()
        }
        
        # 仅在勾选修改密码时才包含密码
        if self.change_password_check.isChecked():
            data["password"] = self.password_edit.text()
            
        return data

class UserManagementPage(QWidget):
    """用户管理页面"""
    
    def __init__(self, db_manager: DatabaseManager, auth_manager=None, user_id=None):
        super().__init__()
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.user_id = user_id
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("userManagementPage")
        
        # 设置主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 设置当前页和每页数量
        self.current_page = 1
        self.page_size = 10
        self.total_pages = 1
        
        # 创建搜索区域
        self.search_layout = QHBoxLayout()
        
        # 登录名搜索
        self.login_name_label = QLabel("登录名:")
        self.search_layout.addWidget(self.login_name_label)
        
        self.login_name_input = QLineEdit()
        self.login_name_input.setPlaceholderText("输入登录名")
        self.login_name_input.setObjectName("searchInput")
        self.login_name_input.returnPressed.connect(self.search)
        self.search_layout.addWidget(self.login_name_input)
        
        # 用户名搜索
        self.name_label = QLabel("用户名:")
        self.search_layout.addWidget(self.name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入用户名")
        self.name_input.setObjectName("searchInput")
        self.name_input.returnPressed.connect(self.search)
        self.search_layout.addWidget(self.name_input)
        
        # 企业名称搜索
        self.corp_name_label = QLabel("企业名称:")
        self.search_layout.addWidget(self.corp_name_label)
        
        self.corp_name_input = QLineEdit()
        self.corp_name_input.setPlaceholderText("输入企业名称")
        self.corp_name_input.setObjectName("searchInput")
        self.corp_name_input.returnPressed.connect(self.search)
        self.search_layout.addWidget(self.corp_name_input)
        
        # 用户角色选择
        self.role_label = QLabel("角色:")
        self.search_layout.addWidget(self.role_label)
        
        self.role_combo = QComboBox()
        self.role_combo.addItem("全部", "")
        self.role_combo.addItem("超级管理员", UserRole.ROOT_ADMIN.value)
        self.role_combo.addItem("企业管理员", UserRole.WECOM_ADMIN.value)
        self.role_combo.addItem("普通用户", UserRole.NORMAL.value)
        self.role_combo.setObjectName("searchCombo")
        WidgetUtils.set_combo_style(self.role_combo)
        self.search_layout.addWidget(self.role_combo)
        
        # 添加搜索按钮
        self.search_btn = QPushButton("搜索")
        self.search_btn.setObjectName("secondaryButton")
        self.search_btn.clicked.connect(self.search)
        self.search_layout.addWidget(self.search_btn)
        
        # 添加重置按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("secondaryButton")
        self.reset_btn.clicked.connect(self.reset_search)
        self.search_layout.addWidget(self.reset_btn)
        
        # 添加弹性空间
        self.search_layout.addStretch()
        
        # 将搜索布局添加到主布局
        self.main_layout.addLayout(self.search_layout)
        
        # 创建工具栏
        self.toolbar = QToolBar()
        self.toolbar.setObjectName("pageToolbar")
        
        # 添加新用户按钮
        self.add_user_btn = QPushButton("添加用户")
        self.add_user_btn.setObjectName("primaryButton")
        self.add_user_btn.clicked.connect(self.add_user)
        self.toolbar.addWidget(self.add_user_btn)
        
        # 添加刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setObjectName("secondaryButton")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.toolbar.addWidget(self.refresh_btn)
        
        # 添加导出按钮
        self.export_btn = QPushButton("导出")
        self.export_btn.setObjectName("secondaryButton")
        self.export_btn.clicked.connect(self.export_data)
        self.toolbar.addWidget(self.export_btn)
        
        # 添加状态过滤下拉框
        self.status_label = QLabel("状态:")
        self.toolbar.addWidget(self.status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.addItem("全部")
        self.status_combo.addItem("活跃")
        self.status_combo.addItem("停用")
        self.status_combo.currentIndexChanged.connect(self.filter_by_status)
        self.toolbar.addWidget(self.status_combo)
        
        # 添加工具栏到主布局
        self.main_layout.addWidget(self.toolbar)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(11)  # 用户ID, 登录名, 显示名, 企业ID, 企业名称, 角色, 状态, 创建时间, 修改时间, 最后登录时间, 操作
        self.table.setHorizontalHeaderLabels([
            "用户ID", "登录名", "显示名", "WeChat ID",
            "企业ID", "企业名称", "角色", "状态", 
            "创建时间", "修改时间", "操作"
        ])
        
        # 设置水平滚动条
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 固定最后一列宽度（操作列）
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
        self.table.setColumnWidth(10, 150)
        
        self.main_layout.addWidget(self.table)
        
        # 创建表格下方的分页控件
        pagination_layout = QHBoxLayout()
        
        # 上一页按钮
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.setObjectName("secondaryButton")
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)
        
        # 页码显示
        self.page_label = QLabel("第 1 页")
        pagination_layout.addWidget(self.page_label)
        
        # 下一页按钮
        self.next_btn = QPushButton("下一页")
        self.next_btn.setObjectName("secondaryButton")
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)
        
        # 添加分页布局到主布局
        self.main_layout.addLayout(pagination_layout)
        
        # 初始化样式
        self.setStyleSheet(StyleManager.get_main_style())
        
        # 加载数据
        self.load_data()
        
    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加用户按钮
        add_btn = QPushButton("添加用户")
        add_btn.setObjectName("primaryButton")
        add_btn.setIcon(QIcon(":/icons/add.png"))
        add_btn.clicked.connect(self.add_user)
        layout.addWidget(add_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setIcon(QIcon(":/icons/refresh.png"))
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
        
        # 导出按钮
        export_btn = QPushButton("导出数据")
        export_btn.setObjectName("secondaryButton")
        export_btn.setIcon(QIcon(":/icons/export.png"))
        export_btn.clicked.connect(self.export_data)
        layout.addWidget(export_btn)
        
        # 添加弹性空间
        layout.addStretch()
        
        return toolbar
        
    def _create_search_group(self) -> QGroupBox:
        """创建搜索区域
        
        Returns:
            搜索区域组控件
        """
        group = QGroupBox("搜索条件")
        layout = QHBoxLayout(group)
        
        # 用户ID
        layout.addWidget(QLabel("用户ID:"))
        self.user_id_field = QLineEdit()
        self.user_id_field.setPlaceholderText("请输入用户ID")
        WidgetUtils.set_input_style(self.user_id_field)
        layout.addWidget(self.user_id_field)
        
        # 登录名
        layout.addWidget(QLabel("登录名:"))
        self.login_name_field = QLineEdit()
        self.login_name_field.setPlaceholderText("请输入登录名")
        WidgetUtils.set_input_style(self.login_name_field)
        layout.addWidget(self.login_name_field)
        
        # 用户名
        layout.addWidget(QLabel("用户名:"))
        self.username = QLineEdit()
        self.username.setPlaceholderText("请输入用户名")
        WidgetUtils.set_input_style(self.username)
        layout.addWidget(self.username)
        
        # 企业微信ID
        layout.addWidget(QLabel("企业微信ID:"))
        self.wecom_code_field = QLineEdit()
        self.wecom_code_field.setPlaceholderText("请输入企业微信ID")
        WidgetUtils.set_input_style(self.wecom_code_field)
        layout.addWidget(self.wecom_code_field)
        
        # 角色
        layout.addWidget(QLabel("角色:"))
        self.role = QComboBox()
        self.role.addItems(["全部", "超级管理员", "企业管理员", "普通用户"])
        WidgetUtils.set_combo_style(self.role)
        layout.addWidget(self.role)
        
        # 状态
        layout.addWidget(QLabel("状态:"))
        self.status = QComboBox()
        self.status.addItems(["全部", "正常", "禁用"])
        WidgetUtils.set_combo_style(self.status)
        layout.addWidget(self.status)
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("secondaryButton")
        search_btn.clicked.connect(self.search)
        layout.addWidget(search_btn)
        
        return group
        
    @PerformanceManager.measure_operation("load_data")
    def load_data(self):
        """加载数据"""
        try:
            # 获取用户列表
            with self.db_manager.get_session() as session:
                query = session.query(User)
                
                # 应用搜索条件 - 根据新的搜索字段过滤
                # 1. 登录名模糊搜索
                if hasattr(self, 'login_name_input') and self.login_name_input.text():
                    query = query.filter(User.login_name.like(f"%{self.login_name_input.text()}%"))
                
                # 2. 用户名模糊搜索
                if hasattr(self, 'name_input') and self.name_input.text():
                    query = query.filter(User.name.like(f"%{self.name_input.text()}%"))
                
                # 3. 企业名称模糊搜索
                if hasattr(self, 'corp_name_input') and self.corp_name_input.text():
                    query = query.filter(User.corpname.like(f"%{self.corp_name_input.text()}%"))
                
                # 4. 用户角色下拉选择
                if hasattr(self, 'role_combo') and self.role_combo.currentData():
                    query = query.filter(User.role == self.role_combo.currentData())
                
                # 5. 用户活跃状态下拉选择
                if hasattr(self, 'status_combo') and self.status_combo.currentText() != "全部":
                    is_active = self.status_combo.currentText() == "活跃"
                    query = query.filter(User.is_active == is_active)
                
                # 计算总页数
                total = query.count()
                self.total_pages = (total + self.page_size - 1) // self.page_size
                
                # 获取当前页数据
                records = query.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
                
                # 在会话范围内准备表格数据
                table_data = []
                for record in records:
                    # 在会话内提取用户数据
                    userid = record.userid
                    login_name = record.login_name if hasattr(record, 'login_name') else record.username
                    name = record.name
                    wecom_code = record.wecom_code if hasattr(record, 'wecom_code') else ""
                    corpname = record.corpname if hasattr(record, 'corpname') else ""
                    role = record.role
                    is_active = record.is_active
                    created_at = record.created_at if hasattr(record, 'created_at') else None
                    updated_at = record.updated_at if hasattr(record, 'updated_at') else None
                    last_login = record.last_login if hasattr(record, 'last_login') else None
                    
                    # 角色文本
                    role_text = {
                        UserRole.ROOT_ADMIN.value: "超级管理员",
                        UserRole.WECOM_ADMIN.value: "企业管理员",
                        UserRole.NORMAL.value: "普通用户"
                    }.get(role, "未知")
                    
                    # 状态文本
                    status_text = "正常" if is_active else "禁用"
                    
                    # 格式化时间
                    created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else ""
                    updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M:%S") if updated_at else ""
                    last_login_str = last_login.strftime("%Y-%m-%d %H:%M:%S") if last_login else ""
                    
                    # 保存用户数据
                    table_data.append({
                        'userid': str(userid),
                        'login_name': login_name,
                        'name': name,
                        'wecom_code': wecom_code,
                        'corpname': corpname,
                        'role_text': role_text,
                        'role': role,
                        'status_text': status_text,
                        'created_at_str': created_at_str,
                        'updated_at_str': updated_at_str,
                        'last_login_str': last_login_str
                    })
            
            # 会话已关闭，使用表格数据更新UI
            self.table.setRowCount(len(table_data))
            for row, data in enumerate(table_data):
                self.table.setItem(row, 0, QTableWidgetItem(data['userid']))
                self.table.setItem(row, 1, QTableWidgetItem(data['login_name']))
                self.table.setItem(row, 2, QTableWidgetItem(data['name']))
                self.table.setItem(row, 3, QTableWidgetItem(data['wecom_code']))
                self.table.setItem(row, 4, QTableWidgetItem(data['corpname']))
                self.table.setItem(row, 5, QTableWidgetItem(data['role_text']))
                self.table.setItem(row, 6, QTableWidgetItem(data['status_text']))
                self.table.setItem(row, 7, QTableWidgetItem(data['created_at_str']))
                self.table.setItem(row, 8, QTableWidgetItem(data['updated_at_str']))
                self.table.setItem(row, 9, QTableWidgetItem(data['last_login_str']))
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                
                # 判断是否为root-admin用户，如果是则不显示编辑和删除按钮
                if data['role'] == UserRole.ROOT_ADMIN.value:
                    info_label = QLabel("系统用户")
                    info_label.setStyleSheet("color: #7f8c8d;")
                    btn_layout.addWidget(info_label)
                else:
                    edit_btn = QPushButton("编辑")
                    edit_btn.setObjectName("linkButton")
                    # 直接设置样式确保按钮可见
                    edit_btn.setStyleSheet("background-color: #f0f0f0; color: #000000; border: 1px solid #cccccc; border-radius: 4px; padding: 4px 12px; min-width: 60px;")
                    
                    # 在按钮点击时重新从数据库获取用户对象
                    user_id = data['userid']
                    edit_btn.clicked.connect(lambda checked, uid=user_id: self._edit_user_by_id(uid))
                    btn_layout.addWidget(edit_btn)
                    
                    delete_btn = QPushButton("删除")
                    delete_btn.setObjectName("linkButton")
                    # 直接设置样式确保按钮可见
                    delete_btn.setStyleSheet("background-color: #f0f0f0; color: #000000; border: 1px solid #cccccc; border-radius: 4px; padding: 4px 12px; min-width: 60px;")
                    delete_btn.clicked.connect(lambda checked, uid=user_id: self._delete_user_by_id(uid))
                    btn_layout.addWidget(delete_btn)
                
                self.table.setCellWidget(row, 10, btn_widget)  # 操作列移到第11列
                
            # 更新分页信息
            self.page_label.setText(f"第 {self.current_page} 页 / 共 {self.total_pages} 页")
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < self.total_pages)
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "加载用户列表失败")
    
    def _edit_user_by_id(self, user_id):
        """通过用户ID编辑用户
        
        Args:
            user_id: 用户ID
        """
        try:
            with self.db_manager.get_session() as session:
                # 使用userid而不是user_id
                user = session.query(User).filter_by(userid=user_id).first()
                if user:
                    # 创建一个不依赖于会话的用户对象副本
                    self.edit_user(user)
                else:
                    ErrorHandler.handle_warning("用户不存在", self)
        except Exception as e:
            ErrorHandler.handle_error(e, self, "编辑用户失败")
    
    def _delete_user_by_id(self, user_id):
        """通过用户ID删除用户
        
        Args:
            user_id: 用户ID
        """
        try:
            with self.db_manager.get_session() as session:
                # 使用userid而不是user_id
                user = session.query(User).filter_by(userid=user_id).first()
                if user:
                    self.delete_user(user)
                else:
                    ErrorHandler.handle_warning("用户不存在", self)
        except Exception as e:
            ErrorHandler.handle_error(e, self, "删除用户失败")
            
    def search(self):
        """搜索"""
        self.current_page = 1
        self.load_data()
        
    def reset_search(self):
        """重置搜索条件"""
        # 清空所有搜索输入框
        self.login_name_input.clear()
        self.name_input.clear()
        self.corp_name_input.clear()
        
        # 重置下拉框
        if hasattr(self, 'role_combo') and self.role_combo.count() > 0:
            self.role_combo.setCurrentIndex(0)  # 设置为"全部"
        if hasattr(self, 'status_combo') and self.status_combo.count() > 0:
            self.status_combo.setCurrentIndex(0)  # 设置为"全部"
        
        # 刷新数据
        self.current_page = 1
        self.load_data()
    
    def filter_by_status(self, index):
        """根据状态筛选用户
        
        Args:
            index: 下拉框索引
        """
        # 根据状态下拉框值筛选用户
        self.current_page = 1  # 重置到第一页
        self.load_data()  # 重新加载数据
        
    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
            
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()
            
    @PerformanceManager.measure_operation("add_user")
    def add_user(self):
        """添加用户"""
        try:
            # 检查权限
            if self.auth_manager and self.user_id:
                with self.db_manager.get_session() as session:
                    if not self.auth_manager.has_permission(self.user_id, "manage_users", session):
                        self.error_handler.handle_warning("您没有权限执行此操作", self)
                        return
            
            # 创建用户对话框
            dialog = UserDialog(self.auth_manager, self.db_manager)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取用户信息
                user_info = dialog.get_data()
                
                # 验证用户名是否已存在
                with self.db_manager.get_session() as session:
                    if session.query(User).filter_by(login_name=user_info["login_name"]).first():
                        ErrorHandler.handle_warning("用户名已存在", self)
                        return
                    
                    # 检查密码是否提供并对其进行哈希处理    
                    if not user_info.get("password"):
                        ErrorHandler.handle_warning("请输入密码", self)
                        return
                    
                    # 设置创建时间
                    from datetime import datetime
                    user_info["created_at"] = datetime.now()
                    
                    # 创建用户并正确设置密码
                    password = user_info.pop("password")  # 取出密码
                    user = User(**user_info)
                    user.set_password(password)  # 使用User类的方法设置密码
                    session.add(user)
                    session.commit()
                    
                ErrorHandler.handle_info("添加用户成功", self, "成功")
                self.load_data()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "添加用户失败")
            
    @PerformanceManager.measure_operation("edit_user")
    def edit_user(self, user: User):
        """编辑用户
        
        Args:
            user: 用户信息
        """
        try:
            # 检查权限
            if self.auth_manager and self.user_id:
                with self.db_manager.get_session() as session:
                    if not self.auth_manager.has_permission(self.user_id, "manage_users", session):
                        self.error_handler.handle_warning("您没有权限执行此操作", self)
                        return
            
            # 创建用户对话框 - 使用用户数据的副本而不是SQLAlchemy对象
            user_data = {
                'login_name': getattr(user, 'login_name', '') or getattr(user, 'username', ''),
                'name': getattr(user, 'name', ''),
                'role': user.role,
                'is_active': user.is_active,
                'corpname': getattr(user, 'corpname', ''),
                'corpid': getattr(user, 'corpid', ''),
                'wecom_code': getattr(user, 'wecom_code', ''),
                'userid': user.userid
            }
            
            dialog = UserDialog(self.auth_manager, self.db_manager, user_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取用户信息
                user_info = dialog.get_data()
                
                # 更新用户信息
                with self.db_manager.get_session() as session:
                    # 获取数据库中的用户，使用合适的ID字段
                    user_id = user_data.get('userid')
                    db_user = session.query(User).filter_by(userid=user_id).first()
                    if not db_user:
                        ErrorHandler.handle_warning("用户不存在", self)
                        return
                    
                    # 如果提供了新密码，则更新密码
                    if "password" in user_info and user_info["password"]:
                        # 使用User类的set_password方法处理密码
                        db_user.set_password(user_info["password"])
                        # 删除处理过的密码项
                        del user_info["password"]
                    
                    # 更新用户字段
                    for key, value in user_info.items():
                        if key != "login_name" and value is not None:  # 不更新登录名
                            setattr(db_user, key, value)
                    
                    # 更新修改时间
                    from datetime import datetime
                    db_user.updated_at = datetime.now()
                    
                    session.commit()
                    
                ErrorHandler.handle_info("编辑用户成功", self, "成功")
                self.load_data()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "编辑用户失败")
            
    @PerformanceManager.measure_operation("delete_user")
    def delete_user(self, user: User):
        """删除用户
        
        Args:
            user: 用户信息
        """
        try:
            # 检查权限
            if self.auth_manager and self.user_id:
                with self.db_manager.get_session() as session:
                    if not self.auth_manager.has_permission(self.user_id, "manage_users", session):
                        self.error_handler.handle_warning("您没有权限执行此操作", self)
                        return
            
            # 确认删除
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除用户 {user.login_name} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 删除用户
                user_id = user.userid
                
                with self.db_manager.get_session() as session:
                    # 找到要删除的用户
                    db_user = session.query(User).filter_by(userid=user_id).first()
                    if not db_user:
                        ErrorHandler.handle_warning("用户不存在", self)
                        return
                    
                    session.delete(db_user)
                    session.commit()
                    
                ErrorHandler.handle_info("删除用户成功", self, "成功")
                self.load_data()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "删除用户失败")
            
    @PerformanceManager.measure_operation("export_data")
    def export_data(self):
        """导出数据"""
        try:
            # 检查权限
            if self.auth_manager and self.user_id:
                with self.db_manager.get_session() as session:
                    if not self.auth_manager.has_permission(self.user_id, "export_data", session):
                        self.error_handler.handle_warning("您没有权限执行此操作", self)
                        return
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存Excel文件",
                "",
                "Excel Files (*.xlsx)"
            )
            if not file_path:
                return
            
            # 获取所有用户记录，并准备导出数据
            user_data = []
            with self.db_manager.get_session() as session:
                users = session.query(User).all()
                
                # 在会话内处理数据
                for user in users:
                    # 角色文本
                    role_text = {
                        UserRole.ROOT_ADMIN.value: "超级管理员",
                        UserRole.WECOM_ADMIN.value: "企业管理员",
                        UserRole.NORMAL.value: "普通用户"
                    }.get(user.role, "未知")
                    
                    # 状态文本
                    status_text = "正常" if user.is_active else "禁用"
                    
                    # 格式化时间
                    created_at_str = user.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(user, 'created_at') and user.created_at else ""
                    updated_at_str = user.updated_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(user, 'updated_at') and user.updated_at else ""
                    last_login_str = user.last_login.strftime("%Y-%m-%d %H:%M:%S") if hasattr(user, 'last_login') and user.last_login else ""
                    
                    user_data.append({
                        "用户ID": user.userid,
                        "登录名": user.login_name if hasattr(user, 'login_name') else "",
                        "用户名": user.name,
                        "企业微信ID": user.wecom_code if hasattr(user, 'wecom_code') else "",
                        "角色": role_text,
                        "状态": status_text,
                        "企业名称": user.corpname if hasattr(user, 'corpname') else "",
                        "企业ID": user.corpid if hasattr(user, 'corpid') else "",
                        "创建时间": created_at_str,
                        "更新时间": updated_at_str,
                        "最后登录": last_login_str
                    })
            
            # 创建DataFrame并导出
            df = pd.DataFrame(user_data)
            df.to_excel(file_path, index=False)
            
            ErrorHandler.handle_info("导出数据成功", self, "成功")
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "导出数据失败")
            
    def refresh_data(self):
        """刷新数据"""
        self.load_data() 