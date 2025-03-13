from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from core.auth_manager import AuthManager
from utils.logger import get_logger
from ..managers.animation import AnimationManager
from utils.performance_manager import PerformanceManager
from utils.error_handler import ErrorHandler
from core.database import DatabaseManager
from models.user import User
import pandas as pd
import os

logger = get_logger(__name__)

class UserDialog(QDialog):
    """用户编辑对话框"""
    
    def __init__(self, auth_manager: AuthManager, user_data: dict = None, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.user_data = user_data
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑用户" if self.user_data else "添加用户")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        layout.setSpacing(10)
        
        # 用户名
        self.username_edit = QLineEdit()
        if self.user_data:
            self.username_edit.setText(self.user_data["username"])
            self.username_edit.setEnabled(False)  # 用户名不可修改
        WidgetUtils.set_input_style(self.username_edit)
        layout.addRow("用户名:", self.username_edit)
        
        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.password_edit)
        layout.addRow("密码:", self.password_edit)
        
        # 确认密码
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.confirm_password_edit)
        layout.addRow("确认密码:", self.confirm_password_edit)
        
        # 角色
        self.role_combo = QComboBox()
        roles = self.auth_manager.get_all_roles()
        for role in roles:
            self.role_combo.addItem(role["name"], role["id"])
        if self.user_data:
            self.role_combo.setCurrentText(roles[0]["name"])  # 默认选择第一个角色
        WidgetUtils.set_combo_style(self.role_combo)
        layout.addRow("角色:", self.role_combo)
        
        # 状态
        self.status = QCheckBox("启用")
        self.status.setChecked(True)
        layout.addRow("状态:", self.status)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow("", btn_layout)
        
    def get_data(self) -> dict:
        """获取表单数据
        
        Returns:
            表单数据
        """
        return {
            "username": self.username_edit.text(),
            "password": self.password_edit.text(),
            "confirm_password": self.confirm_password_edit.text(),
            "role": self.role_combo.currentData(),
            "status": self.status.isChecked()
        }

class UserManagementPage(QWidget):
    """用户管理页面"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("userManagementPage")
        
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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "用户ID", "用户名", "角色", "状态", "创建时间", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        WidgetUtils.set_table_style(self.table)
        layout.addWidget(self.table)
        
        # 创建分页区域
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
        
        layout.addLayout(pagination_layout)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_user_management_style())
        
        # 添加淡入动画
        AnimationManager.fade_in(self)
        
        # 加载数据
        self.current_page = 1
        self.page_size = 10
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
        """创建搜索区域"""
        group = QGroupBox("搜索条件")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 第一行
        row1_layout = QHBoxLayout()
        
        # 用户ID
        row1_layout.addWidget(QLabel("用户ID:"))
        self.user_id = QLineEdit()
        WidgetUtils.set_input_style(self.user_id)
        row1_layout.addWidget(self.user_id)
        
        # 用户名
        row1_layout.addWidget(QLabel("用户名:"))
        self.username = QLineEdit()
        WidgetUtils.set_input_style(self.username)
        row1_layout.addWidget(self.username)
        
        layout.addLayout(row1_layout)
        
        # 第二行
        row2_layout = QHBoxLayout()
        
        # 角色
        row2_layout.addWidget(QLabel("角色:"))
        self.role = QComboBox()
        self.role.addItems(["全部", "超级管理员", "企业管理员", "普通用户"])
        WidgetUtils.set_combo_style(self.role)
        row2_layout.addWidget(self.role)
        
        # 状态
        row2_layout.addWidget(QLabel("状态:"))
        self.status = QComboBox()
        self.status.addItems(["全部", "正常", "禁用"])
        WidgetUtils.set_combo_style(self.status)
        row2_layout.addWidget(self.status)
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("primaryButton")
        search_btn.clicked.connect(self.search)
        row2_layout.addWidget(search_btn)
        
        layout.addLayout(row2_layout)
        
        return group
        
    @PerformanceManager.measure_operation("load_data")
    def load_data(self):
        """加载数据"""
        try:
            # 获取用户列表
            with self.db_manager.get_session() as session:
                query = session.query(User)
                
                # 应用搜索条件
                if self.user_id.text():
                    query = query.filter_by(user_id=self.user_id.text())
                    
                if self.username.text():
                    query = query.filter(User.username.like(f"%{self.username.text()}%"))
                    
                if self.role.currentText() != "全部":
                    role_map = {
                        "超级管理员": "root-admin",
                        "企业管理员": "corp-admin",
                        "普通用户": "user"
                    }
                    query = query.filter_by(role=role_map[self.role.currentText()])
                    
                if self.status.currentText() != "全部":
                    status_map = {
                        "正常": 1,
                        "禁用": 0
                    }
                    query = query.filter_by(status=status_map[self.status.currentText()])
                    
                # 计算总页数
                total = query.count()
                self.total_pages = (total + self.page_size - 1) // self.page_size
                
                # 获取当前页数据
                records = query.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
                
            # 更新表格
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(record.user_id))
                self.table.setItem(row, 1, QTableWidgetItem(record.username))
                
                # 角色
                role_text = {
                    "root-admin": "超级管理员",
                    "corp-admin": "企业管理员",
                    "user": "普通用户"
                }.get(record.role, "未知")
                self.table.setItem(row, 2, QTableWidgetItem(role_text))
                
                # 状态
                status_text = "正常" if record.status else "禁用"
                self.table.setItem(row, 3, QTableWidgetItem(status_text))
                
                # 创建时间
                self.table.setItem(row, 4, QTableWidgetItem(record.create_time.strftime("%Y-%m-%d %H:%M:%S")))
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                
                edit_btn = QPushButton("编辑")
                edit_btn.setObjectName("linkButton")
                edit_btn.clicked.connect(lambda checked, r=record: self.edit_user(r))
                btn_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("删除")
                delete_btn.setObjectName("linkButton")
                delete_btn.clicked.connect(lambda checked, r=record: self.delete_user(r))
                btn_layout.addWidget(delete_btn)
                
                self.table.setCellWidget(row, 5, btn_widget)
                
            # 更新分页信息
            self.page_label.setText(f"第 {self.current_page} 页 / 共 {self.total_pages} 页")
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < self.total_pages)
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "加载用户列表失败")
            
    def search(self):
        """搜索"""
        self.current_page = 1
        self.load_data()
        
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
            # 创建用户对话框
            dialog = UserDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取用户信息
                user_info = dialog.get_data()
                
                # 验证用户ID是否已存在
                with self.db_manager.get_session() as session:
                    if session.query(User).filter_by(user_id=user_info["user_id"]).first():
                        ErrorHandler.handle_warning("用户ID已存在", self)
                        return
                        
                    # 创建用户
                    user = User(**user_info)
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
            # 创建用户对话框
            dialog = UserDialog(self, user)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取用户信息
                user_info = dialog.get_data()
                
                # 更新用户信息
                with self.db_manager.get_session() as session:
                    session.query(User).filter_by(user_id=user.user_id).update(user_info)
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
            # 确认删除
            if not ErrorHandler.handle_question(
                "确定要删除该用户吗？",
                self,
                "确认删除"
            ):
                return
                
            # 删除用户
            with self.db_manager.get_session() as session:
                session.query(User).filter_by(user_id=user.user_id).delete()
                session.commit()
                
            ErrorHandler.handle_info("删除用户成功", self, "成功")
            self.load_data()
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "删除用户失败")
            
    @PerformanceManager.measure_operation("export_data")
    def export_data(self):
        """导出数据"""
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存Excel文件",
                "",
                "Excel Files (*.xlsx)"
            )
            if not file_path:
                return
                
            # 获取所有用户记录
            with self.db_manager.get_session() as session:
                records = session.query(User).all()
                
            # 创建DataFrame
            data = []
            for record in records:
                data.append({
                    "用户ID": record.user_id,
                    "用户名": record.username,
                    "角色": {
                        "root-admin": "超级管理员",
                        "corp-admin": "企业管理员",
                        "user": "普通用户"
                    }.get(record.role, "未知"),
                    "状态": "正常" if record.status else "禁用",
                    "创建时间": record.create_time.strftime("%Y-%m-%d %H:%M:%S")
                })
            df = pd.DataFrame(data)
            
            # 导出到Excel
            df.to_excel(file_path, index=False)
            
            ErrorHandler.handle_info("导出数据成功", self, "成功")
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "导出数据失败")
            
    def refresh_data(self):
        """刷新数据"""
        self.load_data() 