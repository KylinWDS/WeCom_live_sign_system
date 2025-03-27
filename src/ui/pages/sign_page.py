from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QCheckBox,
                             QDateEdit, QTimeEdit, QSpinBox)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from utils.logger import get_logger
from ..managers.animation import AnimationManager
from utils.performance_manager import PerformanceManager
from utils.error_handler import ErrorHandler
from core.database import DatabaseManager
from models.live_viewer import LiveViewer
from ..dialogs.io_dialog import IODialog
import pandas as pd
import os

logger = get_logger(__name__)

class SignImportDialog(IODialog):
    """签到信息导入对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "导入签到信息", 400, 300)
        
    def get_file_path(self) -> str:
        """获取文件路径
        
        Returns:
            文件路径
        """
        return self.file_path.text()

class SignPage(QWidget):
    """签到管理页面"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("signPage")
        
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
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "直播场次", "签到时间", "签到人数", "签到成员", "所在部门",
            "签到次数", "观看时长", "操作"
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
        self.setStyleSheet(StyleManager.get_sign_style())
        
        # 添加淡入动画
        AnimationManager.fade_in(self)
        
        # 加载数据
        self.current_page = 1
        self.page_size = 10
        self.load_data()
        
    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 导入按钮
        import_btn = QPushButton("导入签到")
        import_btn.setObjectName("primaryButton")
        import_btn.setIcon(QIcon(":/icons/import.png"))
        import_btn.clicked.connect(self.import_sign)
        layout.addWidget(import_btn)
        
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
        
        # 直播场次
        row1_layout.addWidget(QLabel("直播场次:"))
        self.live_session = QLineEdit()
        WidgetUtils.set_input_style(self.live_session)
        row1_layout.addWidget(self.live_session)
        
        # 签到时间
        row1_layout.addWidget(QLabel("签到时间:"))
        self.sign_date = QDateEdit()
        self.sign_date.setCalendarPopup(True)
        self.sign_date.setDate(QDate.currentDate())
        WidgetUtils.set_date_style(self.sign_date)
        row1_layout.addWidget(self.sign_date)
        
        layout.addLayout(row1_layout)
        
        # 第二行
        row2_layout = QHBoxLayout()
        
        # 签到成员
        row2_layout.addWidget(QLabel("签到成员:"))
        self.member = QLineEdit()
        WidgetUtils.set_input_style(self.member)
        row2_layout.addWidget(self.member)
        
        # 所在部门
        row2_layout.addWidget(QLabel("所在部门:"))
        self.department = QLineEdit()
        WidgetUtils.set_input_style(self.department)
        row2_layout.addWidget(self.department)
        
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
            # 获取签到记录列表
            with self.db_manager.get_session() as session:
                query = session.query(LiveViewer).filter(LiveViewer.is_signed == True)
                
                # 应用搜索条件
                if self.live_session.text():
                    query = query.filter(LiveViewer.living.has(title=f"%{self.live_session.text()}%"))
                    
                if self.sign_date.date():
                    query = query.filter(LiveViewer.sign_time >= self.sign_date.date().toPyDate())
                    
                if self.member.text():
                    query = query.filter(LiveViewer.username.like(f"%{self.member.text()}%"))
                    
                if self.department.text():
                    query = query.filter(LiveViewer.department.like(f"%{self.department.text()}%"))
                    
                # 计算总页数
                total = query.count()
                self.total_pages = (total + self.page_size - 1) // self.page_size
                
                # 获取当前页数据
                records = query.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
                
            # 更新表格
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                live_title = record.living.title if record.living else "未知直播"
                self.table.setItem(row, 0, QTableWidgetItem(live_title))
                self.table.setItem(row, 1, QTableWidgetItem(record.sign_time.strftime("%Y-%m-%d %H:%M:%S") if record.sign_time else ""))
                self.table.setItem(row, 2, QTableWidgetItem("-"))  # 此字段在新模型中不存在
                self.table.setItem(row, 3, QTableWidgetItem(record.username))
                self.table.setItem(row, 4, QTableWidgetItem(record.department))
                self.table.setItem(row, 5, QTableWidgetItem(str(record.sign_count)))
                self.table.setItem(row, 6, QTableWidgetItem(f"{record.watch_duration}分钟"))
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                
                detail_btn = QPushButton("详情")
                detail_btn.setObjectName("linkButton")
                detail_btn.clicked.connect(lambda checked, r=record: self.show_detail(r))
                btn_layout.addWidget(detail_btn)
                
                delete_btn = QPushButton("删除")
                delete_btn.setObjectName("linkButton")
                delete_btn.clicked.connect(lambda checked, r=record: self.delete_record(r))
                btn_layout.addWidget(delete_btn)
                
                self.table.setCellWidget(row, 7, btn_widget)
                
            # 更新分页信息
            self.page_label.setText(f"第 {self.current_page} 页 / 共 {self.total_pages} 页")
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < self.total_pages)
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "加载签到记录失败")
            
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
            
    @PerformanceManager.measure_operation("import_sign")
    def import_sign(self):
        """导入签到信息"""
        try:
            # 创建导入对话框
            dialog = SignImportDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取文件路径
                file_path = dialog.get_file_path()
                if not file_path:
                    return
                    
                # 读取Excel文件
                df = pd.read_excel(file_path)
                
                # 导入数据
                with self.db_manager.get_session() as session:
                    for _, row in df.iterrows():
                        # 创建或更新LiveViewer记录
                        viewer = LiveViewer(
                            username=row["签到成员"],
                            department=row["所在部门"],
                            sign_count=row.get("签到次数", 1),
                            watch_duration=row.get("观看时长", 0),
                            is_signed=True,
                            sign_time=row["签到时间"]
                        )
                        session.add(viewer)
                    session.commit()
                    
                ErrorHandler.handle_info("导入签到信息成功", self, "成功")
                self.load_data()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "导入签到信息失败")
            
    @PerformanceManager.measure_operation("show_detail")
    def show_detail(self, record: LiveViewer):
        """显示详情
        
        Args:
            record: 签到记录
        """
        try:
            # TODO: 实现详情显示
            pass
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "显示详情失败")
            
    @PerformanceManager.measure_operation("delete_record")
    def delete_record(self, record: LiveViewer):
        """删除记录
        
        Args:
            record: 签到记录
        """
        try:
            # 确认删除
            if not ErrorHandler.handle_question(
                "确定要删除该签到记录吗？",
                self,
                "确认删除"
            ):
                return
                
            # 删除记录
            with self.db_manager.get_session() as session:
                session.query(LiveViewer).filter_by(id=record.id).delete()
                session.commit()
                
            ErrorHandler.handle_info("删除签到记录成功", self, "成功")
            self.load_data()
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "删除签到记录失败")
            
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
                
            # 获取所有签到记录
            with self.db_manager.get_session() as session:
                records = session.query(LiveViewer).filter(LiveViewer.is_signed == True).all()
                
            # 创建DataFrame
            data = []
            for record in records:
                live_title = record.living.title if record.living else "未知直播"
                data.append({
                    "直播场次": live_title,
                    "签到时间": record.sign_time.strftime("%Y-%m-%d %H:%M:%S") if record.sign_time else "",
                    "签到成员": record.username,
                    "所在部门": record.department,
                    "签到次数": record.sign_count,
                    "观看时长": record.watch_duration,
                    "奖励金额": record.reward_amount
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