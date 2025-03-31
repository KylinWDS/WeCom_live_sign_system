from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QCheckBox,
                             QDateEdit, QTimeEdit, QSpinBox, QDialogButtonBox)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from utils.logger import get_logger
from ..managers.animation import AnimationManager
from utils.performance_manager import PerformanceManager
from utils.error_handler import ErrorHandler
from core.database import DatabaseManager
from models.live_viewer import LiveViewer, UserSource
from ..dialogs.io_dialog import IODialog
from src.models.living import Living
from src.models.live_sign_record import LiveSignRecord
import pandas as pd
import os
from datetime import datetime
import time

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
                    query = query.filter(LiveViewer.living.has(Living.theme.like(f"%{self.live_session.text()}%")))
                    
                if self.sign_date.date().isValid():
                    # 将QDate转换为Python date对象
                    py_date = self.sign_date.date().toPython()
                    query = query.filter(LiveViewer.sign_time >= py_date)
                    
                if self.member.text():
                    query = query.filter(LiveViewer.name.like(f"%{self.member.text()}%"))
                    
                if self.department.text():
                    query = query.filter(LiveViewer.department.like(f"%{self.department.text()}%"))
                    
                # 计算总页数
                total = query.count()
                self.total_pages = (total + self.page_size - 1) // self.page_size
                
                # 获取当前页数据
                records = query.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
                
                # 获取每个用户的签到明细记录数量
                viewer_ids = [record.id for record in records]
                if viewer_ids:
                    # 查询每个用户的签到明细记录数
                    sign_counts = {}
                    detail_counts = session.query(
                        LiveSignRecord.viewer_id, 
                        session.query(LiveSignRecord).filter(
                            LiveSignRecord.viewer_id == LiveSignRecord.viewer_id
                        ).statement.with_only_columns([session.func.count()]).scalar_subquery()
                    ).filter(
                        LiveSignRecord.viewer_id.in_(viewer_ids)
                    ).all()
                    
                    # 构建映射
                    for viewer_id, count in detail_counts:
                        sign_counts[viewer_id] = count
                
            # 更新表格
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                # 获取直播主题
                live_theme = record.living.theme if record.living else "未知直播"
                
                # 获取签到次数（从签到明细表中获取）
                detail_count = sign_counts.get(record.id, 0) if viewer_ids else record.sign_count
                
                # 填充表格
                self.table.setItem(row, 0, QTableWidgetItem(live_theme))
                self.table.setItem(row, 1, QTableWidgetItem(record.sign_time.strftime("%Y-%m-%d %H:%M:%S") if record.sign_time else ""))
                self.table.setItem(row, 2, QTableWidgetItem(record.user_source.value if hasattr(record, 'user_source') else "-"))
                self.table.setItem(row, 3, QTableWidgetItem(record.name))
                self.table.setItem(row, 4, QTableWidgetItem(record.department or ""))
                self.table.setItem(row, 5, QTableWidgetItem(str(detail_count)))
                self.table.setItem(row, 6, QTableWidgetItem(f"{record.watch_time//60}分钟" if record.watch_time else "0分钟"))
                
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
                    # 导入前确认选择哪个直播
                    living_id = self._select_living()
                    if not living_id:
                        return
                        
                    # 获取已有记录，用于检查重复
                    existing_records = session.query(LiveViewer).filter_by(living_id=living_id).all()
                    existing_name_map = {record.name.lower(): record for record in existing_records}
                    
                    success_count = 0
                    update_count = 0
                    
                    for _, row in df.iterrows():
                        member_name = row["签到成员"]
                        # 处理微信用户名称，去除@微信后缀
                        processed_member_name = LiveViewer.process_wechat_name(member_name)
                        
                        # 获取部门和签到时间
                        department = row.get("所在部门", "")
                        sign_time = row.get("签到时间", datetime.now())
                        
                        # 检查是否已存在
                        existing_record = existing_name_map.get(processed_member_name.lower())
                        
                        if existing_record:
                            # 更新已有记录
                            existing_record.is_signed = True
                            existing_record.sign_time = sign_time
                            existing_record.sign_type = "import"
                            existing_record.sign_count += 1
                            
                            # 如果有部门信息，更新部门
                            if department and not existing_record.department:
                                existing_record.department = department
                                
                            # 创建新的签到记录
                            sign_record = LiveSignRecord(
                                viewer_id=existing_record.id,
                                sign_time=sign_time,
                                sign_type="import",
                                sign_remark="从Excel导入"
                            )
                            session.add(sign_record)
                            update_count += 1
                        else:
                            # 生成唯一的userid
                            userid = f"wx_{processed_member_name}_{int(time.time())}_{_}"
                            
                            # 创建新记录
                            viewer = LiveViewer(
                                living_id=living_id,
                                userid=userid,
                                name=processed_member_name,
                                user_source=UserSource.EXTERNAL,
                                user_type=1,
                                department=department,
                                is_signed=True,
                                sign_time=sign_time,
                                sign_type="import",
                                sign_count=1
                            )
                            session.add(viewer)
                            
                            # 等待session.flush以获取新记录的id
                            session.flush()
                            
                            # 创建新的签到记录
                            sign_record = LiveSignRecord(
                                viewer_id=viewer.id,
                                sign_time=sign_time,
                                sign_type="import",
                                sign_remark="从Excel导入"
                            )
                            session.add(sign_record)
                            success_count += 1
                    
                    # 更新直播的签到导入状态
                    live = session.query(Living).filter_by(id=living_id).first()
                    if live:
                        live.is_sign_imported = 1
                        
                    session.commit()
                    
                ErrorHandler.handle_info(f"导入签到信息成功：新增{success_count}条，更新{update_count}条", self, "成功")
                self.load_data()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "导入签到信息失败")
            
    def _select_living(self) -> int:
        """选择直播
        
        Returns:
            int: 直播ID，如果取消则返回None
        """
        try:
            with self.db_manager.get_session() as session:
                # 获取所有直播
                livings = session.query(Living).all()
                
                if not livings:
                    ErrorHandler.handle_warning("没有可用的直播记录", self, "提示")
                    return None
                
                # 创建选择对话框
                dialog = QDialog(self)
                dialog.setWindowTitle("选择直播")
                layout = QVBoxLayout(dialog)
                
                combo = QComboBox()
                for live in livings:
                    combo.addItem(f"{live.theme} ({live.living_start.strftime('%Y-%m-%d')})", live.id)
                
                layout.addWidget(QLabel("请选择要导入签到的直播："))
                layout.addWidget(combo)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    return combo.currentData()
                return None
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "选择直播失败")
            return None
        
    @PerformanceManager.measure_operation("show_detail")
    def show_detail(self, record: LiveViewer):
        """显示详情
        
        Args:
            record: 签到记录
        """
        try:
            # 创建详情对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(f"签到详情 - {record.name}")
            dialog.resize(700, 500)
            
            layout = QVBoxLayout(dialog)
            
            # 用户基本信息
            info_group = QGroupBox("基本信息")
            info_layout = QFormLayout(info_group)
            
            info_layout.addRow("用户ID:", QLabel(record.userid))
            info_layout.addRow("姓名:", QLabel(record.name))
            info_layout.addRow("部门:", QLabel(record.department or "无"))
            info_layout.addRow("用户来源:", QLabel(record.user_source.value if hasattr(record, 'user_source') else "未知"))
            info_layout.addRow("是否签到:", QLabel("已签到" if record.is_signed else "未签到"))
            info_layout.addRow("最后签到时间:", QLabel(record.sign_time.strftime("%Y-%m-%d %H:%M:%S") if record.sign_time else "未签到"))
            info_layout.addRow("总签到次数:", QLabel(str(record.sign_count)))
            info_layout.addRow("观看时长:", QLabel(f"{record.watch_time//60}分钟" if record.watch_time else "0分钟"))
            info_layout.addRow("是否评论:", QLabel("是" if record.is_comment else "否"))
            info_layout.addRow("是否连麦:", QLabel("是" if record.is_mic else "否"))
            
            layout.addWidget(info_group)
            
            # 签到明细记录
            detail_group = QGroupBox("签到记录明细")
            detail_layout = QVBoxLayout(detail_group)
            
            detail_table = QTableWidget()
            detail_table.setColumnCount(7)
            detail_table.setHorizontalHeaderLabels(["签到时间", "签到类型", "签到次数", "Sheet名称", "签到备注", "是否有效", "创建时间"])
            detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            WidgetUtils.set_table_style(detail_table)
            
            # 查询签到明细记录
            with self.db_manager.get_session() as session:
                from src.models.living import Living
                
                # 获取签到明细记录，包括关联的直播信息
                sign_records = (
                    session.query(LiveSignRecord, Living.theme)
                    .join(Living, LiveSignRecord.living_id == Living.livingid)
                    .filter(LiveSignRecord.viewer_id == record.id)
                    .order_by(LiveSignRecord.sign_sequence, LiveSignRecord.sign_time.desc())
                    .all()
                )
                
                detail_table.setRowCount(len(sign_records))
                for row, (sign_record, live_theme) in enumerate(sign_records):
                    detail_table.setItem(row, 0, QTableWidgetItem(sign_record.sign_time.strftime("%Y-%m-%d %H:%M:%S") if sign_record.sign_time else ""))
                    detail_table.setItem(row, 1, QTableWidgetItem(sign_record.sign_type))
                    detail_table.setItem(row, 2, QTableWidgetItem(str(sign_record.sign_sequence)))
                    detail_table.setItem(row, 3, QTableWidgetItem(sign_record.sheet_name or ""))
                    detail_table.setItem(row, 4, QTableWidgetItem(sign_record.sign_remark or ""))
                    detail_table.setItem(row, 5, QTableWidgetItem("是" if sign_record.is_valid else "否"))
                    detail_table.setItem(row, 6, QTableWidgetItem(sign_record.create_time.strftime("%Y-%m-%d %H:%M:%S") if sign_record.create_time else ""))
            
            detail_layout.addWidget(detail_table)
            layout.addWidget(detail_group)
            
            # 关闭按钮
            button_box = QDialogButtonBox(QDialogButtonBox.Close)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.exec()
            
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
                "确定要删除该签到记录吗？\n这将同时删除所有关联的签到明细记录。",
                self,
                "确认删除"
            ):
                return
                
            # 删除记录
            with self.db_manager.get_session() as session:
                # 首先获取关联的签到明细记录数量
                sign_detail_count = session.query(LiveSignRecord).filter_by(viewer_id=record.id).count()
                
                # 删除LiveViewer记录（cascade会自动删除关联的签到明细）
                deleted = session.query(LiveViewer).filter_by(id=record.id).delete()
                session.commit()
                
                if deleted:
                    ErrorHandler.handle_info(
                        f"已删除签到记录及{sign_detail_count}条关联的签到明细", 
                        self, 
                        "成功"
                    )
                else:
                    ErrorHandler.handle_warning("未找到要删除的记录", self, "警告")
            
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
                
            # 选择导出方式
            export_type = QMessageBox.question(
                self,
                "导出方式",
                "是否导出签到明细记录？\n点击'是'导出每次签到的详细记录，点击'否'仅导出签到者基本信息",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            # 导出方式：是否包含签到明细
            include_details = (export_type == QMessageBox.Yes)
            
            with pd.ExcelWriter(file_path) as writer:
                # 获取所有签到记录
                with self.db_manager.get_session() as session:
                    # 基本数据：签到者信息
                    records = session.query(LiveViewer).filter(LiveViewer.is_signed == True).all()
                    
                    # 创建DataFrame
                    data = []
                    for record in records:
                        live_title = record.living.theme if record.living else "未知直播"
                        live_time = record.living.living_start.strftime("%Y-%m-%d %H:%M") if record.living and record.living.living_start else ""
                        
                        data.append({
                            "直播场次": live_title,
                            "直播时间": live_time,
                            "签到成员": record.name,
                            "成员ID": record.userid,
                            "所在部门": record.department,
                            "最后签到时间": record.sign_time.strftime("%Y-%m-%d %H:%M:%S") if record.sign_time else "",
                            "签到次数": record.sign_count,
                            "观看时长(秒)": record.watch_time,
                            "是否评论": "是" if record.is_comment else "否",
                            "是否连麦": "是" if record.is_mic else "否"
                        })
                    
                    # 导出签到者基本信息
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name="签到成员信息", index=False)
                    
                    # 是否需要导出签到明细
                    if include_details:
                        # 获取所有签到明细记录
                        sign_records = (
                            session.query(
                                LiveSignRecord,
                                LiveViewer.name,
                                LiveViewer.department,
                                Living.theme,
                                Living.living_start
                            )
                            .join(LiveViewer, LiveSignRecord.viewer_id == LiveViewer.id)
                            .join(Living, LiveSignRecord.living_id == Living.livingid)
                            .all()
                        )
                        
                        # 创建签到明细DataFrame
                        detail_data = []
                        for record, name, department, theme, living_start in sign_records:
                            detail_data.append({
                                "直播场次": theme if theme else "未知直播",
                                "直播时间": living_start.strftime("%Y-%m-%d %H:%M") if living_start else "",
                                "签到成员": name,
                                "所在部门": department,
                                "签到时间": record.sign_time.strftime("%Y-%m-%d %H:%M:%S") if record.sign_time else "",
                                "签到类型": record.sign_type,
                                "签到次数": record.sign_sequence,
                                "Sheet名称": record.sheet_name,
                                "签到备注": record.sign_remark,
                                "是否有效": "是" if record.is_valid else "否",
                                "创建时间": record.create_time.strftime("%Y-%m-%d %H:%M:%S") if record.create_time else ""
                            })
                        
                        # 导出签到明细
                        detail_df = pd.DataFrame(detail_data)
                        detail_df.to_excel(writer, sheet_name="签到明细记录", index=False)
            
            ErrorHandler.handle_info("导出数据成功", self, "成功")
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "导出数据失败")
            
    def refresh_data(self):
        """刷新数据"""
        self.load_data() 