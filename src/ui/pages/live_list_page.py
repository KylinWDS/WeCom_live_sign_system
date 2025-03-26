from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QSpinBox, QHeaderView,
    QFileDialog, QDialog, QFormLayout, QGroupBox,
    QDateEdit, QTimeEdit, QToolBar, QSpacerItem, QSizePolicy
)
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
from src.models.living import Living, LivingStatus
from datetime import datetime, timedelta
from src.ui.components.dialogs.io_dialog import IODialog
import pandas as pd
import os

logger = get_logger(__name__)

class LiveListPage(QWidget):
    """直播列表页面"""
    
    def __init__(self, db_manager: DatabaseManager, wecom_api: WeComAPI):
        super().__init__()
        self.db_manager = db_manager
        self.wecom_api = wecom_api
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("liveListPage")
        
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
                query = session.query(Living)
                
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
                    
                # 计算总页数
                total = query.count()
                self.total_pages = (total + self.page_size - 1) // self.page_size
                
                # 获取当前页数据
                records = query.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
                
            # 更新表格
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(record.livingid))
                self.table.setItem(row, 1, QTableWidgetItem(record.theme))
                self.table.setItem(row, 2, QTableWidgetItem(record.living_start.strftime("%Y-%m-%d %H:%M:%S")))
                self.table.setItem(row, 3, QTableWidgetItem(record.status))
                self.table.setItem(row, 4, QTableWidgetItem(str(record.viewer_num)))
                self.table.setItem(row, 5, QTableWidgetItem(str(record.comment_num)))
                self.table.setItem(row, 6, QTableWidgetItem(str(record.mic_num)))
                
                # 状态
                status_text = {
                    LivingStatus.RESERVED: "预约中",
                    LivingStatus.LIVING: "直播中",
                    LivingStatus.ENDED: "已结束",
                    LivingStatus.EXPIRED: "已过期",
                    LivingStatus.CANCELLED: "已取消"
                }.get(record.status, "未知")
                self.table.setItem(row, 7, QTableWidgetItem(status_text))
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                
                view_btn = QPushButton("查看")
                view_btn.setObjectName("linkButton")
                view_btn.clicked.connect(lambda checked, r=record: self.view_details(r))
                btn_layout.addWidget(view_btn)
                
                import_btn = QPushButton("导入签到")
                import_btn.setObjectName("linkButton")
                import_btn.clicked.connect(lambda checked, r=record: self.import_sign(r))
                btn_layout.addWidget(import_btn)
                
                cancel_btn = QPushButton("取消")
                cancel_btn.setObjectName("linkButton")
                cancel_btn.clicked.connect(lambda checked, r=record: self.cancel_live(r))
                btn_layout.addWidget(cancel_btn)
                
                self.table.setCellWidget(row, 8, btn_widget)
                
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
            # 获取直播详情
            response = self.network_manager.get(
                "https://qyapi.weixin.qq.com/cgi-bin/living/get_living_info",
                params={"livingid": live.livingid}
            )
            
            if response.get("errcode") == 0:
                # 更新直播信息
                live_info = response["living_info"]
                with self.db_manager.get_session() as session:
                    live.viewer_num = live_info["viewer_num"]
                    live.comment_num = live_info["comment_num"]
                    live.mic_num = live_info["mic_num"]
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
            
    @PerformanceManager.measure_operation("import_sign")
    def import_sign(self, live: Living):
        """导入签到信息
        
        Args:
            live: 直播信息
        """
        try:
            # 选择Excel文件
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择签到数据文件",
                "",
                "Excel Files (*.xlsx *.xls)"
            )
            if not file_path:
                return
                
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 验证数据
            required_columns = ["用户ID", "用户名", "签到时间"]
            if not all(col in df.columns for col in required_columns):
                ErrorHandler.handle_warning("文件格式不正确", self)
                return
                
            # 导入数据
            with self.db_manager.get_session() as session:
                for _, row in df.iterrows():
                    sign = SignRecord(
                        living_id=live.livingid,
                        user_id=row["用户ID"],
                        username=row["用户名"],
                        sign_time=pd.to_datetime(row["签到时间"])
                    )
                    session.add(sign)
                session.commit()
                
            ErrorHandler.handle_info("导入签到信息成功", self, "成功")
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "导入签到信息失败")
            
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
            response = self.network_manager.post(
                "https://qyapi.weixin.qq.com/cgi-bin/living/cancel",
                json={"livingid": live.livingid}
            )
            
            if response.get("errcode") == 0:
                # 更新直播状态
                with self.db_manager.get_session() as session:
                    live.status = LivingStatus.CANCELLED
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
                records = session.query(Living).all()
                
            # 创建DataFrame
            data = []
            for record in records:
                # 计算结束时间
                end_time = ""
                if record.living_start and record.living_duration:
                    end_time = (record.living_start + timedelta(seconds=record.living_duration)).strftime("%Y-%m-%d %H:%M:%S")
                
                data.append({
                    "直播场次": record.livingid,
                    "开始时间": record.living_start.strftime("%Y-%m-%d %H:%M:%S") if record.living_start else "",
                    "结束时间": end_time,
                    "主播": record.anchor_userid,
                    "观看人数": record.viewer_num,
                    "评论数": record.comment_num,
                    "连麦人数": record.mic_num,
                    "状态": {
                        LivingStatus.RESERVED: "预约中",
                        LivingStatus.LIVING: "直播中",
                        LivingStatus.ENDED: "已结束",
                        LivingStatus.EXPIRED: "已过期",
                        LivingStatus.CANCELLED: "已取消"
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

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setObjectName("toolbar")
        
        # 添加刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh_data)
        toolbar.addWidget(refresh_button)
        
        # 添加导出按钮
        export_button = QPushButton("导出数据")
        export_button.setObjectName("primaryButton")
        export_button.clicked.connect(self.export_data)
        toolbar.addWidget(export_button)
        
        return toolbar

class LiveDetailDialog(QDialog):
    """直播详情对话框"""
    
    def __init__(self, live_info: dict, parent=None):
        super().__init__(parent)
        self.live_info = live_info
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("直播详情")
        self.setMinimumWidth(600)
        
        layout = QFormLayout(self)
        layout.setSpacing(10)
        
        # 添加详情信息
        layout.addRow("直播主题:", QLabel(self.live_info["theme"]))
        layout.addRow("开始时间:", QLabel(datetime.fromtimestamp(self.live_info["living_start"]).strftime("%Y-%m-%d %H:%M:%S")))
        layout.addRow("直播时长:", QLabel(f"{self.live_info['living_duration']}秒"))
        layout.addRow("主播ID:", QLabel(self.live_info["anchor_userid"]))
        layout.addRow("观看人数:", QLabel(str(self.live_info["viewer_num"])))
        layout.addRow("评论数:", QLabel(str(self.live_info["comment_num"])))
        layout.addRow("连麦人数:", QLabel(str(self.live_info["mic_num"])))
        layout.addRow("状态:", QLabel({
            LivingStatus.RESERVED: "预约中",
            LivingStatus.LIVING: "直播中",
            LivingStatus.ENDED: "已结束",
            LivingStatus.EXPIRED: "已过期",
            LivingStatus.CANCELLED: "已取消"
        }.get(self.live_info["status"], "未知")))
        
        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        layout.addRow("", close_btn) 