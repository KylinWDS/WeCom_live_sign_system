from PySide6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox,
                             QMessageBox, QGroupBox, QFormLayout, QFileDialog,
                             QSpinBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from utils.logger import get_logger
from utils.error_handler import ErrorHandler
from core.database import DatabaseManager
from models.corp import CorpInfo
from models.user import User, UserRole
import os
import json

logger = get_logger(__name__)

class InitWizard(QWizard):
    """初始化向导"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("系统初始化")
        self.setFixedSize(600, 400)
        
        # 创建欢迎页面
        welcome_page = self.create_welcome_page()
        self.addPage(welcome_page)
        
        # 创建企业信息配置页面
        corp_page = self.create_corp_page()
        self.addPage(corp_page)
        
        # 创建管理员配置页面
        admin_page = self.create_admin_page()
        self.addPage(admin_page)
        
        # 创建系统配置页面
        system_page = self.create_system_page()
        self.addPage(system_page)
        
        # 创建完成页面
        finish_page = self.create_finish_page()
        self.addPage(finish_page)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_main_style())
        
    def create_welcome_page(self) -> QWizardPage:
        """创建欢迎页面"""
        page = QWizardPage()
        page.setTitle("欢迎")
        page.setSubTitle("欢迎使用企业微信直播签到系统")
        
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # 欢迎文本
        welcome_label = QLabel(
            "本向导将帮助您完成系统的初始化配置。\n"
            "请按照向导的提示，依次完成以下配置：\n\n"
            "1. 企业信息配置\n"
            "2. 管理员账号配置\n"
            "3. 系统参数配置"
        )
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        return page
        
    def create_corp_page(self) -> QWizardPage:
        """创建企业信息配置页面"""
        page = QWizardPage()
        page.setTitle("企业信息")
        page.setSubTitle("请配置企业微信相关信息")
        
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # 创建表单
        form_group = QGroupBox("企业信息")
        form_layout = QFormLayout()
        
        # 企业名称
        self.corp_name = QLineEdit()
        WidgetUtils.set_input_style(self.corp_name)
        form_layout.addRow("企业名称:", self.corp_name)
        
        # 企业ID
        self.corp_id = QLineEdit()
        WidgetUtils.set_input_style(self.corp_id)
        form_layout.addRow("企业ID:", self.corp_id)
        
        # 企业应用Secret
        self.corp_secret = QLineEdit()
        self.corp_secret.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.corp_secret)
        form_layout.addRow("企业应用Secret:", self.corp_secret)
        
        # 应用ID
        self.agent_id = QLineEdit()
        WidgetUtils.set_input_style(self.agent_id)
        form_layout.addRow("应用ID:", self.agent_id)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        return page
        
    def create_admin_page(self) -> QWizardPage:
        """创建管理员配置页面"""
        page = QWizardPage()
        page.setTitle("管理员配置")
        page.setSubTitle("请配置超级管理员账号")
        
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # 创建表单
        form_group = QGroupBox("管理员信息")
        form_layout = QFormLayout()
        
        # 用户名
        self.admin_username = QLineEdit()
        WidgetUtils.set_input_style(self.admin_username)
        form_layout.addRow("用户名:", self.admin_username)
        
        # 密码
        self.admin_password = QLineEdit()
        self.admin_password.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.admin_password)
        form_layout.addRow("密码:", self.admin_password)
        
        # 确认密码
        self.admin_confirm = QLineEdit()
        self.admin_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.admin_confirm)
        form_layout.addRow("确认密码:", self.admin_confirm)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        return page
        
    def create_system_page(self) -> QWizardPage:
        """创建系统配置页面"""
        page = QWizardPage()
        page.setTitle("系统配置")
        page.setSubTitle("请配置系统参数")
        
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # 创建表单
        form_group = QGroupBox("系统参数")
        form_layout = QFormLayout()
        
        # 数据库路径
        db_layout = QHBoxLayout()
        self.db_path = QLineEdit()
        WidgetUtils.set_input_style(self.db_path)
        db_layout.addWidget(self.db_path)
        
        # 浏览按钮
        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.clicked.connect(self.browse_db_path)
        db_layout.addWidget(browse_btn)
        
        form_layout.addRow("数据库路径:", db_layout)
        
        # 日志路径
        log_layout = QHBoxLayout()
        self.log_path = QLineEdit()
        WidgetUtils.set_input_style(self.log_path)
        log_layout.addWidget(self.log_path)
        
        # 浏览按钮
        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.clicked.connect(self.browse_log_path)
        log_layout.addWidget(browse_btn)
        
        form_layout.addRow("日志路径:", log_layout)
        
        # 日志级别
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        WidgetUtils.set_combo_style(self.log_level)
        form_layout.addRow("日志级别:", self.log_level)
        
        # 日志保留天数
        self.log_retention = QSpinBox()
        self.log_retention.setValue(30)
        self.log_retention.setSuffix(" 天")
        WidgetUtils.set_spin_style(self.log_retention)
        form_layout.addRow("日志保留天数:", self.log_retention)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        return page
        
    def create_finish_page(self) -> QWizardPage:
        """创建完成页面"""
        page = QWizardPage()
        page.setTitle("完成")
        page.setSubTitle("系统初始化完成")
        
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # 完成文本
        finish_label = QLabel(
            "系统初始化已完成。\n"
            "请点击"完成"按钮保存配置并启动系统。"
        )
        finish_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(finish_label)
        
        return page
        
    def browse_db_path(self):
        """浏览数据库路径"""
        path = QFileDialog.getExistingDirectory(
            self,
            "选择数据库目录",
            os.path.expanduser("~")
        )
        if path:
            self.db_path.setText(path)
            
    def browse_log_path(self):
        """浏览日志路径"""
        path = QFileDialog.getExistingDirectory(
            self,
            "选择日志目录",
            os.path.expanduser("~")
        )
        if path:
            self.log_path.setText(path)
            
    def validateCurrentPage(self) -> bool:
        """验证当前页面"""
        current_page = self.currentPage()
        
        if current_page == self.page(1):  # 企业信息页面
            if not self.corp_name.text():
                ErrorHandler.handle_error("请输入企业名称", self, "错误")
                return False
                
            if not self.corp_id.text():
                ErrorHandler.handle_error("请输入企业ID", self, "错误")
                return False
                
            if not self.corp_secret.text():
                ErrorHandler.handle_error("请输入企业应用Secret", self, "错误")
                return False
                
            if not self.agent_id.text():
                ErrorHandler.handle_error("请输入应用ID", self, "错误")
                return False
                
        elif current_page == self.page(2):  # 管理员配置页面
            if not self.admin_username.text():
                ErrorHandler.handle_error("请输入用户名", self, "错误")
                return False
                
            if not self.admin_password.text():
                ErrorHandler.handle_error("请输入密码", self, "错误")
                return False
                
            if not self.admin_confirm.text():
                ErrorHandler.handle_error("请确认密码", self, "错误")
                return False
                
            if self.admin_password.text() != self.admin_confirm.text():
                ErrorHandler.handle_error("两次输入的密码不一致", self, "错误")
                return False
                
        elif current_page == self.page(3):  # 系统配置页面
            if not self.db_path.text():
                ErrorHandler.handle_error("请选择数据库路径", self, "错误")
                return False
                
            if not self.log_path.text():
                ErrorHandler.handle_error("请选择日志路径", self, "错误")
                return False
                
        return True
        
    def accept(self):
        """保存配置"""
        try:
            # 保存企业信息
            corp_info = CorpInfo(
                corp_name=self.corp_name.text(),
                corp_id=self.corp_id.text(),
                corp_secret=self.corp_secret.text(),
                agent_id=self.agent_id.text()
            )
            
            # 保存管理员账号
            admin = User(
                username=self.admin_username.text(),
                password=self.admin_password.text(),  # TODO: 加密密码
                role=UserRole.ADMIN
            )
            
            # 保存系统配置
            settings = {
                "db_path": self.db_path.text(),
                "log_path": self.log_path.text(),
                "log_level": self.log_level.currentText(),
                "log_retention": self.log_retention.value()
            }
            
            # 写入数据库
            with self.db_manager.get_session() as session:
                session.add(corp_info)
                session.add(admin)
                session.commit()
                
            # 保存系统配置
            config_path = os.path.join(os.path.dirname(self.db_path.text()), "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
                
            super().accept()
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存配置失败") 