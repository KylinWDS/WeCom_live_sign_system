from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTextEdit, QComboBox,
                             QDateTimeEdit, QSpinBox, QMessageBox, QGroupBox,
                             QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
                             QHeaderView, QFileDialog)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from src.ui.managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.models.live_booking import LiveBooking
from src.core.database import DatabaseManager
from src.api.wecom import WeComAPI
from src.core.task_manager import TaskManager
from datetime import datetime
from src.ui.components.dialogs.io_dialog import IODialog
import pandas as pd
import os

logger = get_logger(__name__)

class LiveBookingPage(QWidget):
    """直播预约页面"""
    
    def __init__(self, db_manager: DatabaseManager, wecom_api: WeComAPI, task_manager: TaskManager):
        super().__init__()
        self.db_manager = db_manager
        self.wecom_api = wecom_api
        self.task_manager = task_manager
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("liveBookingPage")
        
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
        self.setStyleSheet(StyleManager.get_live_booking_style())
        
        # 添加淡入动画
        AnimationManager.fade_in(self)
        
        # 加载数据
        self.load_data()
        
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QHBoxLayout()
        
        # 创建表单
        form_group = self._create_form_group()
        toolbar.addWidget(form_group)
        
        # 创建按钮
        button_layout = QHBoxLayout()
        
        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_btn)
        
        toolbar.addLayout(button_layout)
        
        return toolbar
        
    def _create_form_group(self) -> QGroupBox:
        """创建表单组"""
        group = QGroupBox("直播信息")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # 主播信息
        anchor_layout = QHBoxLayout()
        anchor_layout.addWidget(QLabel("主播ID:"))
        self.anchor_input = QLineEdit()
        self.anchor_input.setPlaceholderText("请输入主播ID")
        WidgetUtils.set_input_style(self.anchor_input)
        anchor_layout.addWidget(self.anchor_input)
        layout.addLayout(anchor_layout)
        
        # 直播标题
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("直播标题:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("请输入直播标题(最多20个字符)")
        WidgetUtils.set_input_style(self.title_input)
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)
        
        # 直播时间
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("开始时间:"))
        self.start_time = QDateTimeEdit()
        self.start_time.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # 默认1小时后
        self.start_time.setMinimumDateTime(QDateTime.currentDateTime())
        time_layout.addWidget(self.start_time)
        
        time_layout.addWidget(QLabel("直播时长:"))
        self.duration = QSpinBox()
        self.duration.setRange(1, 24 * 3600)  # 1秒到24小时
        self.duration.setValue(3600)  # 默认1小时
        self.duration.setSuffix(" 秒")
        WidgetUtils.set_spin_style(self.duration)
        time_layout.addWidget(self.duration)
        
        layout.addLayout(time_layout)
        
        # 直播类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("直播类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "通用直播",
            "小班课",
            "大班课",
            "企业培训",
            "活动直播"
        ])
        self.type_combo.setCurrentText("企业培训")  # 默认企业
        WidgetUtils.set_combo_style(self.type_combo)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # 直播描述
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("直播描述:"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("请输入直播描述(最多100个字符)")
        self.desc_input.setMaximumHeight(100)
        WidgetUtils.set_input_style(self.desc_input)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)
        
        return group
        
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
        
    @PerformanceManager.measure_operation("validate_input")
    def _validate_input(self) -> bool:
        """验证输入"""
        try:
            # 验证主播ID
            if not self.anchor_input.text().strip():
                ErrorHandler.handle_warning("请输入主播ID", self)
                return False
                
            # 验证直播标题
            title = self.title_input.text().strip()
            if not title:
                ErrorHandler.handle_warning("请输入直播标题", self)
                return False
            if len(title) > 20:
                ErrorHandler.handle_warning("直播标题不能超过20个字符", self)
                return False
                
            # 验证直播描述
            desc = self.desc_input.toPlainText().strip()
            if len(desc) > 100:
                ErrorHandler.handle_warning("直播描述不能超过100个字符", self)
                return False
                
            # 验证直播类型
            type_index = self.type_combo.currentIndex()
            if type_index not in [0, 3, 4]:  # 不是通用直播、企业培训或活动直播
                reply = ErrorHandler.handle_question(
                    "当前选择的直播类型可能会创建失败，是否继续？",
                    self,
                    "提示"
                )
                if not reply:
                    return False
                    
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "验证输入失败")
            return False
        
    @PerformanceManager.measure_operation("save_live_info")
    def _on_save(self):
        """保存直播信息"""
        try:
            # 验证输入
            if not self._validate_input():
                return
                
            # 获取输入数据
            data = {
                "anchor_userid": self.anchor_input.text().strip(),
                "theme": self.title_input.text().strip(),
                "living_start": int(self.start_time.dateTime().toSecsSinceEpoch()),
                "living_duration": self.duration.value(),
                "description": self.desc_input.toPlainText().strip(),
                "type": self.type_combo.currentIndex(),
                "agentid": self.db_manager.get_current_agent_id()
            }
            
            # 创建直播
            result = self.wecom_api.create_live(**data)
            
            if result["errcode"] == 0:
                # 保存到数据库
                self.save_live_info(result["livingid"], data)
                
                # 调度详情拉取任务
                self.task_manager.schedule_live_info_task(
                    result["livingid"],
                    data["living_start"]
                )
                
                # 显示成功消息
                ErrorHandler.handle_info("直播预约创建成功", self, "成功")
                
                # 清空表单
                self._clear_form()
                
                # 添加淡出动画
                AnimationManager.fade_out(self)
                
                # 跳转到直播列表页面
                self.parent().switch_to_live_list()
                
            else:
                ErrorHandler.handle_error(
                    Exception(result["errmsg"]),
                    self,
                    "创建直播失败"
                )
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存直播信息失败")
            
    def _on_cancel(self):
        """取消操作"""
        # 添加淡出动画
        AnimationManager.fade_out(self)
        self._clear_form()
        
    def _clear_form(self):
        """清空表单"""
        self.anchor_input.clear()
        self.title_input.clear()
        self.start_time.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.duration.setValue(3600)
        self.type_combo.setCurrentText("企业培训")
        self.desc_input.clear()
        
    def save_live_info(self, livingid: str, data: dict):
        """保存直播信息到数据库"""
        try:
            with self.db_manager.get_session() as session:
                live = LiveBooking(
                    livingid=livingid,
                    anchor_userid=data["anchor_userid"],
                    theme=data["theme"],
                    living_start=datetime.fromtimestamp(data["living_start"]),
                    living_duration=data["living_duration"],
                    description=data["description"],
                    type=data["type"],
                    status=0  # 预约中
                )
                session.add(live)
                session.commit()
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存直播信息到数据库失败")
            raise 