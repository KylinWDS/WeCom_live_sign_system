from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.ui.managers.style import StyleManager
from src.ui.utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from src.ui.managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.core.database import DatabaseManager
from src.models.live import Live
from src.ui.components.dialogs.io_dialog import IODialog
import pandas as pd
import os

logger = get_logger(__name__)

class HomePage(QWidget):
    """首页"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("homePage")
        
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
            "直播ID", "直播标题", "直播时间", "直播状态",
            "观看人数", "签到人数", "操作"
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
        
    def _create_search_group(self) -> QGroupBox:
        """创建搜索区域"""
        group = QGroupBox("搜索条件")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 第一行
        row1_layout = QHBoxLayout()
        
        # 直播标题
        row1_layout.addWidget(QLabel("直播标题:"))
        self.live_title = QLineEdit()
        WidgetUtils.set_input_style(self.live_title)
        row1_layout.addWidget(self.live_title)
        
        # 直播状态
        row1_layout.addWidget(QLabel("直播状态:"))
        self.live_status = QComboBox()
        self.live_status.addItems(["全部", "未开始", "进行中", "已结束"])
        WidgetUtils.set_combo_style(self.live_status)
        row1_layout.addWidget(self.live_status)
        
        layout.addLayout(row1_layout)
        
        # 第二行
        row2_layout = QHBoxLayout()
        
        # 直播时间
        row2_layout.addWidget(QLabel("直播时间:"))
        self.live_time = QLineEdit()
        WidgetUtils.set_input_style(self.live_time)
        row2_layout.addWidget(self.live_time)
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("primaryButton")
        search_btn.clicked.connect(self.search)
        row2_layout.addWidget(search_btn)
        
        layout.addLayout(row2_layout)
        
        return group