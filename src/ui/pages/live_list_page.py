from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QSpinBox, QHeaderView,
    QFileDialog, QDialog, QFormLayout, QGroupBox,
    QDateEdit, QTimeEdit, QToolBar, QSpacerItem, QSizePolicy,
    QProgressDialog, QInputDialog
)
from PySide6.QtCore import Qt, QDateTime, QTimer
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from src.ui.managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.models.live_booking import LiveBooking, LiveStatus as BookingStatus
from src.core.database import DatabaseManager
from src.api.wecom import WeComAPI
from src.models.living import Living, LivingStatus, LivingType
from datetime import datetime, timedelta
from src.ui.components.dialogs.io_dialog import IODialog
from src.ui.components.widgets.custom_datetime_widget import CustomDateTimeWidget
import pandas as pd
import os
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from src.core.live_viewer_manager import LiveViewerManager

logger = get_logger(__name__)

class AutoCloseMessageBox(QMessageBox):
    """自动关闭的消息对话框"""
    
    def __init__(self, title, text, timeout=3000, parent=None):
        """
        初始化自动关闭的消息对话框
        
        Args:
            title: 标题
            text: 显示文本
            timeout: 自动关闭的时间（毫秒）
            parent: 父窗口
        """
        super().__init__(QMessageBox.Information, title, text, QMessageBox.NoButton, parent)
        self.timeout = timeout
        
        # 添加倒计时标签
        self.time_label = QLabel(f"{timeout//1000}秒后自动关闭", self)
        self.time_label.setStyleSheet("color: gray; margin-top: 10px;")
        self.time_label.setAlignment(Qt.AlignRight)
        
        # 获取布局并添加标签
        layout = self.layout()
        layout.addWidget(self.time_label, layout.rowCount(), 0, 1, layout.columnCount(), Qt.AlignRight)
        
        # 设置定时器
        self.countdown = timeout // 1000  # 转换为秒
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_counter)
        self.timer.start(1000)  # 每秒更新一次
    
    def update_counter(self):
        """更新倒计时"""
        self.countdown -= 1
        if self.countdown <= 0:
            self.timer.stop()
            self.close()
        else:
            self.time_label.setText(f"{self.countdown}秒后自动关闭")

class LiveListPage(QWidget):
    """直播列表页面"""
    
    def __init__(self, db_manager: DatabaseManager, wecom_api: WeComAPI, auth_manager=None, user_id=None):
        super().__init__()
        self.db_manager = db_manager
        self.wecom_api = wecom_api
        self.auth_manager = auth_manager
        self.user_id = user_id
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("liveListPage")
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 创建搜索和工具栏区域
        search_tool_layout = QVBoxLayout()
        search_tool_layout.setSpacing(10)
        
        # 创建搜索区域
        search_group = self._create_search_group()
        search_tool_layout.addWidget(search_group)
        
        # 添加工具栏
        toolbar = self._create_toolbar()
        search_tool_layout.addWidget(toolbar)
        
        layout.addLayout(search_tool_layout)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(16)  # 从12增加到16列，添加4个状态字段
        self.table.setHorizontalHeaderLabels([
            "直播ID", "直播标题", "开始时间", "结束时间",
            "主播", "状态", "直播类型", 
            "观看人数", "评论数", "签到人数", "签到次数", 
            "观看信息", "签到导入", "企微文档", "远程同步", "操作"  # 添加4个状态字段
        ])
        
        # 设置表格可以显示滚动条
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # 始终显示横向滚动条
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 设置各列的宽度模式 - 除了操作列使用固定宽度外，其他列使用固定宽度以确保内容可见
        column_widths = [100, 200, 150, 150, 150, 100, 120, 80, 80, 80, 80, 80, 80, 80, 80, 350]  # 将操作列宽度从280增加到350
        
        for i in range(15):  # 前15列使用固定宽度
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Interactive)  # 允许用户调整宽度
            self.table.setColumnWidth(i, column_widths[i])
            
        # 操作列使用固定宽度，确保按钮显示完整
        self.table.horizontalHeader().setSectionResizeMode(15, QHeaderView.Fixed)
        self.table.setColumnWidth(15, column_widths[15])  # 为操作列设置足够宽度
        
        # 设置垂直头部策略，适应内容
        self.table.verticalHeader().setVisible(False)  # 隐藏行号
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置选择模式
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        # 应用样式
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
        self.setStyleSheet(StyleManager.get_live_list_style())
        
        # 添加淡入动画
        AnimationManager.fade_in(self)
        
        # 加载数据
        self.current_page = 1
        self.page_size = 10
        self.load_data()
        
    def _create_search_group(self) -> QGroupBox:
        """创建搜索区域"""
        group = QGroupBox("搜索条件")
        main_layout = QVBoxLayout(group)
        main_layout.setSpacing(10)
        
        # 第一行：标题和状态
        first_row = QHBoxLayout()
        first_row.setSpacing(10)
        
        # 直播标题
        first_row.addWidget(QLabel("直播标题:"))
        self.live_title = QLineEdit()
        self.live_title.setMaximumWidth(180)
        WidgetUtils.set_input_style(self.live_title)
        first_row.addWidget(self.live_title)
        
        # 直播状态
        first_row.addWidget(QLabel("直播状态:"))
        self.live_status = QComboBox()
        self.live_status.addItems(["全部", "未开始", "进行中", "已结束"])
        self.live_status.setMaximumWidth(100)
        WidgetUtils.set_combo_style(self.live_status)
        first_row.addWidget(self.live_status)
        
        # 添加弹性空间，让元素靠左对齐
        first_row.addStretch(1)
        
        # 第二行：新增的状态字段搜索
        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        
        # 是否拉取观看信息
        status_row.addWidget(QLabel("观看信息:"))
        self.viewer_fetched_status = QComboBox()
        self.viewer_fetched_status.addItems(["全部", "已拉取", "未拉取"])
        self.viewer_fetched_status.setMaximumWidth(80)
        WidgetUtils.set_combo_style(self.viewer_fetched_status)
        status_row.addWidget(self.viewer_fetched_status)
        
        # 是否导入签到
        status_row.addWidget(QLabel("签到导入:"))
        self.sign_imported_status = QComboBox()
        self.sign_imported_status.addItems(["全部", "已导入", "未导入"])
        self.sign_imported_status.setMaximumWidth(80)
        WidgetUtils.set_combo_style(self.sign_imported_status)
        status_row.addWidget(self.sign_imported_status)
        
        # 是否上传企微文档
        status_row.addWidget(QLabel("企微文档:"))
        self.doc_uploaded_status = QComboBox()
        self.doc_uploaded_status.addItems(["全部", "已上传", "未上传"])
        self.doc_uploaded_status.setMaximumWidth(80)
        WidgetUtils.set_combo_style(self.doc_uploaded_status)
        status_row.addWidget(self.doc_uploaded_status)
        
        # 是否远程同步
        status_row.addWidget(QLabel("远程同步:"))
        self.remote_synced_status = QComboBox()
        self.remote_synced_status.addItems(["全部", "已同步", "未同步"])
        self.remote_synced_status.setMaximumWidth(80)
        WidgetUtils.set_combo_style(self.remote_synced_status)
        status_row.addWidget(self.remote_synced_status)
        
        # 添加弹性空间，让元素靠左对齐
        status_row.addStretch(1)
        
        # 第三行：时间范围和按钮
        second_row = QHBoxLayout()
        second_row.setSpacing(10)
        
        # 直播时间范围 - 使用自定义日期时间组件
        second_row.addWidget(QLabel("开始时间:"))
        self.start_date_time = CustomDateTimeWidget()
        self.start_date_time.setDateTime(QDateTime.currentDateTime().addMonths(-1))  # 默认一个月前
        self.start_date_time.setWidth(230)  # 设置合适的宽度
        second_row.addWidget(self.start_date_time)
        
        second_row.addWidget(QLabel("至"))
        
        self.end_date_time = CustomDateTimeWidget()
        self.end_date_time.setDateTime(QDateTime.currentDateTime())  # 默认今天
        self.end_date_time.setWidth(230)  # 设置合适的宽度
        second_row.addWidget(self.end_date_time)
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("primaryButton")
        search_btn.clicked.connect(self.search)
        second_row.addWidget(search_btn)
        
        # 重置按钮
        reset_btn = QPushButton("重置")
        reset_btn.setObjectName("primaryButton")
        reset_btn.clicked.connect(self.reset_search)
        second_row.addWidget(reset_btn)
        
        # 同步按钮
        sync_btn = QPushButton("同步直播数据")
        sync_btn.setObjectName("primaryButton")
        sync_btn.clicked.connect(self.sync_live_data)
        second_row.addWidget(sync_btn)
        
        # 导出按钮
        export_btn = QPushButton("导出数据")
        export_btn.setObjectName("primaryButton")
        export_btn.clicked.connect(self.export_data)
        second_row.addWidget(export_btn)
        
        # 将两行添加到主布局
        main_layout.addLayout(first_row)
        main_layout.addLayout(status_row)
        main_layout.addLayout(second_row)
        
        return group
        
    @PerformanceManager.measure_operation("load_data")
    def load_data(self):
        """加载数据"""
        try:
            # 获取直播列表
            records_data = []  # 存储转换后的记录数据
            
            with self.db_manager.get_session() as session:
                # 获取当前用户信息和权限
                current_user = None
                user_role = None
                user_corpname = None
                user_id = None
                
                if self.auth_manager and self.user_id:
                    # 在当前会话中获取用户信息
                    from src.models.user import User, UserRole
                    current_user = session.query(User).filter_by(userid=self.user_id).first()
                    if current_user:
                        user_role = current_user.role
                        user_corpname = current_user.corpname
                        user_id = current_user.wecom_code or current_user.login_name
                
                # 使用旧版API风格
                query = session.query(Living)
                
                # 根据用户权限过滤数据
                if current_user:
                    if user_role == UserRole.ROOT_ADMIN.value:
                        # 超级管理员可以查看所有直播
                        pass
                    elif user_role == UserRole.WECOM_ADMIN.value and user_corpname:
                        # 企业管理员只能查看自己企业的直播
                        query = query.filter(Living.corpname == user_corpname)
                    else:
                        # 普通用户只能查看自己为主播的直播
                        if user_id:
                            query = query.filter(Living.anchor_userid == user_id)
                        else:
                            # 如果没有企业微信ID，则显示空列表
                            logger.warning(f"用户 {current_user.login_name} 没有企业微信ID，无法显示直播列表")
                            self.table.setRowCount(0)
                            self.prev_btn.setEnabled(False)
                            self.next_btn.setEnabled(False)
                            self.page_label.setText("第 0 页 / 共 0 页")
                            return
                
                # 应用搜索条件
                if self.live_title.text():
                    query = query.filter(Living.theme.like(f"%{self.live_title.text()}%"))
                    
                if self.live_status.currentText() != "全部":
                    status_map = {
                        "未开始": LivingStatus.RESERVED,
                        "进行中": LivingStatus.LIVING,
                        "已结束": LivingStatus.ENDED
                    }
                    query = query.filter(Living.status == status_map[self.live_status.currentText()])
                
                # 应用新增的状态字段过滤条件
                # 是否拉取观看信息
                if self.viewer_fetched_status.currentText() != "全部":
                    is_fetched = 1 if self.viewer_fetched_status.currentText() == "已拉取" else 0
                    query = query.filter(Living.is_viewer_fetched == is_fetched)
                
                # 是否导入签到
                if self.sign_imported_status.currentText() != "全部":
                    is_imported = 1 if self.sign_imported_status.currentText() == "已导入" else 0
                    query = query.filter(Living.is_sign_imported == is_imported)
                
                # 是否上传企微文档
                if self.doc_uploaded_status.currentText() != "全部":
                    is_uploaded = 1 if self.doc_uploaded_status.currentText() == "已上传" else 0
                    query = query.filter(Living.is_doc_uploaded == is_uploaded)
                
                # 是否远程同步
                if self.remote_synced_status.currentText() != "全部":
                    is_synced = 1 if self.remote_synced_status.currentText() == "已同步" else 0
                    query = query.filter(Living.is_remote_synced == is_synced)
                
                # 应用日期范围查询
                start_datetime = self.start_date_time.dateTime().toPython()
                end_datetime = self.end_date_time.dateTime().toPython()
                
                # 过滤直播开始时间在指定范围内的记录
                query = query.filter(Living.living_start >= start_datetime)
                query = query.filter(Living.living_start <= end_datetime)
                
                # 计算总记录数
                total = query.count()
                self.total_pages = (total + self.page_size - 1) // self.page_size
                
                # 获取当前页数据
                records = query.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
                
                # 在会话内将数据转换为字典，避免会话关闭后的访问问题
                for record in records:
                    # 获取所有需要的数据
                    record_data = {
                        "id": record.id,  # 用于标识记录
                        "livingid": record.livingid,
                        "theme": record.theme,
                        "living_start": record.living_start,
                        "living_duration": record.living_duration,
                        "anchor_userid": record.anchor_userid,
                        "description": record.description,
                        "type": record.type,
                        "status": record.status,
                        "corpname": record.corpname,
                        "agentid": record.agentid,
                        "viewer_num": record.viewer_num,
                        "comment_num": record.comment_num,
                        "mic_num": record.mic_num,
                        "online_count": record.online_count,
                        "subscribe_count": record.subscribe_count
                    }
                    
                    # 获取主播的名称
                    from src.models.user import User
                    user = session.query(User).filter(
                        (User.wecom_code == record.anchor_userid) | 
                        (User.login_name == record.anchor_userid)
                    ).first()
                    
                    if user:
                        record_data["anchor_name"] = f"{user.name}({record.anchor_userid})"
                    else:
                        record_data["anchor_name"] = f"{record.anchor_userid}"
                    
                    # 计算结束时间
                    if record.living_start and record.living_duration:
                        record_data["end_time"] = record.living_start + timedelta(seconds=record.living_duration)
                    else:
                        record_data["end_time"] = None
                        
                    # 获取签到统计信息
                    from src.models.live_viewer import LiveViewer
                    # 使用 LiveViewer 查询签到统计
                    sign_stats = {}
                    with self.db_manager.get_session() as stats_session:
                        # 获取不同的签到人数
                        unique_signers = stats_session.query(func.count(LiveViewer.id)).filter(
                            LiveViewer.living_id == record.id,
                            LiveViewer.is_signed == True
                        ).scalar() or 0
                        
                        # 获取总签到次数
                        sign_count = stats_session.query(func.sum(LiveViewer.sign_count)).filter(
                            LiveViewer.living_id == record.id,
                            LiveViewer.is_signed == True
                        ).scalar() or 0
                        
                        # 获取首次签到时间
                        first_sign = stats_session.query(func.min(LiveViewer.sign_time)).filter(
                            LiveViewer.living_id == record.id,
                            LiveViewer.is_signed == True
                        ).scalar()
                        
                        sign_stats = {
                            "unique_signers": unique_signers,
                            "sign_count": sign_count,
                            "sign_time": first_sign
                        }
                    
                    record_data["sign_count"] = sign_stats["unique_signers"]  # 使用unique_signers作为签到人数
                    record_data["total_sign_count"] = sign_stats["sign_count"]  # 总签到次数
                    record_data["sign_time"] = sign_stats["sign_time"]
                    
                    # 添加状态字段
                    record_data["is_viewer_fetched"] = record.is_viewer_fetched
                    record_data["is_sign_imported"] = record.is_sign_imported
                    record_data["is_doc_uploaded"] = record.is_doc_uploaded
                    record_data["is_remote_synced"] = record.is_remote_synced
                    
                    records_data.append(record_data)
                
            # 更新表格
            self.table.setRowCount(len(records_data))
            for row, record_data in enumerate(records_data):
                # 设置足够的行高以容纳按钮
                self.table.setRowHeight(row, 27)  # 设置每行高度为原来的2/3（约27像素）
                
                self.table.setItem(row, 0, QTableWidgetItem(record_data["livingid"]))
                self.table.setItem(row, 1, QTableWidgetItem(record_data["theme"]))
                self.table.setItem(row, 2, QTableWidgetItem(record_data["living_start"].strftime("%Y-%m-%d %H:%M:%S")))
                
                # 结束时间
                end_time_str = record_data["end_time"].strftime("%Y-%m-%d %H:%M:%S") if record_data["end_time"] else "-"
                self.table.setItem(row, 3, QTableWidgetItem(end_time_str))
                
                # 主播名称
                self.table.setItem(row, 4, QTableWidgetItem(record_data["anchor_name"]))
                
                # 状态
                status_text = {
                    LivingStatus.RESERVED: "预约中",
                    LivingStatus.LIVING: "直播中",
                    LivingStatus.ENDED: "已结束",
                    LivingStatus.EXPIRED: "已过期",
                    LivingStatus.CANCELLED: "已取消"
                }.get(record_data["status"], "未知")
                self.table.setItem(row, 5, QTableWidgetItem(status_text))
                
                # 直播类型
                type_text = {
                    LivingType.GENERAL: "通用直播",
                    LivingType.SMALL: "小班课",
                    LivingType.LARGE: "大班课",
                    LivingType.TRAINING: "企业培训",
                    LivingType.EVENT: "活动直播"
                }.get(record_data["type"], "未知")
                self.table.setItem(row, 6, QTableWidgetItem(type_text))
                
                self.table.setItem(row, 7, QTableWidgetItem(str(record_data["viewer_num"])))
                self.table.setItem(row, 8, QTableWidgetItem(str(record_data["comment_num"])))
                
                # 签到人数
                self.table.setItem(row, 9, QTableWidgetItem(str(record_data["sign_count"])))
                
                # 签到次数
                self.table.setItem(row, 10, QTableWidgetItem(str(record_data["total_sign_count"])))
                
                # 观看信息状态
                viewer_fetched_text = "已拉取" if record_data["is_viewer_fetched"] == 1 else "未拉取"
                viewer_item = QTableWidgetItem(viewer_fetched_text)
                viewer_item.setForeground(Qt.green if record_data["is_viewer_fetched"] == 1 else Qt.red)
                self.table.setItem(row, 11, viewer_item)
                
                # 签到导入状态
                sign_imported_text = "已导入" if record_data["is_sign_imported"] == 1 else "未导入"
                sign_item = QTableWidgetItem(sign_imported_text)
                sign_item.setForeground(Qt.green if record_data["is_sign_imported"] == 1 else Qt.red)
                self.table.setItem(row, 12, sign_item)
                
                # 企微文档状态
                doc_uploaded_text = "已上传" if record_data["is_doc_uploaded"] == 1 else "未上传"
                doc_item = QTableWidgetItem(doc_uploaded_text)
                doc_item.setForeground(Qt.green if record_data["is_doc_uploaded"] == 1 else Qt.red)
                self.table.setItem(row, 13, doc_item)
                
                # 远程同步状态
                remote_synced_text = "已同步" if record_data["is_remote_synced"] == 1 else "未同步"
                remote_item = QTableWidgetItem(remote_synced_text)
                remote_item.setForeground(Qt.green if record_data["is_remote_synced"] == 1 else Qt.red)
                self.table.setItem(row, 14, remote_item)
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(2, 2, 2, 2)  # 减小边距使按钮更紧凑
                btn_layout.setSpacing(5)  # 减少按钮之间的间距
                
                # 创建Living对象用于按钮回调，避免会话问题
                living = Living(
                    livingid=record_data["livingid"],
                    theme=record_data["theme"],
                    living_start=record_data["living_start"],
                    living_duration=record_data["living_duration"],
                    anchor_userid=record_data["anchor_userid"],
                    description=record_data["description"],
                    status=record_data["status"],
                    type=record_data["type"],
                    corpname=record_data["corpname"],
                    agentid=record_data["agentid"],
                    viewer_num=record_data["viewer_num"],
                    comment_num=record_data["comment_num"],
                    mic_num=record_data["mic_num"],
                    online_count=record_data["online_count"],
                    subscribe_count=record_data["subscribe_count"]
                )
                # 保存签到信息到living对象中，以便在详情对话框中使用
                living.sign_count = record_data["sign_count"]
                living.total_sign_count = record_data["total_sign_count"]
                living.sign_time = record_data["sign_time"]
                
                # 创建样式化的按钮，减小高度以适应行高
                view_btn = QPushButton("查看")
                view_btn.setObjectName("linkButton")
                view_btn.setMinimumHeight(22)  # 减小按钮高度
                view_btn.setFixedWidth(80)  # 固定宽度
                view_btn.clicked.connect(lambda checked, r=living: self.view_details(r))
                btn_layout.addWidget(view_btn)
                
                # 添加"拉取观看信息"按钮，并根据状态调整显示
                fetch_viewer_btn = QPushButton("拉取观看信息" if not record_data["is_viewer_fetched"] else "重取观看信息")
                fetch_viewer_btn.setObjectName("linkButton")
                fetch_viewer_btn.setMinimumHeight(22)  # 减小按钮高度
                fetch_viewer_btn.setFixedWidth(120)  # 固定宽度
                # 如果已经拉取过，使用不同的样式
                if record_data["is_viewer_fetched"]:
                    fetch_viewer_btn.setStyleSheet("color: #0056b3;")  # 使用较暗的蓝色
                fetch_viewer_btn.clicked.connect(lambda checked, r=living: self.fetch_watch_stat(r))
                btn_layout.addWidget(fetch_viewer_btn)
                
                import_btn = QPushButton("导入签到")
                import_btn.setObjectName("linkButton")
                import_btn.setMinimumHeight(22)  # 减小按钮高度
                import_btn.setFixedWidth(80)  # 固定宽度
                import_btn.clicked.connect(lambda checked, r=living: self.import_sign(r))
                btn_layout.addWidget(import_btn)
                
                # 只有在直播状态为"预约中"时才显示取消按钮
                if record_data["status"] == LivingStatus.RESERVED:
                    cancel_btn = QPushButton("取消")
                    cancel_btn.setObjectName("linkButton")
                    cancel_btn.setMinimumHeight(22)  # 减小按钮高度
                    cancel_btn.setFixedWidth(80)  # 固定宽度
                    cancel_btn.clicked.connect(lambda checked, r=living: self.cancel_live(r))
                    btn_layout.addWidget(cancel_btn)
                
                self.table.setCellWidget(row, 15, btn_widget)
                
            # 更新分页信息
            self.page_label.setText(f"第 {self.current_page} 页 / 共 {self.total_pages} 页")
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < self.total_pages)
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "加载直播列表失败")
            
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
            
    @PerformanceManager.measure_operation("view_details")
    def view_details(self, live: Living):
        """查看直播详情
        
        Args:
            live: 直播信息
        """
        try:
            # 从数据库获取最新记录，确保状态是最新的
            with self.db_manager.get_session() as session:
                record = session.query(Living).filter_by(livingid=live.livingid).first()
                if record:
                    # 使用最新的数据库记录创建详情对话框
                    dialog = LiveDetailsDialog(record)
                else:
                    # 如果找不到记录，使用传入的live对象
                    dialog = LiveDetailsDialog(live)
                dialog.exec()
                
            # 获取直播详情
            response = self.wecom_api.get_living_info(live.livingid)
            
            if response.get("errcode") == 0:
                # 获取直播信息
                live_info = response.get("living_info", {})
                
                # 更新直播数据
                with self.db_manager.get_session() as session:
                    # 从数据库中获取最新的实体
                    stmt = select(Living).where(Living.livingid == live.livingid)
                    result = session.execute(stmt)
                    db_live = result.scalar_one_or_none()
                    
                    # 如果找到实体，才更新它
                    if db_live:
                        db_live.viewer_num = live_info["viewer_num"]
                        db_live.comment_num = live_info["comment_num"]
                        db_live.mic_num = live_info["mic_num"]
                        
                        # 处理状态字段，确保它是 LivingStatus 枚举类型
                        status_value = live_info.get("status")
                        if status_value is not None:
                            if isinstance(status_value, int) or (isinstance(status_value, str) and status_value.isdigit()):
                                status_value = int(status_value)
                                # 将数字映射到 LivingStatus 枚举
                                status_map = {
                                    0: LivingStatus.RESERVED,
                                    1: LivingStatus.LIVING,
                                    2: LivingStatus.ENDED,
                                    3: LivingStatus.EXPIRED,
                                    4: LivingStatus.CANCELLED
                                }
                                db_live.status = status_map.get(status_value, LivingStatus.RESERVED)
            else:
                ErrorHandler.handle_warning(
                    f"获取直播详情失败：{response.get('errmsg')}",
                    self,
                    "失败"
                )
        except Exception as e:
            ErrorHandler.handle_error(e, self, "查看直播详情失败")
            
    @PerformanceManager.measure_operation("sync_live_data")
    def sync_live_data(self):
        """同步直播数据"""
        try:
            confirm = ErrorHandler.handle_question(
                "确定要同步直播数据吗？这将从企业微信拉取最新数据并更新本地数据库。",
                self,
                "确认同步"
            )
            
            if not confirm:
                return
                
            # 显示倒计时提示（自动3秒关闭）
            msg_box = AutoCloseMessageBox("同步进行中", "正在同步直播数据，请稍候...", 3000, self)
            msg_box.exec()
            
            # 获取用于API调用的用户ID列表
            user_ids_for_api = []
            
            with self.db_manager.get_session() as session:
                from src.models.user import UserRole, User
                
                # 1. 获取当前用户信息和权限
                current_user = None
                user_role = None
                user_corpid = None
                
                if self.auth_manager and self.user_id:
                    # 在当前会话中获取用户信息
                    current_user = session.query(User).filter_by(userid=self.user_id).first()
                    if current_user:
                        user_role = current_user.role
                        user_corpid = current_user.corpid
                
                if not current_user:
                    ErrorHandler.handle_warning(
                        "无法获取当前用户信息，将使用默认权限同步数据。",
                        self,
                        "警告"
                    )
                
                # 2. 根据权限确定要获取的用户ID列表
                if current_user and user_role == UserRole.ROOT_ADMIN.value:
                    # 如果是超级管理员，获取所有用户的直播列表
                    users = session.query(User).all()
                    for user in users:
                        userid = user.wecom_code or user.login_name
                        if userid:
                            user_ids_for_api.append(userid)
                
                elif current_user and user_role == UserRole.WECOM_ADMIN.value and user_corpid:
                    # 如果是企业管理员，获取该企业下所有用户的直播列表
                    users = session.query(User).filter_by(corpid=user_corpid).all()
                    for user in users:
                        userid = user.wecom_code or user.login_name
                        if userid:
                            user_ids_for_api.append(userid)
                
                else:
                    # 如果是普通用户或无法确定角色，只获取自己的直播列表
                    if current_user:
                        userid = current_user.wecom_code or current_user.login_name
                        if userid:
                            user_ids_for_api.append(userid)
            
            # 从企业微信API获取直播ID列表
            livingid_list = []
            for userid in user_ids_for_api:
                try:
                    response = self.wecom_api.get_user_all_livingid(userid)
                    if response.get("errcode") == 0:
                        livingid_list.extend(response.get("livingid_list", []))
                except Exception as e:
                    logger.error(f"获取用户 {userid} 的直播列表失败: {str(e)}")
            
            # 去重
            livingid_list = list(set(livingid_list))
            
            # 3. 从预约直播表中获取数据
            bookings = {}
            with self.db_manager.get_session() as session:
                booking_records = session.query(LiveBooking).all()
                for booking in booking_records:
                    bookings[booking.livingid] = {
                        "id": booking.id,  # 添加booking的ID
                        "livingid": booking.livingid,
                        "theme": booking.theme,
                        "living_start": booking.living_start,
                        "living_duration": booking.living_duration,
                        "anchor_userid": booking.anchor_userid,
                        "description": booking.description,
                        "type": booking.type,
                        "status": booking.status,
                        "corpname": booking.corpname,
                        "agentid": booking.agentid,
                        "viewer_num": booking.viewer_num,
                        "comment_num": booking.comment_num,
                        "mic_num": booking.mic_num,
                        "online_count": booking.online_count,
                        "subscribe_count": booking.subscribe_count,
                    }
            
            # 4. 从直播信息表中获取数据
            livings = {}
            with self.db_manager.get_session() as session:
                living_records = session.query(Living).all()
                for living in living_records:
                    livings[living.livingid] = {
                        "id": living.id,  # 添加living的ID
                        "livingid": living.livingid,
                        "theme": living.theme,
                        "living_start": living.living_start,
                        "living_duration": living.living_duration,
                        "anchor_userid": living.anchor_userid,
                        "description": living.description,
                        "type": living.type,
                        "status": living.status,
                        "corpname": living.corpname,
                        "agentid": living.agentid,
                        "viewer_num": living.viewer_num,
                        "comment_num": living.comment_num,
                        "mic_num": living.mic_num,
                        "online_count": living.online_count,
                        "subscribe_count": living.subscribe_count,
                    }
            
            # 5. 创建所有直播ID的集合（API获取的 + 本地数据库的）
            all_live_ids = set(livingid_list) | set(bookings.keys()) | set(livings.keys())
            
            # 6. 从企业微信获取直播数据
            updated_count = 0
            created_count = 0
            
            with self.db_manager.get_session() as session:
                for livingid in all_live_ids:
                    # 从企业微信获取数据
                    try:
                        response = self.wecom_api.get_living_info(livingid)
                        
                        if response.get("errcode") == 0:
                            # 获取企业微信返回的数据
                            wecom_data = response.get("living_info", {})
                            
                            # 创建最终数据（优先级：企业微信 > livings > bookings）
                            final_data = {}
                            
                            # 添加bookings数据
                            booking_id = None
                            if livingid in bookings:
                                final_data.update(bookings[livingid])
                                booking_id = bookings[livingid]["id"]
                                
                            # 添加livings数据
                            if livingid in livings:
                                final_data.update(livings[livingid])
                                
                            # 添加企业微信数据（转换格式）
                            if wecom_data:
                                # 转换时间和状态
                                if "living_start" in wecom_data and isinstance(wecom_data["living_start"], (int, float)):
                                    wecom_data["living_start"] = datetime.fromtimestamp(wecom_data["living_start"])
                                    
                                # 转换状态（BookingStatus -> LivingStatus）
                                if "status" in wecom_data:
                                    status_map = {
                                        BookingStatus.RESERVING: LivingStatus.RESERVED,
                                        BookingStatus.LIVING: LivingStatus.LIVING,
                                        BookingStatus.ENDED: LivingStatus.ENDED,
                                        BookingStatus.EXPIRED: LivingStatus.EXPIRED,
                                        BookingStatus.CANCELLED: LivingStatus.CANCELLED
                                    }
                                    wecom_data["status"] = status_map.get(wecom_data["status"], LivingStatus.RESERVED)
                                
                                final_data.update(wecom_data)
                            
                            # 检查是否存在
                            exists = session.query(Living).filter_by(livingid=livingid).first()
                            
                            if exists:
                                # 处理类型字段，确保它是 LivingType 枚举类型
                                type_value = final_data.get("type")
                                if type_value is not None:
                                    if isinstance(type_value, int) or (isinstance(type_value, str) and type_value.isdigit()):
                                        type_value = int(type_value)
                                        # 将数字映射到 LivingType 枚举
                                        type_map = {
                                            0: LivingType.GENERAL,
                                            1: LivingType.SMALL,
                                            2: LivingType.LARGE,
                                            3: LivingType.TRAINING,
                                            4: LivingType.EVENT
                                        }
                                        exists.type = type_map.get(type_value, LivingType.GENERAL)
                                
                                # 处理状态字段，确保它是 LivingStatus 枚举类型
                                status_value = final_data.get("status")
                                if status_value is not None:
                                    if isinstance(status_value, int) or (isinstance(status_value, str) and status_value.isdigit()):
                                        status_value = int(status_value)
                                        # 将数字映射到 LivingStatus 枚举
                                        status_map = {
                                            0: LivingStatus.RESERVED,
                                            1: LivingStatus.LIVING,
                                            2: LivingStatus.ENDED,
                                            3: LivingStatus.EXPIRED,
                                            4: LivingStatus.CANCELLED
                                        }
                                        exists.status = status_map.get(status_value, LivingStatus.RESERVED)
                                
                                # 更新现有记录的其他字段
                                exists.theme = final_data.get("theme", exists.theme)
                                exists.living_start = final_data.get("living_start", exists.living_start)
                                exists.living_duration = final_data.get("living_duration", exists.living_duration)
                                exists.anchor_userid = final_data.get("anchor_userid", exists.anchor_userid)
                                exists.description = final_data.get("description", exists.description)
                                # type 和 status 已在上面处理，这里不再赋值
                                exists.corpname = final_data.get("corpname", exists.corpname)
                                exists.agentid = final_data.get("agentid", exists.agentid)
                                exists.viewer_num = final_data.get("viewer_num", exists.viewer_num)
                                exists.comment_num = final_data.get("comment_num", exists.comment_num)
                                exists.mic_num = final_data.get("mic_num", exists.mic_num)
                                exists.online_count = final_data.get("online_count", exists.online_count)
                                exists.subscribe_count = final_data.get("subscribe_count", exists.subscribe_count)
                                # 设置远程同步状态为已同步
                                exists.is_remote_synced = 1
                                # 设置关联的预约ID
                                exists.live_booking_id = booking_id
                                updated_count += 1
                                
                                # 更新相关的LiveViewer记录的live_booking_id
                                if booking_id:
                                    session.query(LiveViewer).filter_by(living_id=exists.id).update(
                                        {"live_booking_id": booking_id}
                                    )
                            else:
                                # 创建新记录
                                # 处理类型字段，确保它是 LivingType 枚举类型
                                type_value = final_data.get("type")
                                if type_value is not None:
                                    if isinstance(type_value, int) or (isinstance(type_value, str) and type_value.isdigit()):
                                        type_value = int(type_value)
                                        # 将数字映射到 LivingType 枚举
                                        type_map = {
                                            0: LivingType.GENERAL,
                                            1: LivingType.SMALL,
                                            2: LivingType.LARGE,
                                            3: LivingType.TRAINING,
                                            4: LivingType.EVENT
                                        }
                                        type_value = type_map.get(type_value, LivingType.GENERAL)
                                else:
                                    type_value = LivingType.GENERAL
                                    
                                # 处理状态字段，确保它是 LivingStatus 枚举类型
                                status_value = final_data.get("status", LivingStatus.RESERVED)
                                if isinstance(status_value, int) or (isinstance(status_value, str) and status_value.isdigit()):
                                    status_value = int(status_value)
                                    # 将数字映射到 LivingStatus 枚举
                                    status_map = {
                                        0: LivingStatus.RESERVED,
                                        1: LivingStatus.LIVING,
                                        2: LivingStatus.ENDED,
                                        3: LivingStatus.EXPIRED,
                                        4: LivingStatus.CANCELLED
                                    }
                                    status_value = status_map.get(status_value, LivingStatus.RESERVED)
                                
                                new_living = Living(
                                    livingid=livingid,
                                    theme=final_data.get("theme", ""),
                                    living_start=final_data.get("living_start", datetime.now()),
                                    living_duration=final_data.get("living_duration", 0),
                                    anchor_userid=final_data.get("anchor_userid", ""),
                                    description=final_data.get("description", ""),
                                    type=type_value,
                                    status=status_value,
                                    corpname=final_data.get("corpname", ""),
                                    agentid=final_data.get("agentid", ""),
                                    viewer_num=final_data.get("viewer_num", 0),
                                    comment_num=final_data.get("comment_num", 0),
                                    mic_num=final_data.get("mic_num", 0),
                                    online_count=final_data.get("online_count", 0),
                                    subscribe_count=final_data.get("subscribe_count", 0),
                                    is_remote_synced=1,  # 设置远程同步状态为已同步
                                    live_booking_id=booking_id  # 设置关联的预约ID
                                )
                                session.add(new_living)
                                created_count += 1
                    except Exception as e:
                        logger.error(f"同步直播数据失败 (ID: {livingid}): {str(e)}")
                
                # 提交所有更改
                session.commit()
            
            # 显示结果
            ErrorHandler.handle_info(
                f"同步直播数据完成\n更新记录：{updated_count}条\n新增记录：{created_count}条",
                self,
                "同步完成"
            )
            
            # 刷新数据
            self.load_data()
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "同步直播数据失败")
            
    @PerformanceManager.measure_operation("cancel_live")
    def cancel_live(self, live: Living):
        """取消直播
        
        Args:
            live: 直播信息
        """
        try:
            # 确认取消
            if not ErrorHandler.handle_question(
                "确定要取消该直播吗？",
                self,
                "确认取消"
            ):
                return
                
            # 取消直播
            response = self.wecom_api.cancel_living(live.livingid)
            
            if response.get("errcode") == 0:
                # 更新直播状态
                with self.db_manager.get_session() as session:
                    # 从数据库中获取最新的实体并更新
                    stmt = select(Living).where(Living.livingid == live.livingid)
                    result = session.execute(stmt)
                    db_live = result.scalar_one_or_none()
                    if db_live:
                        db_live.status = LivingStatus.CANCELLED
                
                ErrorHandler.handle_info("取消直播成功", self, "成功")
                self.load_data()
                
            else:
                ErrorHandler.handle_warning(
                    f"取消直播失败：{response.get('errmsg')}",
                    self,
                    "失败"
                )
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "取消直播失败")
            
    @PerformanceManager.measure_operation("import_sign")
    def import_sign(self, live: Living):
        """
        导入签到数据
        :param live: 直播信息
        """
        try:
            # 先在一个会话中执行检查
            with self.db_manager.get_session() as session:
                # 重新获取直播记录
                live_record = session.query(Living).filter_by(livingid=live.livingid).first()
                if not live_record:
                    ErrorHandler.handle_warning("找不到直播记录", self, "错误")
                    return
                
                # 添加调试日志
                logger.info(f"找到直播记录：id={live_record.id}, livingid={live_record.livingid}")
                
                # 检查是否已拉取观看信息
                if not live_record.is_viewer_fetched:
                    ErrorHandler.handle_warning("请先拉取观看信息后再导入签到数据", self, "错误")
                    return
            
            # 显示文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择签到文件",
                "",
                "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return  # 用户取消了选择，直接返回
            
            # 使用进度对话框模式创建IO对话框
            io_dialog = IODialog(parent=self, title="导入签到记录", is_progress_dialog=True)
            io_dialog.add_info(f"正在导入签到数据，请稍候...")
            io_dialog.add_info(f"选择的文件: {file_path}")
            io_dialog.show()
            
            # 读取文件
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                try:
                    df = pd.read_excel(file_path)
                except Exception as e:
                    io_dialog.add_error(f"读取Excel文件失败: {str(e)}")
                    io_dialog.finish()  # 设置完成状态，但不关闭对话框
                    io_dialog.exec()  # 使用exec()而不是show()，等待用户关闭
                    return
            elif file_path.endswith('.csv'):
                try:
                    df = pd.read_csv(file_path)
                except Exception as e:
                    io_dialog.add_error(f"读取CSV文件失败: {str(e)}")
                    io_dialog.finish()
                    io_dialog.exec()
                    return
            else:
                io_dialog.add_error("不支持的文件格式")
                io_dialog.finish()
                io_dialog.exec()
                return
            
            # 创建SignImportManager实例
            from src.core.sign_import_manager import SignImportManager
            
            # 简化创建过程，移除不必要的企业信息获取
            import_manager = SignImportManager(self.db_manager)
            
            try:
                # 在一个会话中执行整个导入过程，以避免会话分离问题
                with self.db_manager.get_session() as session:
                    # 重新获取直播记录
                    live_record = session.query(Living).filter_by(livingid=live.livingid).first()
                    if not live_record:
                        io_dialog.add_error("找不到直播记录")
                        io_dialog.finish()
                        io_dialog.exec()
                        return
                    
                    # 添加进度信息
                    io_dialog.add_info(f"开始导入直播 \"{live_record.theme}\" 的签到数据...")
                    io_dialog.add_info(f"直播ID: {live_record.livingid}")
                    io_dialog.add_info(f"直播时间: {live_record.living_start}")
                    
                    # 导入签到数据，传递 live_record.id，确保它仍然与会话关联
                    import_results = import_manager.import_sign_data(file_path, live_record.id)
                    
                    # 解析导入结果
                    success_count = import_results.get('success_count', 0)
                    error_count = import_results.get('error_count', 0)
                    skipped_count = import_results.get('skipped_count', 0)
                    success_details = import_results.get('success_details', [])
                    error_details = import_results.get('error_details', [])
                    skipped_details = import_results.get('skipped_details', [])
                    
                    # 设置签到导入标志
                    live_record.is_sign_imported = 1
                    session.commit()
            except Exception as e:
                io_dialog.add_error(f"导入过程中发生错误: {str(e)}")
                import traceback
                io_dialog.add_error(f"错误详情: {traceback.format_exc()}")
                io_dialog.finish()
                io_dialog.exec()
                return
            
            # 显示导入结果
            io_dialog.add_info("\n===== 导入过程完成 =====")
            
            # 显示成功记录
            if success_count > 0:
                io_dialog.add_success(f"✓ 成功导入 {success_count} 条签到记录")
                # 显示成功详情（限制显示数量以避免过多）
                max_success_details = 10
                if success_details:
                    io_dialog.add_info(f"成功详情（显示前{min(len(success_details), max_success_details)}条，共{len(success_details)}条）:")
                    for detail in success_details[:max_success_details]:
                        io_dialog.add_success(f"  ✓ {detail}")
                    if len(success_details) > max_success_details:
                        io_dialog.add_info(f"  ... 还有 {len(success_details) - max_success_details} 条成功记录未显示")
            else:
                io_dialog.add_warning("没有成功导入的记录")
            
            # 显示跳过记录
            if skipped_count > 0:
                io_dialog.add_warning(f"⚠ 跳过 {skipped_count} 条重复记录")
                # 显示跳过详情
                if skipped_details:
                    max_skipped_details = 10
                    io_dialog.add_warning(f"跳过详情（显示前{min(len(skipped_details), max_skipped_details)}条，共{len(skipped_details)}条）:")
                    for detail in skipped_details[:max_skipped_details]:
                        io_dialog.add_warning(f"  ⚠ {detail}")
                    if len(skipped_details) > max_skipped_details:
                        io_dialog.add_warning(f"  ... 还有 {len(skipped_details) - max_skipped_details} 条跳过记录未显示")
            
            # 显示错误记录
            if error_count > 0:
                io_dialog.add_error(f"✗ 导入失败 {error_count} 条记录")
                # 显示错误详情
                if error_details:
                    max_error_details = 10
                    io_dialog.add_error(f"错误详情（显示前{min(len(error_details), max_error_details)}条，共{len(error_details)}条）:")
                    for detail in error_details[:max_error_details]:
                        io_dialog.add_error(f"  ✗ {detail}")
                    if len(error_details) > max_error_details:
                        io_dialog.add_error(f"  ... 还有 {len(error_details) - max_error_details} 条错误记录未显示")
            
            # 添加总结信息
            io_dialog.add_info("\n===== 导入结果总结 =====")
            io_dialog.add_info(f"总处理记录: {success_count + error_count + skipped_count}")
            io_dialog.add_success(f"成功导入: {success_count}")
            io_dialog.add_warning(f"跳过记录: {skipped_count}")
            io_dialog.add_error(f"导入失败: {error_count}")
            
            # 完成导入过程，但不自动关闭对话框
            io_dialog.finish()
            
            # 使用exec()方法显示对话框，并等待用户手动关闭
            io_dialog.exec()
            
            # 刷新数据
            self.load_data()
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "导入签到失败")
            
    @PerformanceManager.measure_operation("fetch_watch_stat")
    def fetch_watch_stat(self, live: Living):
        """拉取直播观看信息"""
        logger.info("开始拉取直播观看信息")
        
        try:
            # 显示确认对话框
            confirm_box = QMessageBox(self)
            confirm_box.setIcon(QMessageBox.Icon.Question)
            confirm_box.setWindowTitle("确认拉取")
            confirm_box.setText(f"确定要拉取直播[{live.theme}]的观看信息吗？")
            confirm_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            confirm_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            if confirm_box.exec() != QMessageBox.StandardButton.Yes:
                return
            
            # 显示进度对话框
            dialog = IODialog(parent=self, title="拉取观看信息", is_import=False, is_progress_dialog=True)
            dialog.show()
            dialog.add_info(f"正在拉取直播[{live.theme}]的观看信息...")
            
            # 创建LiveViewerManager实例
            from src.core.live_viewer_manager import LiveViewerManager
            viewer_manager = LiveViewerManager(
                self.db_manager,
                self.auth_manager
            )
            
            # 拉取观看信息 - 移除外部token参数，使用系统自动处理token
            success = viewer_manager.process_viewer_info(live.livingid)
            
            # 获取统计数据
            stats = viewer_manager.get_stats()
            
            # 检查是否成功拉取数据
            if not success:
                # 显示错误信息
                error_message = stats.get('last_error', '未知错误')
                dialog.add_error(f"观看数据拉取失败：{error_message}")
                dialog.finish()
                return
            
            # 检查是否有观众数据
            if stats.get('total_viewers', 0) == 0:
                dialog.add_warning("未获取到任何观看数据，请确认该直播有人观看")
                dialog.finish()
                
                # 尽管没有观众数据，仍然更新直播的拉取状态
                with self.db_manager.get_session() as session:
                    living_record = session.query(Living).filter_by(livingid=live.livingid).first()
                    if living_record:
                        living_record.is_viewer_fetched = 1
                        session.commit()
                        
                # 重新加载直播列表
                self.load_data()
                return
            
            # 显示成功信息
            dialog.add_success(f"观看数据拉取成功！")
            dialog.add_info(f"总观看人数: {stats.get('total_viewers', 0)}")
            dialog.add_info(f"内部成员: {stats.get('internal_viewers', 0)}")
            dialog.add_info(f"外部用户: {stats.get('external_viewers', 0)}")
                
            # 更新直播的拉取状态
            with self.db_manager.get_session() as session:
                living_record = session.query(Living).filter_by(livingid=live.livingid).first()
                if living_record:
                    living_record.is_viewer_fetched = 1
                    session.commit()
                    dialog.add_success("已更新拉取状态标记")
            
            # 重新加载直播列表
            self.load_data()
            
            # 完成操作
            dialog.finish()
            
            # 显示成功消息
            msg_box = AutoCloseMessageBox(
                "拉取成功", 
                f"已成功拉取直播[{live.theme}]的观看信息", 
                timeout=3000
            )
            msg_box.exec()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "拉取观看信息失败")
            
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
                
            # 获取所有直播记录
            with self.db_manager.get_session() as session:
                result = session.execute(select(Living))
                records = result.scalars().all()
                
                # 创建DataFrame
                data = []
                for record in records:
                    # 计算结束时间
                    end_time = ""
                    if record.living_start and record.living_duration:
                        end_time = (record.living_start + timedelta(seconds=record.living_duration)).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 获取主播的名称
                    from src.models.user import User
                    user = session.query(User).filter(
                        (User.wecom_code == record.anchor_userid) | 
                        (User.login_name == record.anchor_userid)
                    ).first()
                    
                    anchor_name = f"{user.name}({record.anchor_userid})" if user else record.anchor_userid
                    
                    # 获取签到统计信息
                    from src.models.live_viewer import LiveViewer
                    # 使用 LiveViewer 查询签到统计
                    sign_stats = {}
                    with self.db_manager.get_session() as stats_session:
                        # 获取不同的签到人数
                        unique_signers = stats_session.query(func.count(LiveViewer.id)).filter(
                            LiveViewer.living_id == record.id,
                            LiveViewer.is_signed == True
                        ).scalar() or 0
                        
                        # 获取总签到次数
                        sign_count = stats_session.query(func.sum(LiveViewer.sign_count)).filter(
                            LiveViewer.living_id == record.id,
                            LiveViewer.is_signed == True
                        ).scalar() or 0
                        
                        # 获取首次签到时间
                        first_sign = stats_session.query(func.min(LiveViewer.sign_time)).filter(
                            LiveViewer.living_id == record.id,
                            LiveViewer.is_signed == True
                        ).scalar()
                        
                        sign_stats = {
                            "unique_signers": unique_signers,
                            "sign_count": sign_count,
                            "sign_time": first_sign
                        }
                    
                    record_data["sign_count"] = sign_stats["unique_signers"]  # 使用unique_signers作为签到人数
                    record_data["total_sign_count"] = sign_stats["sign_count"]  # 总签到次数
                    record_data["sign_time"] = sign_stats["sign_time"]
                    
                    # 获取直播类型
                    type_text = {
                        LivingType.GENERAL: "通用直播",
                        LivingType.SMALL: "小班课",
                        LivingType.LARGE: "大班课",
                        LivingType.TRAINING: "企业培训",
                        LivingType.EVENT: "活动直播"
                    }.get(record.type, "未知")
                    
                    data.append({
                        "直播ID": record.livingid,
                        "直播标题": record.theme,
                        "开始时间": record.living_start.strftime("%Y-%m-%d %H:%M:%S") if record.living_start else "",
                        "结束时间": end_time,
                        "主播": anchor_name,
                        "状态": {
                            LivingStatus.RESERVED: "预约中",
                            LivingStatus.LIVING: "直播中",
                            LivingStatus.ENDED: "已结束",
                            LivingStatus.EXPIRED: "已过期",
                            LivingStatus.CANCELLED: "已取消"
                        }.get(record.status, "未知"),
                        "直播类型": type_text,
                        "观看人数": record.viewer_num,
                        "评论数": record.comment_num,
                        "签到人数": sign_stats["unique_signers"],  # 不同的签到人数
                        "签到次数": sign_stats["sign_count"],      # 总签到次数
                        "首次签到时间": sign_stats["sign_time"] if sign_stats["sign_time"] else "-",
                        "已拉取观看信息": "是" if record.is_viewer_fetched == 1 else "否",
                        "已导入签到": "是" if record.is_sign_imported == 1 else "否",
                        "已上传企微文档": "是" if record.is_doc_uploaded == 1 else "否",
                        "已远程同步": "是" if record.is_remote_synced == 1 else "否",
                        "记录创建时间": record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else "",
                        "记录更新时间": record.updated_at.strftime("%Y-%m-%d %H:%M:%S") if record.updated_at else ""
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
        
    def reset_search(self):
        """重置搜索条件并刷新数据"""
        # 清空所有搜索条件
        self.live_title.clear()
        self.live_status.setCurrentIndex(0)  # 设置为"全部"
        
        # 重置新增的状态字段
        self.viewer_fetched_status.setCurrentIndex(0)  # 设置为"全部"
        self.sign_imported_status.setCurrentIndex(0)  # 设置为"全部"
        self.doc_uploaded_status.setCurrentIndex(0)  # 设置为"全部"
        self.remote_synced_status.setCurrentIndex(0)  # 设置为"全部"
        
        # 重置日期时间范围
        self.start_date_time.setDateTime(QDateTime.currentDateTime().addMonths(-1))
        self.end_date_time.setDateTime(QDateTime.currentDateTime())
        
        # 重置页码
        self.current_page = 1
        
        # 重新加载数据
        self.load_data()

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setObjectName("toolbar")
        return toolbar

class LiveDetailsDialog(QDialog):
    """直播详情对话框"""
    
    def __init__(self, live_info: Living, parent=None):
        super().__init__(parent)
        self.live_info = live_info  # 现在直接接收Living对象
        from src.core.database import DatabaseManager
        self.db_manager = DatabaseManager()  # 直接创建实例而不是调用get_db方法
        # 打印日志，检查状态值
        logger.debug(f"LiveDetailsDialog初始化 - 状态值: is_remote_synced={self.live_info.is_remote_synced}")
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("直播详情")
        self.setMinimumWidth(600)
        
        # 创建主布局（使用垂直布局）
        main_layout = QVBoxLayout(self)
        
        # 创建分组盒子 - 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(10)
        
        # 添加基本信息
        basic_layout.addRow("直播主题:", QLabel(self.live_info.theme))
        
        # 显示living_start和结束时间
        start_time_str = self.live_info.living_start.strftime("%Y-%m-%d %H:%M:%S") if self.live_info.living_start else ""
        basic_layout.addRow("开始时间:", QLabel(start_time_str))
        
        # 计算结束时间
        end_time = None
        if self.live_info.living_start and self.live_info.living_duration:
            end_time = self.live_info.living_start + timedelta(seconds=self.live_info.living_duration)
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
            basic_layout.addRow("结束时间:", QLabel(end_time_str))
        
        # 直播时长（转换为分钟和小时）
        if self.live_info.living_duration:
            hours = self.live_info.living_duration // 3600
            minutes = (self.live_info.living_duration % 3600) // 60
            seconds = self.live_info.living_duration % 60
            duration_str = ""
            if hours > 0:
                duration_str += f"{hours}小时"
            if minutes > 0:
                duration_str += f"{minutes}分钟"
            if seconds > 0 or duration_str == "":
                duration_str += f"{seconds}秒"
            basic_layout.addRow("直播时长:", QLabel(duration_str))
        
        # 主播信息
        try:
            from src.models.user import User
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(
                    (User.wecom_code == self.live_info.anchor_userid) | 
                    (User.login_name == self.live_info.anchor_userid)
                ).first()
                if user:
                    anchor_name = f"{user.name}({self.live_info.anchor_userid})"
                else:
                    anchor_name = self.live_info.anchor_userid
                basic_layout.addRow("主播:", QLabel(anchor_name))
        except Exception as e:
            basic_layout.addRow("主播ID:", QLabel(self.live_info.anchor_userid))
            
        # 直播类型
        type_text = {
            LivingType.GENERAL: "通用直播",
            LivingType.SMALL: "小班课",
            LivingType.LARGE: "大班课",
            LivingType.TRAINING: "企业培训",
            LivingType.EVENT: "活动直播"
        }.get(self.live_info.type, "未知")
        basic_layout.addRow("直播类型:", QLabel(type_text))
        
        # 状态
        status_text = {
            LivingStatus.RESERVED: "预约中",
            LivingStatus.LIVING: "直播中",
            LivingStatus.ENDED: "已结束",
            LivingStatus.EXPIRED: "已过期",
            LivingStatus.CANCELLED: "已取消"
        }.get(self.live_info.status, "未知")
        basic_layout.addRow("状态:", QLabel(status_text))
        
        # 企业信息
        basic_layout.addRow("企业名称:", QLabel(self.live_info.corpname))
        
        # 描述
        if self.live_info.description:
            desc_label = QLabel(self.live_info.description)
            desc_label.setWordWrap(True)  # 允许文本自动换行
            basic_layout.addRow("直播描述:", desc_label)
            
        # 状态标记
        status_layout = QHBoxLayout()
        status_layout.setSpacing(15)
        
        # 是否拉取观看信息
        viewer_fetched_status = "已拉取" if self.live_info.is_viewer_fetched == 1 else "未拉取"
        viewer_label = QLabel(f"观看信息: {viewer_fetched_status}")
        viewer_label.setStyleSheet(f"color: {'green' if self.live_info.is_viewer_fetched == 1 else 'red'}")
        status_layout.addWidget(viewer_label)
        
        # 是否导入签到
        sign_imported_status = "已导入" if self.live_info.is_sign_imported == 1 else "未导入"
        sign_label = QLabel(f"签到导入: {sign_imported_status}")
        sign_label.setStyleSheet(f"color: {'green' if self.live_info.is_sign_imported == 1 else 'red'}")
        status_layout.addWidget(sign_label)
        
        # 是否上传企微文档
        doc_uploaded_status = "已上传" if self.live_info.is_doc_uploaded == 1 else "未上传"
        doc_label = QLabel(f"企微文档: {doc_uploaded_status}")
        doc_label.setStyleSheet(f"color: {'green' if self.live_info.is_doc_uploaded == 1 else 'red'}")
        status_layout.addWidget(doc_label)
        
        # 是否远程同步
        remote_synced_status = "已同步" if self.live_info.is_remote_synced == 1 else "未同步"
        remote_label = QLabel(f"远程同步: {remote_synced_status}")
        remote_label.setStyleSheet(f"color: {'green' if self.live_info.is_remote_synced == 1 else 'red'}")
        status_layout.addWidget(remote_label)
        
        # 添加状态布局
        basic_layout.addRow("数据状态:", status_layout)
            
        # 添加基本信息组到主布局
        main_layout.addWidget(basic_group)
        
        # 创建分组盒子 - 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QFormLayout(stats_group)
        stats_layout.setSpacing(10)
        
        # 视频统计
        stats_layout.addRow("观看人数:", QLabel(str(self.live_info.viewer_num)))
        stats_layout.addRow("评论数:", QLabel(str(self.live_info.comment_num)))
        stats_layout.addRow("连麦人数:", QLabel(str(self.live_info.mic_num)))
        stats_layout.addRow("当前在线人数:", QLabel(str(self.live_info.online_count)))
        stats_layout.addRow("预约人数:", QLabel(str(self.live_info.subscribe_count)))
        
        # 签到统计
        if hasattr(self.live_info, 'sign_count'):
            stats_layout.addRow("签到人数:", QLabel(str(self.live_info.sign_count)))
        if hasattr(self.live_info, 'total_sign_count'):
            stats_layout.addRow("签到次数:", QLabel(str(self.live_info.total_sign_count)))
        if hasattr(self.live_info, 'sign_time') and self.live_info.sign_time:
            stats_layout.addRow("首次签到时间:", QLabel(str(self.live_info.sign_time)))
            
            # 计算首次签到相对于直播开始的时间
            if self.live_info.living_start:
                try:
                    from datetime import datetime
                    sign_time = datetime.strptime(self.live_info.sign_time, "%Y.%m.%d %H:%M")
                    time_diff = sign_time - self.live_info.living_start
                    minutes_diff = time_diff.total_seconds() // 60
                    if minutes_diff > 0:
                        stats_layout.addRow("首签距直播开始:", QLabel(f"{int(minutes_diff)}分钟后"))
                    elif minutes_diff < 0:
                        stats_layout.addRow("首签距直播开始:", QLabel(f"{int(abs(minutes_diff))}分钟前"))
                    else:
                        stats_layout.addRow("首签距直播开始:", QLabel("同时"))
                except Exception:
                    pass  # 忽略日期解析错误
        
        # 添加统计信息组到主布局
        main_layout.addWidget(stats_group)
        
        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        # 设置窗口大小
        self.setMinimumHeight(500) 