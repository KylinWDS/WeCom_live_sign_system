# PySide6导入
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit, QComboBox, QCheckBox, QTextEdit, QProgressBar
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
    
    def __init__(self, parent=None, title: str = "", is_import: bool = True, is_progress_dialog: bool = False):
        super().__init__(parent, title, 500, 400)
        self.is_import = is_import
        self.is_progress_dialog = is_progress_dialog
        
        # 如果是进度对话框，创建不同的布局
        if is_progress_dialog:
            self._init_progress_dialog()
        else:
            self._init_io_dialog()
            
    def _init_io_dialog(self):
        """初始化导入/导出对话框"""
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
        
        if not self.is_import:
            self.header_check = QCheckBox("包含表头")
            self.header_check.setChecked(True)
            self.options_layout.addWidget(self.header_check)
            
        self.content_layout.addLayout(self.options_layout)
        
    def _init_progress_dialog(self):
        """初始化进度对话框"""
        # 创建日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.content_layout.addWidget(self.log_text)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.content_layout.addWidget(self.progress_bar)
        
        # 设置按钮
        self.set_ok_button_text("完成")
        self.set_ok_button_enabled(False)
        self.set_cancel_button_text("取消")
        
    def _browse_file(self):
        """浏览文件"""
        if self.is_import:
            file_path, selected_filter = QFileDialog.getOpenFileName(
                self,
                "选择文件",
                "",
                "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv);;JSON文件 (*.json)"
            )
        else:
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "保存文件",
                "",
                "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv);;JSON文件 (*.json)"
            )
            
        if file_path:
            self.file_edit.setText(file_path)
            # 自动检测文件格式和编码
            self.detect_file_format_and_encoding(file_path)
            
    def detect_file_format_and_encoding(self, file_path):
        """根据文件路径检测文件格式和编码"""
        # 检测文件格式
        if file_path.lower().endswith(('.xlsx', '.xls')):
            self.format_combo.setCurrentText("Excel")
        elif file_path.lower().endswith('.csv'):
            self.format_combo.setCurrentText("CSV")
        elif file_path.lower().endswith('.json'):
            self.format_combo.setCurrentText("JSON")
            
        # 尝试检测文件编码（这里是简单示例，实际可能需要更复杂的检测）
        try:
            import chardet
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read(1024))
                detected_encoding = result['encoding']
                
                # 设置编码选项
                if detected_encoding and detected_encoding.lower() in ['utf-8', 'utf8']:
                    self.encoding_check.setChecked(True)
                else:
                    self.encoding_check.setChecked(False)
        except:
            # 如果检测失败，保持默认设置
            pass
            
    def set_file_path(self, file_path):
        """设置文件路径并自动检测文件格式和编码"""
        self.file_edit.setText(file_path)
        self.detect_file_format_and_encoding(file_path)
        
    def get_file_path(self) -> str:
        """获取文件路径"""
        return self.file_edit.text()
        
    def get_file_format(self) -> str:
        """获取文件格式"""
        return self.format_combo.currentText()
        
    def get_options(self) -> Dict[str, Any]:
        """获取选项"""
        options = {
            "encoding": "utf-8" if hasattr(self, 'encoding_check') and self.encoding_check.isChecked() else "gbk"
        }
        if not self.is_import and hasattr(self, 'header_check'):
            options["include_header"] = self.header_check.isChecked()
        return options
        
    # 以下是进度对话框特有的方法
    def add_info(self, text: str):
        """添加信息日志"""
        if hasattr(self, 'log_text'):
            self.log_text.append(f"<font color='black'>[信息] {text}</font>")
            self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
            
    def add_success(self, text: str):
        """添加成功日志"""
        if hasattr(self, 'log_text'):
            self.log_text.append(f"<font color='green'>[成功] {text}</font>")
            self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
            
    def add_warning(self, text: str):
        """添加警告日志"""
        if hasattr(self, 'log_text'):
            self.log_text.append(f"<font color='orange'>[警告] {text}</font>")
            self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
            
    def add_error(self, text: str):
        """添加错误日志"""
        if hasattr(self, 'log_text'):
            self.log_text.append(f"<font color='red'>[错误] {text}</font>")
            self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
            
    def set_progress(self, value: int):
        """设置进度条值"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)
            
    def clear_log(self):
        """清除日志"""
        if hasattr(self, 'log_text'):
            self.log_text.clear()
            
    def finish(self):
        """完成操作"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(100)
            self.set_ok_button_enabled(True)
            self.set_cancel_button_enabled(False)