# PySide6导入
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QSize

# 类型提示导入
from typing import Optional, Callable

class BaseDialog(QDialog):
    """对话框基类"""
    
    def __init__(self, parent=None, title: str = "", width: int = 400, height: int = 300):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)
        
        # 创建内容布局
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self.main_layout.addLayout(self.content_layout)
        
        # 创建按钮布局
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        self.main_layout.addLayout(self.button_layout)
        
        # 添加确定和取消按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.setFixedSize(80, 30)
        self.ok_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFixedSize(80, 30)
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)
        
    def add_content(self, widget):
        """添加内容到对话框"""
        self.content_layout.addWidget(widget)
        
    def add_button(self, text: str, callback: Callable, is_primary: bool = False):
        """添加自定义按钮
        
        Args:
            text: 按钮文本
            callback: 回调函数
            is_primary: 是否为主要按钮
        """
        button = QPushButton(text)
        button.setFixedSize(80, 30)
        button.clicked.connect(callback)
        if is_primary:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #1890ff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #40a9ff;
                }
            """)
        self.button_layout.addWidget(button)
        return button
        
    def set_ok_button_text(self, text: str):
        """设置确定按钮文本"""
        self.ok_button.setText(text)
        
    def set_cancel_button_text(self, text: str):
        """设置取消按钮文本"""
        self.cancel_button.setText(text)
        
    def set_ok_button_enabled(self, enabled: bool):
        """设置确定按钮是否可用"""
        self.ok_button.setEnabled(enabled)
        
    def set_cancel_button_enabled(self, enabled: bool):
        """设置取消按钮是否可用"""
        self.cancel_button.setEnabled(enabled)
        
    def set_ok_button_visible(self, visible: bool):
        """设置确定按钮是否可见"""
        self.ok_button.setVisible(visible)
        
    def set_cancel_button_visible(self, visible: bool):
        """设置取消按钮是否可见"""
        self.cancel_button.setVisible(visible) 