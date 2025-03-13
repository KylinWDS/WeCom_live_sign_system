# 标准库导入
import os
import pandas as pd

# PySide6导入
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QFileDialog, QGroupBox,
                             QDateEdit, QTimeEdit, QSpinBox, QComboBox,
                             QDialog, QLineEdit, QFormLayout)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QIcon

# UI相关导入
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from ..managers.animation import AnimationManager

# 核心功能导入
from src.utils.logger import get_logger
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.core.database import DatabaseManager
from src.core.network_manager import NetworkManager
from src.models.live import Live

logger = get_logger(__name__)

class LivePage(QWidget):
    """直播管理页面"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.network_manager = NetworkManager()
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("livePage")
        
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
        self.setStyleSheet(StyleManager.get_live_style())
        
        # 添加淡入动画
        AnimationManager.fade_in(self)
        
        # 加载数据
        self.load_data()
        
    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建直播按钮
        create_btn = QPushButton("创建直播")
        create_btn.setObjectName("primaryButton")
        create_btn.setIcon(QIcon(":/icons/add.png"))
        create_btn.clicked.connect(self.create_live)
        layout.addWidget(create_btn)
        
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
        
    @PerformanceManager.measure_operation("load_data")
    def load_data(self):
        """加载数据"""
        try:
            # 获取直播列表
            with self.db_manager.get_session() as session:
                query = session.query(Live)
                
                # 应用搜索条件
                if self.live_title.text():
                    query = query.filter(Live.title.like(f"%{self.live_title.text()}%"))
                    
                if self.live_status.currentText() != "全部":
                    status_map = {
                        "未开始": 0,
                        "进行中": 1,
                        "已结束": 2
                    }
                    query = query.filter_by(status=status_map[self.live_status.currentText()])
                    
                # 计算总页数
                total = query.count()
                self.total_pages = (total + self.page_size - 1) // self.page_size
                
                # 获取当前页数据
                records = query.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
                
            # 更新表格
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(record.live_session))
                self.table.setItem(row, 1, QTableWidgetItem(record.title))
                self.table.setItem(row, 2, QTableWidgetItem(record.start_time.strftime("%Y-%m-%d %H:%M:%S")))
                self.table.setItem(row, 3, QTableWidgetItem(str(record.status)))
                self.table.setItem(row, 4, QTableWidgetItem(str(record.viewer_num)))
                self.table.setItem(row, 5, QTableWidgetItem(str(record.comment_num)))
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                
                view_btn = QPushButton("查看")
                view_btn.setObjectName("linkButton")
                view_btn.clicked.connect(lambda checked, r=record: self.view_details(r))
                btn_layout.addWidget(view_btn)
                
                cancel_btn = QPushButton("取消")
                cancel_btn.setObjectName("linkButton")
                cancel_btn.clicked.connect(lambda checked, r=record: self.cancel_live(r))
                btn_layout.addWidget(cancel_btn)
                
                self.table.setCellWidget(row, 6, btn_widget)
                
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
            
    @PerformanceManager.measure_operation("create_live")
    def create_live(self):
        """创建直播"""
        try:
            # 创建直播对话框
            dialog = LiveCreateDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取直播信息
                live_info = dialog.get_live_info()
                
                # 创建直播
                response = self.network_manager.post(
                    "https://qyapi.weixin.qq.com/cgi-bin/living/create",
                    json=live_info
                )
                
                if response.get("errcode") == 0:
                    # 保存直播信息
                    with self.db_manager.get_session() as session:
                        live = Live(
                            live_session=response["livingid"],
                            start_time=QDateTime.fromSecsSinceEpoch(live_info["living_start"]),
                            end_time=QDateTime.fromSecsSinceEpoch(
                                live_info["living_start"] + live_info["living_duration"]
                            ),
                            anchor=live_info["anchor_userid"],
                            status=0  # 预约中
                        )
                        session.add(live)
                        session.commit()
                        
                    ErrorHandler.handle_info("创建直播成功", self, "成功")
                    self.load_data()
                    
                else:
                    ErrorHandler.handle_warning(
                        f"创建直播失败：{response.get('errmsg')}",
                        self,
                        "失败"
                    )
                    
        except Exception as e:
            ErrorHandler.handle_error(e, self, "创建直播失败")
            
    @PerformanceManager.measure_operation("view_details")
    def view_details(self, live: Live):
        """查看直播详情
        
        Args:
            live: 直播信息
        """
        try:
            # 获取直播详情
            response = self.network_manager.get(
                "https://qyapi.weixin.qq.com/cgi-bin/living/get_living_info",
                params={"livingid": live.live_session}
            )
            
            if response.get("errcode") == 0:
                # 更新直播信息
                live_info = response["living_info"]
                with self.db_manager.get_session() as session:
                    live.viewer_num = live_info["viewer_num"]
                    live.comment_num = live_info["comment_num"]
                    live.status = live_info["status"]
                    session.commit()
                    
                # 显示详情对话框
                dialog = LiveDetailsDialog(live, self)
                dialog.exec()
                
            else:
                ErrorHandler.handle_warning(
                    f"获取直播详情失败：{response.get('errmsg')}",
                    self,
                    "失败"
                )
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "查看直播详情失败")
            
    @PerformanceManager.measure_operation("cancel_live")
    def cancel_live(self, live: Live):
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
            response = self.network_manager.post(
                "https://qyapi.weixin.qq.com/cgi-bin/living/cancel",
                json={"livingid": live.live_session}
            )
            
            if response.get("errcode") == 0:
                # 更新直播状态
                with self.db_manager.get_session() as session:
                    live.status = 4  # 已取消
                    session.commit()
                    
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
                records = session.query(Live).all()
                
            # 创建DataFrame
            data = []
            for record in records:
                data.append({
                    "直播场次": record.live_session,
                    "开始时间": record.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "结束时间": record.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "主播": record.anchor,
                    "观看人数": record.viewer_num,
                    "评论数": record.comment_num,
                    "状态": {
                        0: "预约中",
                        1: "直播中",
                        2: "已结束",
                        3: "已过期",
                        4: "已取消"
                    }.get(record.status, "未知")
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

class LiveCreateDialog(QDialog):
    """创建直播对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("创建直播")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        layout.setSpacing(10)
        
        # 主播ID
        self.anchor = QLineEdit()
        WidgetUtils.set_input_style(self.anchor)
        layout.addRow("主播ID:", self.anchor)
        
        # 直播标题
        self.title = QLineEdit()
        WidgetUtils.set_input_style(self.title)
        layout.addRow("直播标题:", self.title)
        
        # 开始时间
        self.start_time = QDateTimeEdit()
        self.start_time.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # 默认1小时后开始
        self.start_time.setCalendarPopup(True)
        WidgetUtils.set_date_style(self.start_time)
        layout.addRow("开始时间:", self.start_time)
        
        # 直播时长
        self.duration = QSpinBox()
        self.duration.setRange(60, 7200)  # 1分钟到2小时
        self.duration.setValue(3600)  # 默认1小时
        WidgetUtils.set_spin_style(self.duration)
        layout.addRow("直播时长(秒):", self.duration)
        
        # 直播类型
        self.type = QComboBox()
        self.type.addItems(["通用直播", "小班课", "大班课", "企业培训", "活动直播"])
        WidgetUtils.set_combo_style(self.type)
        layout.addRow("直播类型:", self.type)
        
        # 直播简介
        self.description = QLineEdit()
        WidgetUtils.set_input_style(self.description)
        layout.addRow("直播简介:", self.description)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow("", button_layout)
        
    def get_live_info(self) -> dict:
        """获取直播信息"""
        return {
            "anchor_userid": self.anchor.text(),
            "theme": self.title.text(),
            "living_start": int(self.start_time.dateTime().toSecsSinceEpoch()),
            "living_duration": self.duration.value(),
            "type": self.type.currentIndex(),
            "description": self.description.text(),
            "agentid": 1000002  # TODO: 从配置获取
        }