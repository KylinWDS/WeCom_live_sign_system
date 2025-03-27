from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QWidget, QFormLayout)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon
from datetime import datetime, timedelta
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LiveCreateSuccessDialog(QDialog):
    """创建直播成功提示对话框"""
    
    # 定义信号
    navigate_to_list = Signal()  # 导航到直播列表信号
    
    def __init__(self, live_info, parent=None):
        super().__init__(parent)
        self.live_info = live_info
        self.countdown = 10  # 倒计时秒数
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("创建成功")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 成功消息
        message_label = QLabel("直播预约创建成功！")
        message_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #52c41a; 
            margin: 15px 0;
        """)
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)
        
        # 分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #f0f0f0;")
        layout.addWidget(separator)
        
        # 直播信息
        info_widget = QWidget()
        info_layout = QFormLayout(info_widget)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(10, 10, 10, 10)
        
        info_layout.addRow("<b>直播ID:</b>", QLabel(self.live_info.get("livingid", "")))
        info_layout.addRow("<b>直播标题:</b>", QLabel(self.live_info.get("theme", "")))
        
        # 时间格式化
        living_start = datetime.fromtimestamp(self.live_info.get("living_start", 0))
        living_end = living_start + timedelta(seconds=self.live_info.get("living_duration", 0))
        
        info_layout.addRow("<b>开始时间:</b>", QLabel(living_start.strftime("%Y-%m-%d %H:%M:%S")))
        info_layout.addRow("<b>结束时间:</b>", QLabel(living_end.strftime("%Y-%m-%d %H:%M:%S")))
        info_layout.addRow("<b>直播时长:</b>", QLabel(f"{self.live_info.get('living_duration', 0)}秒"))
        info_layout.addRow("<b>主播:</b>", QLabel(self.live_info.get("anchor_userid", "")))
        
        layout.addWidget(info_widget)
        
        # 分隔线
        separator2 = QWidget()
        separator2.setFixedHeight(1)
        separator2.setStyleSheet("background-color: #f0f0f0;")
        layout.addWidget(separator2)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 跳转直播列表按钮
        self.goto_btn = QPushButton(f"跳转直播列表({self.countdown}s)")
        self.goto_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
        """)
        self.goto_btn.clicked.connect(self.on_goto_clicked)
        button_layout.addWidget(self.goto_btn)
        
        # 继续预约直播按钮
        continue_btn = QPushButton("继续预约直播")
        continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #1890ff;
                border: 1px solid #1890ff;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 130px;
            }
            QPushButton:hover {
                background-color: #e6f7ff;
            }
            QPushButton:pressed {
                background-color: #cce5ff;
            }
        """)
        continue_btn.clicked.connect(self.reject)
        button_layout.addWidget(continue_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #666666;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
            QPushButton:pressed {
                background-color: #e6e6e6;
            }
        """)
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 启动定时器
        self.timer.start(1000)  # 每秒更新一次
        
    def update_countdown(self):
        """更新倒计时"""
        self.countdown -= 1
        if self.countdown <= 0:
            self.timer.stop()
            self.on_goto_clicked()  # 倒计时结束，执行跳转
        else:
            self.goto_btn.setText(f"跳转直播列表({self.countdown}s)")
    
    def on_goto_clicked(self):
        """点击跳转按钮或倒计时结束时的处理"""
        self.timer.stop()
        self.navigate_to_list.emit()  # 发送导航信号
        self.accept()
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self.timer.stop()
        super().closeEvent(event) 