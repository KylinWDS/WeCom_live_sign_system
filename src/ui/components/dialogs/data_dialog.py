# PySide6导入
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox

# UI相关导入
from .base_dialog import BaseDialog
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils

# 核心功能导入
from core.database import DatabaseManager

# 工具类导入
from utils.logger import get_logger

logger = get_logger(__name__)

class DataDialog(BaseDialog):
    """数据表格对话框基类"""
    
    def __init__(self, parent=None, title: str = "", columns: List[str] = None):
        super().__init__(parent, title, 800, 600)
        self.columns = columns or []
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.content_layout.addWidget(self.table)
        
    def set_data(self, data: List[Dict[str, Any]]):
        """设置数据
        
        Args:
            data: 数据列表
        """
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            for col, key in enumerate(self.columns):
                value = item.get(key, "")
                if isinstance(value, (int, float)):
                    value = str(value)
                self.table.setItem(row, col, QTableWidgetItem(value))
                
    def get_data(self) -> List[Dict[str, Any]]:
        """获取数据
        
        Returns:
            List[Dict[str, Any]]: 数据列表
        """
        data = []
        for row in range(self.table.rowCount()):
            item = {}
            for col, key in enumerate(self.columns):
                item[key] = self.table.item(row, col).text()
            data.append(item)
        return data
        
    def get_selected_data(self) -> List[Dict[str, Any]]:
        """获取选中的数据
        
        Returns:
            List[Dict[str, Any]]: 选中的数据列表
        """
        data = []
        for row in self.table.selectedItems():
            row_data = {}
            for col, key in enumerate(self.columns):
                row_data[key] = self.table.item(row.row(), col).text()
            data.append(row_data)
        return data
        
    def clear_data(self):
        """清空数据"""
        self.table.setRowCount(0)
        
    def set_column_width(self, column: int, width: int):
        """设置列宽
        
        Args:
            column: 列索引
            width: 宽度
        """
        self.table.setColumnWidth(column, width)
        
    def set_column_visible(self, column: int, visible: bool):
        """设置列是否可见
        
        Args:
            column: 列索引
            visible: 是否可见
        """
        self.table.setColumnHidden(column, not visible)
        
    def set_row_visible(self, row: int, visible: bool):
        """设置行是否可见
        
        Args:
            row: 行索引
            visible: 是否可见
        """
        self.table.setRowHidden(row, not visible)
        
    def set_cell_editable(self, row: int, column: int, editable: bool):
        """设置单元格是否可编辑
        
        Args:
            row: 行索引
            column: 列索引
            editable: 是否可编辑
        """
        item = self.table.item(row, column)
        if item:
            item.setFlags(item.flags() | Qt.ItemIsEditable if editable else item.flags() & ~Qt.ItemIsEditable) 