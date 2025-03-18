# PySide6导入
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox,
                             QToolButton, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

# UI相关导入
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from ..managers.animation import AnimationManager
from .main_window import MainWindow

# 核心功能导入
from core.config_manager import ConfigManager
from core.database import DatabaseManager
from core.auth_manager import AuthManager

# 工具类导入
from utils.logger import get_logger

logger = get_logger(__name__)

class LoginWindow(QMainWindow):
    """登录窗口"""
    
    def __init__(self, auth_manager: AuthManager, config_manager: ConfigManager, db_manager: DatabaseManager):
        super().__init__()
        self.auth_manager = auth_manager
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.main_window = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("企业微信直播签到系统")
        self.setFixedSize(400, 500)
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title_label = QLabel("企业微信直播签到系统")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # 用户名
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.textChanged.connect(self.on_username_changed)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_edit)
        layout.addLayout(username_layout)
        
        # 密码
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_edit)
        layout.addLayout(password_layout)
        
        # 企业选择
        corp_layout = QHBoxLayout()
        corp_label = QLabel("企业名称:")
        self.corp_combo = QComboBox()
        self.corp_combo.setEditable(True)
        self.corp_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.corp_combo.currentTextChanged.connect(self.on_corp_changed)
        corp_layout.addWidget(corp_label)
        corp_layout.addWidget(self.corp_combo)
        layout.addLayout(corp_layout)
        
        # 企业信息
        self.corp_info = QLabel()
        self.corp_info.setWordWrap(True)
        self.corp_info.setStyleSheet("color: #666666;")
        layout.addWidget(self.corp_info)
        
        # 登录按钮
        self.login_btn = QPushButton("登录")
        self.login_btn.clicked.connect(self.on_login)
        layout.addWidget(self.login_btn)
        
        # 免责声明
        disclaimer = QLabel(
            "免责声明：本软件仅供个人测试使用，请勿用于商业用途。"
            "使用本软件即表示您同意遵守相关法律法规。"
        )
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet("color: #999999; font-size: 12px;")
        layout.addWidget(disclaimer)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_login_style())
        
        # 加载企业列表
        self.load_corp_list()
    
    def load_corp_list(self):
        """加载企业列表"""
        try:
            corporations = self.config_manager.get_corporations()
            self.corp_combo.clear()
            for corp in corporations:
                self.corp_combo.addItem(corp["name"])
            
            # 如果有企业，显示第一个企业的信息
            if corporations:
                self.on_corp_changed(corporations[0]["name"])
        except Exception as e:
            logger.error(f"加载企业列表失败: {str(e)}")
            QMessageBox.warning(self, "警告", "加载企业列表失败")
    
    def on_username_changed(self, text: str):
        """用户名输入变化事件"""
        # 如果是root-admin，禁用企业选择
        if text.strip().lower() == "root-admin":
            self.corp_combo.setEnabled(False)
            self.corp_combo.setCurrentText("")
            self.corp_info.setText("超级管理员无需选择企业")
        else:
            self.corp_combo.setEnabled(True)
            # 恢复企业信息显示
            corp_name = self.corp_combo.currentText()
            if corp_name:
                self.on_corp_changed(corp_name)
    
    def on_corp_changed(self, corpname: str):
        """企业选择改变"""
        try:
            # 如果是root-admin，不显示企业信息
            if self.username_edit.text().strip().lower() == "root-admin":
                self.corp_info.setText("超级管理员无需选择企业")
                return
                
            corp = self.config_manager.get_corporation(corpname)
            if corp:
                info_text = f"企业ID: {corp['corpid']}\n"
                info_text += f"应用ID: {corp['agentid']}\n"
                info_text += f"状态: {'启用' if corp['status'] else '禁用'}"
                self.corp_info.setText(info_text)
            else:
                self.corp_info.setText("")
        except Exception as e:
            logger.error(f"更新企业信息失败: {str(e)}")
            self.corp_info.setText("")
    
    def on_login(self):
        """登录按钮点击"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "警告", "请输入用户名和密码")
            return
        
        # 如果是root-admin，不需要验证企业
        if username.lower() == "root-admin":
            corpname = None
        else:
            corpname = self.corp_combo.currentText().strip()
            if not corpname:
                QMessageBox.warning(self, "警告", "请选择或输入企业名称")
                return
        
        try:
            success, message = self.auth_manager.login(username, password, corpname)
            if success:
                logger.info(f"用户 {username} 登录成功")
                # 创建主窗口
                self.main_window = MainWindow(
                    {"userid": username},  # 传递用户信息
                    self.config_manager,
                    self.db_manager,
                    self.auth_manager
                )
                self.main_window.show()
                self.close()
            else:
                QMessageBox.warning(self, "错误", message)
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            QMessageBox.critical(self, "错误", "登录失败，请稍后重试") 