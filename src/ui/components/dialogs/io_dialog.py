# PySide6导入
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit, QComboBox, QCheckBox
from PySide6.QtCore import Qt
from typing import Dict, Any, List

# UI相关导入
from src.ui.managers.style import StyleManager
from src.ui.utils.widget_utils import WidgetUtils
from src.ui.components.dialogs.base_dialog import BaseDialog

# 核心功能导入
from src.core.database import DatabaseManager

# 工具类导入
from src.utils.logger import get_logger

logger = get_logger(__name__)

class IODialog(BaseDialog):
    """导入/导出对话框基类"""
    
    def __init__(self, parent=None, title: str = "", is_import: bool = True):
        super().__init__(parent, title, 500, 400)
        self.is_import = is_import
        
        # 创建文件选择区域
        self.file_layout = QHBoxLayout()
        self.file_label = QLabel("文件路径:")
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.file_button = self.add_button("浏览", self._browse_file)
        self.file_layout.addWidget(self.file_label)
        self.file_layout.addWidget(self.file_edit)
        self.file_layout.addWidget(self.file_button)
        self.content_layout.addLayout(self.file_layout)
        
        # 创建格式选择
        self.format_layout = QHBoxLayout()
        self.format_label = QLabel("文件格式:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "Excel", "JSON"])
        self.format_layout.addWidget(self.format_label)
        self.format_layout.addWidget(self.format_combo)
        self.content_layout.addLayout(self.format_layout)
        
        # 创建选项区域
        self.options_layout = QVBoxLayout()
        self.encoding_check = QCheckBox("使用UTF-8编码")
        self.encoding_check.setChecked(True)
        self.options_layout.addWidget(self.encoding_check)
        
        if not is_import:
            self.header_check = QCheckBox("包含表头")
            self.header_check.setChecked(True)
            self.options_layout.addWidget(self.header_check)
            
        self.content_layout.addLayout(self.options_layout)
        
    def _browse_file(self):
        """浏览文件"""
        if self.is_import:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择文件",
                "",
                "CSV文件 (*.csv);;Excel文件 (*.xlsx);;JSON文件 (*.json)"
            )
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存文件",
                "",
                "CSV文件 (*.csv);;Excel文件 (*.xlsx);;JSON文件 (*.json)"
            )
            
        if file_path:
            self.file_edit.setText(file_path)
            
    def get_file_path(self) -> str:
        """获取文件路径"""
        return self.file_edit.text()
        
    def get_file_format(self) -> str:
        """获取文件格式"""
        return self.format_combo.currentText()
        
    def get_options(self) -> Dict[str, Any]:
        """获取选项"""
        options = {
            "encoding": "utf-8" if self.encoding_check.isChecked() else "gbk"
        }
        if not self.is_import:
            options["include_header"] = self.header_check.isChecked()
        return options