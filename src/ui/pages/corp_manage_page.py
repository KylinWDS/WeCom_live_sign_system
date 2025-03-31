from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDialog, QFormLayout,
                             QHeaderView, QFileDialog, QGroupBox, QCheckBox, QAbstractItemView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from ..managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.core.database import DatabaseManager
from src.models.corporation import Corporation as Corp
from src.core.auth_manager import AuthManager
import pandas as pd
import os
from datetime import datetime

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
            self.corp_name.setText(self.corp_data["name"])
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
        save_btn.clicked.connect(self.validate_and_accept)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow("", btn_layout)
        
    def validate_and_accept(self):
        """验证输入并接受"""
        # 验证必填字段
        if not self.corp_name.text():
            ErrorHandler.handle_warning("企业名称不能为空", self)
            return
        
        if not self.corp_id.text():
            ErrorHandler.handle_warning("企业ID不能为空", self)
            return
            
        if not self.corp_secret.text():
            ErrorHandler.handle_warning("企业应用Secret不能为空", self)
            return
            
        if not self.agent_id.text():
            ErrorHandler.handle_warning("应用ID不能为空", self)
            return
            
        self.accept()
        
    def get_data(self) -> dict:
        """获取表单数据
        
        Returns:
            表单数据
        """
        return {
            "name": self.corp_name.text(),
            "corp_id": self.corp_id.text(),
            "corp_secret": self.corp_secret.text(),
            "agent_id": self.agent_id.text(),
            "status": self.status.isChecked()
        }

class CorpManagePage(QWidget):
    """企业管理页面"""
    
    def __init__(self, db_manager: DatabaseManager, auth_manager=None, user_id=None):
        super().__init__()
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.user_id = user_id
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
            "企业ID", "企业名称", "应用ID", "企业应用Secret",
            "状态", "创建时间", "操作"
        ])
        # 修改表格的滚动模式，支持水平滚动
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 设置最后一列（操作列）的宽度固定
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 180)  # 增加操作列的宽度为180像素
        
        # 增加行高设置
        self.table.verticalHeader().setDefaultSectionSize(50)  # 增加默认行高为50像素
        
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
        """创建搜索区域
        
        Returns:
            搜索区域组控件
        """
        group = QGroupBox("搜索条件")
        layout = QHBoxLayout(group)
        
        # 企业名称
        layout.addWidget(QLabel("企业名称:"))
        self.corp_name = QLineEdit()
        self.corp_name.setPlaceholderText("请输入企业名称")
        WidgetUtils.set_input_style(self.corp_name)
        layout.addWidget(self.corp_name)
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("secondaryButton")
        search_btn.clicked.connect(self.search)
        layout.addWidget(search_btn)
        
        return group
        
    @PerformanceManager.measure_operation("load_data")
    def load_data(self):
        """加载数据"""
        try:
            # 获取企业列表
            with self.db_manager.get_session() as session:
                query = session.query(Corp)
                
                # 应用搜索条件
                if hasattr(self, 'corp_name') and self.corp_name.text():
                    query = query.filter(Corp.name.like(f"%{self.corp_name.text()}%"))
                    
                # 计算总页数
                total = query.count()
                self.total_pages = (total + self.page_size - 1) // self.page_size
                
                # 获取当前页数据
                records = query.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
                
                # 在会话范围内准备表格数据
                table_data = []
                for record in records:
                    # 在会话内获取数据
                    corp_id = record.corp_id
                    name = record.name
                    agent_id = record.agent_id
                    corp_secret = record.corp_secret
                    status = record.status
                    created_at = record.created_at
                    updated_at = record.updated_at
                    
                    # 脱敏处理企业密钥
                    if corp_secret and len(corp_secret) > 8:
                        masked_secret = corp_secret[:4] + '*' * (len(corp_secret) - 8) + corp_secret[-4:]
                    else:
                        masked_secret = '****' if corp_secret else ''
                    
                    # 保存企业数据
                    table_data.append({
                        'id': getattr(record, 'id', None),
                        'corp_id': corp_id,
                        'name': name,
                        'agent_id': agent_id,
                        'corp_secret': corp_secret,  # 保存原始值用于编辑
                        'masked_secret': masked_secret,  # 保存脱敏值用于显示
                        'status': status,
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
            
            # 会话已关闭，使用从会话中提取的数据更新表格
            self.table.setRowCount(len(table_data))
            for row, data in enumerate(table_data):
                self.table.setItem(row, 0, QTableWidgetItem(data['corp_id']))
                self.table.setItem(row, 1, QTableWidgetItem(data['name']))
                self.table.setItem(row, 2, QTableWidgetItem(data['agent_id']))
                self.table.setItem(row, 3, QTableWidgetItem(data['masked_secret']))  # 显示脱敏值
                
                # 状态列
                status_text = "启用" if data['status'] else "禁用"
                self.table.setItem(row, 4, QTableWidgetItem(status_text))
                
                # 创建时间
                created_at = ""
                if data['created_at']:
                    if isinstance(data['created_at'], datetime):
                        created_at = data['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        created_at = str(data['created_at'])
                self.table.setItem(row, 5, QTableWidgetItem(created_at))
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)  # 使用水平布局，与用户管理页面一致
                btn_layout.setContentsMargins(0, 0, 0, 0)  # 减少边距
                
                edit_btn = QPushButton("编辑")
                edit_btn.setObjectName("linkButton")
                # 直接设置样式确保按钮可见，与用户管理页面样式一致
                edit_btn.setStyleSheet("background-color: #f0f0f0; color: #000000; border: 1px solid #cccccc; border-radius: 4px; padding: 4px 12px; min-width: 60px;")
                corp_id = data['corp_id']
                edit_btn.clicked.connect(lambda checked, cid=corp_id: self._edit_corp_by_id(cid))
                btn_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("删除")
                delete_btn.setObjectName("linkButton")
                # 直接设置样式确保按钮可见，与用户管理页面样式一致
                delete_btn.setStyleSheet("background-color: #f0f0f0; color: #000000; border: 1px solid #cccccc; border-radius: 4px; padding: 4px 12px; min-width: 60px;")
                delete_btn.clicked.connect(lambda checked, cid=corp_id: self._delete_corp_by_id(cid))
                btn_layout.addWidget(delete_btn)
                
                self.table.setCellWidget(row, 6, btn_widget)
                
            # 更新分页信息
            self.page_label.setText(f"第 {self.current_page} 页 / 共 {self.total_pages} 页")
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < self.total_pages)
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "加载企业列表失败")
    
    def _edit_corp_by_id(self, corp_id):
        """通过企业ID编辑企业
        
        Args:
            corp_id: 企业ID
        """
        try:
            with self.db_manager.get_session() as session:
                corp = session.query(Corp).filter_by(corp_id=corp_id).first()
                if corp:
                    # 使用企业对象副本，避免依赖于会话外的对象
                    self.edit_corp(corp)
                else:
                    ErrorHandler.handle_warning("企业不存在", self)
        except Exception as e:
            ErrorHandler.handle_error(e, self, "编辑企业失败")
    
    def _delete_corp_by_id(self, corp_id):
        """通过企业ID删除企业
        
        Args:
            corp_id: 企业ID
        """
        try:
            with self.db_manager.get_session() as session:
                corp = session.query(Corp).filter_by(corp_id=corp_id).first()
                if corp:
                    self.delete_corp(corp)
                else:
                    ErrorHandler.handle_warning("企业不存在", self)
        except Exception as e:
            ErrorHandler.handle_error(e, self, "删除企业失败")
        
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
            # 检查权限
            if self.auth_manager and self.user_id:
                with self.db_manager.get_session() as session:
                    if not self.auth_manager.has_permission(self.user_id, "manage_corps", session):
                        self.error_handler.handle_warning("您没有权限执行此操作", self)
                        return
            
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
                    
                    # 验证必填字段
                    if not corp_info["name"] or not corp_info["corp_id"]:
                        ErrorHandler.handle_warning("请填写企业名称和企业ID", self)
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
            # 检查权限
            if self.auth_manager and self.user_id:
                with self.db_manager.get_session() as session:
                    if not self.auth_manager.has_permission(self.user_id, "manage_corps", session):
                        self.error_handler.handle_warning("您没有权限执行此操作", self)
                        return
            
            # 创建企业对话框，使用企业数据的副本而不是SQLAlchemy对象
            corp_data = {
                "name": getattr(corp, 'name', ''),
                "corp_id": getattr(corp, 'corp_id', ''),
                "corp_secret": getattr(corp, 'corp_secret', ''),
                "agent_id": getattr(corp, 'agent_id', ''),
                "status": getattr(corp, 'status', True)
            }
            
            dialog = CorpDialog(corp_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取企业信息
                corp_info = dialog.get_data()
                
                # 更新企业信息
                with self.db_manager.get_session() as session:
                    # 获取数据库中的企业
                    db_corp = session.query(Corp).filter_by(corp_id=corp_data["corp_id"]).first()
                    if not db_corp:
                        ErrorHandler.handle_warning("企业不存在", self)
                        return
                    
                    # 更新所有字段
                    for key, value in corp_info.items():
                        if key != "corp_id":  # 不更新主键
                            setattr(db_corp, key, value)
                    
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
            # 检查权限
            if self.auth_manager and self.user_id:
                with self.db_manager.get_session() as session:
                    if not self.auth_manager.has_permission(self.user_id, "manage_corps", session):
                        self.error_handler.handle_warning("您没有权限执行此操作", self)
                        return
            
            # 确认删除
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除企业 {corp.name} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 获取企业ID
                corp_id = corp.corp_id
                
                with self.db_manager.get_session() as session:
                    # 找到要删除的企业
                    db_corp = session.query(Corp).filter_by(corp_id=corp_id).first()
                    if not db_corp:
                        ErrorHandler.handle_warning("企业不存在", self)
                        return
                    
                    session.delete(db_corp)
                    session.commit()
                    
                ErrorHandler.handle_info("删除企业成功", self, "成功")
                self.load_data()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "删除企业失败")
            
    @PerformanceManager.measure_operation("export_data")
    def export_data(self):
        """导出数据"""
        try:
            # 检查权限
            if self.auth_manager and self.user_id:
                with self.db_manager.get_session() as session:
                    if not self.auth_manager.has_permission(self.user_id, "export_data", session):
                        self.error_handler.handle_warning("您没有权限执行此操作", self)
                        return
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存Excel文件",
                "",
                "Excel Files (*.xlsx)"
            )
            if not file_path:
                return
                
            # 获取所有企业记录，并准备导出数据
            corp_data = []
            with self.db_manager.get_session() as session:
                corps = session.query(Corp).all()
                
                # 在会话内处理数据
                for corp in corps:
                    # 脱敏处理企业密钥
                    corp_secret = corp.corp_secret
                    if corp_secret and len(corp_secret) > 8:
                        masked_secret = corp_secret[:4] + '*' * (len(corp_secret) - 8) + corp_secret[-4:]
                    else:
                        masked_secret = '****' if corp_secret else ''
                    
                    created_at_str = corp.created_at.strftime("%Y-%m-%d %H:%M:%S") if corp.created_at else ''
                    updated_at_str = corp.updated_at.strftime("%Y-%m-%d %H:%M:%S") if corp.updated_at else ''
                    
                    corp_data.append({
                        "企业名称": corp.name,
                        "企业ID": corp.corp_id,
                        "应用ID": corp.agent_id,
                        "企业微信密钥": masked_secret,  # 导出时也脱敏
                        "状态": "启用" if corp.status else "禁用",
                        "创建时间": created_at_str,
                        "更新时间": updated_at_str
                    })
            
            # 创建DataFrame并导出
            df = pd.DataFrame(corp_data)
            df.to_excel(file_path, index=False)
            
            ErrorHandler.handle_info("导出数据成功", self, "成功")
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "导出数据失败")
            
    def refresh_data(self):
        """刷新数据"""
        self.load_data()