from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from utils.logger import get_logger
from ..managers.animation import AnimationManager
from utils.performance_manager import PerformanceManager
from utils.error_handler import ErrorHandler
from core.database import DatabaseManager
from models.corp import Corp
import pandas as pd
import os

logger = get_logger(__name__)

class CorpDialog(QDialog):
    """企业编辑对话框"""
    
    def __init__(self, corp_data: dict = None, parent=None):
        super().__init__(parent)
        self.corp_data = corp_data
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑企业" if self.corp_data else "添加企业")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        layout.setSpacing(10)
        
        # 企业名称
        self.corp_name = QLineEdit()
        if self.corp_data:
            self.corp_name.setText(self.corp_data["corp_name"])
        WidgetUtils.set_input_style(self.corp_name)
        layout.addRow("企业名称:", self.corp_name)
        
        # 企业ID
        self.corp_id = QLineEdit()
        if self.corp_data:
            self.corp_id.setText(self.corp_data["corp_id"])
            self.corp_id.setEnabled(False)  # 企业ID不可修改
        WidgetUtils.set_input_style(self.corp_id)
        layout.addRow("企业ID:", self.corp_id)
        
        # 企业应用Secret
        self.corp_secret = QLineEdit()
        if self.corp_data:
            self.corp_secret.setText(self.corp_data["corp_secret"])
        self.corp_secret.setEchoMode(QLineEdit.EchoMode.Password)
        WidgetUtils.set_input_style(self.corp_secret)
        layout.addRow("企业应用Secret:", self.corp_secret)
        
        # 应用ID
        self.agent_id = QLineEdit()
        if self.corp_data:
            self.agent_id.setText(self.corp_data["agent_id"])
        WidgetUtils.set_input_style(self.agent_id)
        layout.addRow("应用ID:", self.agent_id)
        
        # 状态
        self.status = QCheckBox("启用")
        if self.corp_data:
            self.status.setChecked(self.corp_data["status"])
        else:
            self.status.setChecked(True)
        layout.addRow("状态:", self.status)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow("", btn_layout)
        
    def get_data(self) -> dict:
        """获取表单数据
        
        Returns:
            表单数据
        """
        return {
            "corp_name": self.corp_name.text(),
            "corp_id": self.corp_id.text(),
            "corp_secret": self.corp_secret.text(),
            "agent_id": self.agent_id.text(),
            "status": self.status.isChecked()
        }

class CorpManagePage(QWidget):
    """企业管理页面"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("corpManagePage")
        
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
            "企业ID", "企业名称", "企业微信ID", "企业微信密钥",
            "企业微信Token", "企业微信EncodingAESKey", "操作"
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
        self.setStyleSheet(StyleManager.get_main_style())
        
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
        
        # 添加企业按钮
        add_btn = QPushButton("添加企业")
        add_btn.setObjectName("primaryButton")
        add_btn.setIcon(QIcon(":/icons/add.png"))
        add_btn.clicked.connect(self.add_corp)
        layout.addWidget(add_btn)
        
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
        
        # 企业名称
        row1_layout.addWidget(QLabel("企业名称:"))
        self.corp_name = QLineEdit()
        WidgetUtils.set_input_style(self.corp_name)
        row1_layout.addWidget(self.corp_name)
        
        # 企业微信ID
        row1_layout.addWidget(QLabel("企业微信ID:"))
        self.corp_id = QLineEdit()
        WidgetUtils.set_input_style(self.corp_id)
        row1_layout.addWidget(self.corp_id)
        
        layout.addLayout(row1_layout)
        
        # 第二行
        row2_layout = QHBoxLayout()
        
        # 企业微信密钥
        row2_layout.addWidget(QLabel("企业微信密钥:"))
        self.corp_secret = QLineEdit()
        WidgetUtils.set_input_style(self.corp_secret)
        row2_layout.addWidget(self.corp_secret)
        
        # 企业微信Token
        row2_layout.addWidget(QLabel("企业微信Token:"))
        self.corp_token = QLineEdit()
        WidgetUtils.set_input_style(self.corp_token)
        row2_layout.addWidget(self.corp_token)
        
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
            # 获取企业列表
            with self.db_manager.get_session() as session:
                query = session.query(Corp)
                
                # 应用搜索条件
                if self.corp_name.text():
                    query = query.filter(Corp.corp_name.like(f"%{self.corp_name.text()}%"))
                    
                if self.corp_id.text():
                    query = query.filter_by(corp_id=self.corp_id.text())
                    
                if self.corp_secret.text():
                    query = query.filter_by(corp_secret=self.corp_secret.text())
                    
                if self.corp_token.text():
                    query = query.filter_by(corp_token=self.corp_token.text())
                    
                # 计算总页数
                total = query.count()
                self.total_pages = (total + self.page_size - 1) // self.page_size
                
                # 获取当前页数据
                records = query.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
                
            # 更新表格
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(record.corp_id))
                self.table.setItem(row, 1, QTableWidgetItem(record.corp_name))
                self.table.setItem(row, 2, QTableWidgetItem(record.agent_id))
                self.table.setItem(row, 3, QTableWidgetItem(record.corp_secret))
                self.table.setItem(row, 4, QTableWidgetItem(record.corp_token))
                self.table.setItem(row, 5, QTableWidgetItem(record.corp_encoding_aes_key))
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                
                edit_btn = QPushButton("编辑")
                edit_btn.setObjectName("linkButton")
                edit_btn.clicked.connect(lambda checked, r=record: self.edit_corp(r))
                btn_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("删除")
                delete_btn.setObjectName("linkButton")
                delete_btn.clicked.connect(lambda checked, r=record: self.delete_corp(r))
                btn_layout.addWidget(delete_btn)
                
                self.table.setCellWidget(row, 6, btn_widget)
                
            # 更新分页信息
            self.page_label.setText(f"第 {self.current_page} 页 / 共 {self.total_pages} 页")
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < self.total_pages)
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "加载企业列表失败")
            
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
            
    @PerformanceManager.measure_operation("add_corp")
    def add_corp(self):
        """添加企业"""
        try:
            # 创建企业对话框
            dialog = CorpDialog()
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取企业信息
                corp_info = dialog.get_data()
                
                # 验证企业ID是否已存在
                with self.db_manager.get_session() as session:
                    if session.query(Corp).filter_by(corp_id=corp_info["corp_id"]).first():
                        ErrorHandler.handle_warning("企业ID已存在", self)
                        return
                        
                    # 创建企业
                    corp = Corp(**corp_info)
                    session.add(corp)
                    session.commit()
                    
                ErrorHandler.handle_info("添加企业成功", self, "成功")
                self.load_data()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "添加企业失败")
            
    @PerformanceManager.measure_operation("edit_corp")
    def edit_corp(self, corp: Corp):
        """编辑企业
        
        Args:
            corp: 企业信息
        """
        try:
            # 创建企业对话框
            dialog = CorpDialog({
                "corp_name": corp.corp_name,
                "corp_id": corp.corp_id,
                "corp_secret": corp.corp_secret,
                "agent_id": corp.agent_id,
                "corp_token": corp.corp_token,
                "corp_encoding_aes_key": corp.corp_encoding_aes_key
            })
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取企业信息
                corp_info = dialog.get_data()
                
                # 更新企业信息
                with self.db_manager.get_session() as session:
                    session.query(Corp).filter_by(corp_id=corp.corp_id).update(corp_info)
                    session.commit()
                    
                ErrorHandler.handle_info("编辑企业成功", self, "成功")
                self.load_data()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "编辑企业失败")
            
    @PerformanceManager.measure_operation("delete_corp")
    def delete_corp(self, corp: Corp):
        """删除企业
        
        Args:
            corp: 企业信息
        """
        try:
            # 确认删除
            if not ErrorHandler.handle_question(
                "确定要删除该企业吗？",
                self,
                "确认删除"
            ):
                return
                
            # 删除企业
            with self.db_manager.get_session() as session:
                session.query(Corp).filter_by(corp_id=corp.corp_id).delete()
                session.commit()
                
            ErrorHandler.handle_info("删除企业成功", self, "成功")
            self.load_data()
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "删除企业失败")
            
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
                
            # 获取所有企业记录
            with self.db_manager.get_session() as session:
                records = session.query(Corp).all()
                
            # 创建DataFrame
            data = []
            for record in records:
                data.append({
                    "企业名称": record.corp_name,
                    "企业ID": record.corp_id,
                    "应用ID": record.agent_id,
                    "企业微信密钥": record.corp_secret,
                    "企业微信Token": record.corp_token,
                    "企业微信EncodingAESKey": record.corp_encoding_aes_key
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