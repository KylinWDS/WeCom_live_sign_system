from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from utils.logger import get_logger
from utils.error_handler import ErrorHandler
from core.database import DatabaseManager
from models.user import User

logger = get_logger(__name__)

class AdminResetDialog(QDialog):
    """管理员重置密码对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("重置管理员密码")
        self.setFixedSize(400, 300)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 创建表单
        form_layout = QVBoxLayout()
        
        # 管理员Token
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("管理员Token:"))
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.token_input)
        token_layout.addWidget(self.token_input)
        form_layout.addLayout(token_layout)
        
        # 验证码
        captcha_layout = QHBoxLayout()
        captcha_layout.addWidget(QLabel("验证码:"))
        self.captcha_input = QLineEdit()
        WidgetUtils.set_input_style(self.captcha_input)
        captcha_layout.addWidget(self.captcha_input)
        
        # 刷新验证码按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.clicked.connect(self.refresh_captcha)
        captcha_layout.addWidget(refresh_btn)
        
        form_layout.addLayout(captcha_layout)
        
        # 新密码
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("新密码:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.password_input)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        # 确认密码
        confirm_layout = QHBoxLayout()
        confirm_layout.addWidget(QLabel("确认密码:"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.confirm_input)
        confirm_layout.addWidget(self.confirm_input)
        form_layout.addLayout(confirm_layout)
        
        layout.addLayout(form_layout)
        
        # 创建按钮
        button_layout = QHBoxLayout()
        
        # 重置按钮
        reset_btn = QPushButton("重置")
        reset_btn.setObjectName("primaryButton")
        reset_btn.clicked.connect(self.reset_password)
        button_layout.addWidget(reset_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_main_style())
        
        # 刷新验证码
        self.refresh_captcha()
        
    def refresh_captcha(self):
        """刷新验证码"""
        # TODO: 实现验证码刷新
        pass
        
    def check_password_strength(self, password: str) -> bool:
        """检查密码强度
        
        Args:
            password: 密码
            
        Returns:
            是否满足强度要求
        """
        # 密码长度至少8位
        if len(password) < 8:
            return False
            
        # 必须包含数字和字母
        has_digit = any(c.isdigit() for c in password)
        has_letter = any(c.isalpha() for c in password)
        
        return has_digit and has_letter
        
    def reset_password(self):
        """重置密码"""
        try:
            # 获取输入
            token = self.token_input.text()
            captcha = self.captcha_input.text()
            password = self.password_input.text()
            confirm = self.confirm_input.text()
            
            # 验证输入
            if not token:
                ErrorHandler.handle_error("请输入管理员Token", self, "错误")
                return
                
            if not captcha:
                ErrorHandler.handle_error("请输入验证码", self, "错误")
                return
                
            if not password:
                ErrorHandler.handle_error("请输入新密码", self, "错误")
                return
                
            if not confirm:
                ErrorHandler.handle_error("请确认新密码", self, "错误")
                return
                
            if password != confirm:
                ErrorHandler.handle_error("两次输入的密码不一致", self, "错误")
                return
                
            if not self.check_password_strength(password):
                ErrorHandler.handle_error("密码强度不足", self, "错误")
                return
                
            # TODO: 验证Token和验证码
            
            # 重置密码
            with self.db_manager.get_session() as session:
                admin = session.query(User).filter_by(role="admin").first()
                if not admin:
                    ErrorHandler.handle_error("未找到管理员用户", self, "错误")
                    return
                    
                admin.password = password  # TODO: 加密密码
                session.commit()
                
            ErrorHandler.handle_info("密码重置成功", self, "成功")
            self.accept()
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "重置密码失败") 