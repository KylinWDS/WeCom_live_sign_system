# PySide6导入
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QMessageBox,
                             QCheckBox, QGroupBox, QFormLayout)
from PySide6.QtCore import Qt

# UI相关导入
from .base_dialog import BaseDialog
from src.ui.managers.style import StyleManager
from src.ui.utils.widget_utils import WidgetUtils

# 核心功能导入
from src.core.database import DatabaseManager
from src.models.user import User, UserRole
from src.utils.token_manager import TokenManager

# 工具类导入
from src.utils.logger import get_logger

logger = get_logger(__name__)

class UserDialog(BaseDialog):
    """用户对话框"""
    
    def __init__(self, parent=None, user: User = None):
        super().__init__(parent, "用户信息", 400, 500)
        self.user = user
        
        # 用户名
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("用户名:"))
        self.username = QLineEdit()
        if self.user:  # 编辑模式下用户名不可修改
            self.username.setEnabled(False)
        username_layout.addWidget(self.username)
        self.content_layout.addLayout(username_layout)
        
        # 密码
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("密码:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        if self.user:  # 编辑模式下密码为空表示不修改
            self.password.setPlaceholderText("留空表示不修改")
        password_layout.addWidget(self.password)
        self.content_layout.addLayout(password_layout)
        
        # 确认密码
        confirm_password_layout = QHBoxLayout()
        confirm_password_layout.addWidget(QLabel("确认密码:"))
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_password_layout.addWidget(self.confirm_password)
        self.content_layout.addLayout(confirm_password_layout)
        
        # 角色
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel("角色:"))
        self.role = QComboBox()
        self.role.addItems(["超级管理员", "企业微信管理员", "普通用户"])
        role_layout.addWidget(self.role)
        self.content_layout.addLayout(role_layout)
        
        # 企业微信配置（仅对企业微信管理员显示）
        self.wecom_group = QGroupBox("企业微信配置")
        wecom_layout = QFormLayout()
        
        self.corpname = QLineEdit()
        self.corpid = QLineEdit()
        self.corpsecret = QLineEdit()
        self.corpsecret.setEchoMode(QLineEdit.EchoMode.Password)
        self.agentid = QLineEdit()
        
        wecom_layout.addRow("企业名称:", self.corpname)
        wecom_layout.addRow("企业ID:", self.corpid)
        wecom_layout.addRow("应用Secret:", self.corpsecret)
        wecom_layout.addRow("应用ID:", self.agentid)
        
        self.wecom_group.setLayout(wecom_layout)
        self.wecom_group.setVisible(False)
        self.content_layout.addWidget(self.wecom_group)
        
        # 状态
        status_layout = QHBoxLayout()
        self.is_active = QCheckBox("启用")
        self.is_active.setChecked(True)
        status_layout.addWidget(self.is_active)
        self.content_layout.addLayout(status_layout)
        
        # 添加隐私声明
        privacy_notice = QLabel(
            "隐私声明：您的个人信息仅用于系统内部管理，不会向第三方提供或泄露。"
        )
        privacy_notice.setWordWrap(True)
        privacy_notice.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                margin-top: 10px;
                padding: 8px;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
        """)
        self.content_layout.addWidget(privacy_notice)
        
        # 连接角色选择信号
        self.role.currentIndexChanged.connect(self._on_role_changed)
        
        # 加载用户数据
        if user:
            self.load_user_data()
            
        # 重写确定按钮点击事件
        self.ok_button.clicked.disconnect()
        self.ok_button.clicked.connect(self.accept)
    
    def _on_role_changed(self, index: int):
        """角色改变处理"""
        is_wecom_admin = index == 1  # 企业微信管理员
        self.wecom_group.setVisible(is_wecom_admin)
    
    def load_user_data(self):
        """加载用户数据"""
        self.username.setText(self.user.username)
        # 根据用户角色设置下拉框选项
        role_index = {
            UserRole.ROOT_ADMIN.value: 0,
            UserRole.WECOM_ADMIN.value: 1,
            UserRole.NORMAL.value: 2
        }.get(self.user.role, 2)  # 默认为普通用户
        self.role.setCurrentIndex(role_index)
        self.is_active.setChecked(self.user.is_active)
        
        # 如果是企业微信管理员，加载企业微信配置
        if self.user.role == UserRole.WECOM_ADMIN.value:
            self.corpname.setText(self.user.corpname)
            self.corpid.setText(self.user.corpid)
            self.corpsecret.setText(self.user.corpsecret)
            self.agentid.setText(self.user.agentid)
            self.wecom_group.setVisible(True)
    
    def get_user_data(self) -> dict:
        """获取用户数据"""
        role_map = {
            0: UserRole.ROOT_ADMIN.value,
            1: UserRole.WECOM_ADMIN.value,
            2: UserRole.NORMAL.value
        }
        data = {
            "username": self.username.text(),
            "password": self.password.text(),
            "role": role_map[self.role.currentIndex()],
            "is_active": self.is_active.isChecked()
        }
        
        # 如果是企业微信管理员，添加企业微信配置
        if self.role.currentIndex() == 1:
            data.update({
                "corpname": self.corpname.text(),
                "corpid": self.corpid.text(),
                "corpsecret": self.corpsecret.text(),
                "agentid": self.agentid.text()
            })
        
        return data
    
    def validate(self) -> bool:
        """验证输入"""
        if not self.username.text():
            QMessageBox.warning(self, "警告", "请输入用户名")
            return False
        
        if not self.user and not self.password.text():
            QMessageBox.warning(self, "警告", "请输入密码")
            return False
        
        if not self.user and self.password.text() != self.confirm_password.text():
            QMessageBox.warning(self, "警告", "两次输入的密码不一致")
            return False
        
        return True
    
    def accept(self):
        """确认"""
        if self.validate():
            try:
                # 验证企业微信接口
                if self.role.currentIndex() == 1:
                    token_manager = TokenManager()
                    token_manager.set_credentials(self.corpid.text(), self.corpsecret.text())
                    token = token_manager.get_token()
                    
                    if not token:
                        QMessageBox.warning(self, "警告", "企业微信接口验证失败，请检查企业信息是否正确")
                        return
                        
                super().accept()
                
            except Exception as e:
                logger.error(f"保存用户信息失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"保存用户信息失败: {str(e)}")
    
    def reject(self):
        """取消"""
        super().reject() 