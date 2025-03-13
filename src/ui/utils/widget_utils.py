from PySide6.QtWidgets import (QWidget, QPushButton, QLabel, QLineEdit, QTextEdit,
                             QComboBox, QCheckBox, QRadioButton, QSpinBox, QDoubleSpinBox,
                             QSlider, QProgressBar, QTableWidget, QTableWidgetItem,
                             QHeaderView, QScrollArea, QFrame, QDateEdit, QTimeEdit)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from src.utils.logger import get_logger

logger = get_logger(__name__)

class WidgetUtils:
    """控件工具类"""
    
    @staticmethod
    def create_button(parent: QWidget = None, text: str = "", icon: QIcon = None,
                     min_width: int = 80, min_height: int = 30) -> QPushButton:
        """创建按钮"""
        try:
            button = QPushButton(text, parent)
            if icon:
                button.setIcon(icon)
            button.setMinimumSize(min_width, min_height)
            return button
        except Exception as e:
            logger.error(f"创建按钮失败: {str(e)}")
            return None
            
    @staticmethod
    def create_label(parent: QWidget = None, text: str = "", font_size: int = 12) -> QLabel:
        """创建标签"""
        try:
            label = QLabel(text, parent)
            font = QFont()
            font.setPointSize(font_size)
            label.setFont(font)
            return label
        except Exception as e:
            logger.error(f"创建标签失败: {str(e)}")
            return None
            
    @staticmethod
    def create_line_edit(parent: QWidget = None, placeholder: str = "",
                        min_width: int = 200, min_height: int = 30) -> QLineEdit:
        """创建单行输入框"""
        try:
            line_edit = QLineEdit(placeholder, parent)
            line_edit.setMinimumSize(min_width, min_height)
            WidgetUtils.set_input_style(line_edit)
            return line_edit
        except Exception as e:
            logger.error(f"创建单行输入框失败: {str(e)}")
            return None
            
    @staticmethod
    def create_text_edit(parent: QWidget = None, placeholder: str = "",
                        min_width: int = 300, min_height: int = 100) -> QTextEdit:
        """创建多行输入框"""
        try:
            text_edit = QTextEdit(placeholder, parent)
            text_edit.setMinimumSize(min_width, min_height)
            return text_edit
        except Exception as e:
            logger.error(f"创建多行输入框失败: {str(e)}")
            return None
            
    @staticmethod
    def create_combo_box(parent: QWidget = None, items: list = None,
                        min_width: int = 200, min_height: int = 30) -> QComboBox:
        """创建下拉框"""
        try:
            combo_box = QComboBox(parent)
            if items:
                combo_box.addItems(items)
            combo_box.setMinimumSize(min_width, min_height)
            WidgetUtils.set_combo_style(combo_box)
            return combo_box
        except Exception as e:
            logger.error(f"创建下拉框失败: {str(e)}")
            return None
            
    @staticmethod
    def create_check_box(parent: QWidget = None, text: str = "") -> QCheckBox:
        """创建复选框"""
        try:
            check_box = QCheckBox(text, parent)
            return check_box
        except Exception as e:
            logger.error(f"创建复选框失败: {str(e)}")
            return None
            
    @staticmethod
    def create_radio_button(parent: QWidget = None, text: str = "") -> QRadioButton:
        """创建单选框"""
        try:
            radio_button = QRadioButton(text, parent)
            return radio_button
        except Exception as e:
            logger.error(f"创建单选框失败: {str(e)}")
            return None
            
    @staticmethod
    def create_spin_box(parent: QWidget = None, min_value: int = 0,
                       max_value: int = 100, default_value: int = 0) -> QSpinBox:
        """创建整数输入框"""
        try:
            spin_box = QSpinBox(parent)
            spin_box.setRange(min_value, max_value)
            spin_box.setValue(default_value)
            WidgetUtils.set_spin_style(spin_box)
            return spin_box
        except Exception as e:
            logger.error(f"创建整数输入框失败: {str(e)}")
            return None
            
    @staticmethod
    def create_double_spin_box(parent: QWidget = None, min_value: float = 0.0,
                             max_value: float = 100.0, default_value: float = 0.0,
                             decimals: int = 2) -> QDoubleSpinBox:
        """创建浮点数输入框"""
        try:
            double_spin_box = QDoubleSpinBox(parent)
            double_spin_box.setRange(min_value, max_value)
            double_spin_box.setValue(default_value)
            double_spin_box.setDecimals(decimals)
            return double_spin_box
        except Exception as e:
            logger.error(f"创建浮点数输入框失败: {str(e)}")
            return None
            
    @staticmethod
    def create_slider(parent: QWidget = None, orientation: Qt.Orientation = Qt.Horizontal,
                     min_value: int = 0, max_value: int = 100,
                     default_value: int = 0) -> QSlider:
        """创建滑块"""
        try:
            slider = QSlider(orientation, parent)
            slider.setRange(min_value, max_value)
            slider.setValue(default_value)
            return slider
        except Exception as e:
            logger.error(f"创建滑块失败: {str(e)}")
            return None
            
    @staticmethod
    def create_progress_bar(parent: QWidget = None, min_width: int = 200,
                          min_height: int = 20) -> QProgressBar:
        """创建进度条"""
        try:
            progress_bar = QProgressBar(parent)
            progress_bar.setMinimumSize(min_width, min_height)
            return progress_bar
        except Exception as e:
            logger.error(f"创建进度条失败: {str(e)}")
            return None
            
    @staticmethod
    def create_table(parent: QWidget = None, row_count: int = 0,
                    column_count: int = 0, headers: list = None) -> QTableWidget:
        """创建表格"""
        try:
            table = QTableWidget(row_count, column_count, parent)
            if headers:
                table.setHorizontalHeaderLabels(headers)
            WidgetUtils.set_table_style(table)
            return table
        except Exception as e:
            logger.error(f"创建表格失败: {str(e)}")
            return None
            
    @staticmethod
    def create_scroll_area(parent: QWidget = None) -> QScrollArea:
        """创建滚动区域"""
        try:
            scroll_area = QScrollArea(parent)
            return scroll_area
        except Exception as e:
            logger.error(f"创建滚动区域失败: {str(e)}")
            return None
            
    @staticmethod
    def create_frame(parent: QWidget = None, frame_shape: QFrame.Shape = QFrame.StyledPanel,
                    frame_shadow: QFrame.Shadow = QFrame.Raised) -> QFrame:
        """创建框架"""
        try:
            frame = QFrame(parent)
            frame.setFrameShape(frame_shape)
            frame.setFrameShadow(frame_shadow)
            return frame
        except Exception as e:
            logger.error(f"创建框架失败: {str(e)}")
            return None
    
    @staticmethod
    def set_input_style(widget: QLineEdit):
        """设置输入框样式"""
        widget.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #40a9ff;
            }
        """)
    
    @staticmethod
    def set_combo_style(widget: QComboBox):
        """设置下拉框样式"""
        widget.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #40a9ff;
            }
        """)
    
    @staticmethod
    def set_table_style(widget: QTableWidget):
        """设置表格样式"""
        widget.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                background-color: white;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e6f7ff;
            }
            QHeaderView::section {
                background-color: #fafafa;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #f0f0f0;
                font-weight: bold;
            }
        """)
    
    @staticmethod
    def set_date_style(widget: QDateEdit):
        """设置日期选择器样式"""
        widget.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QDateEdit:focus {
                border-color: #40a9ff;
            }
        """)
    
    @staticmethod
    def set_time_style(widget: QTimeEdit):
        """设置时间选择器样式"""
        widget.setStyleSheet("""
            QTimeEdit {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QTimeEdit:focus {
                border-color: #40a9ff;
            }
        """)
    
    @staticmethod
    def set_spin_style(widget: QSpinBox):
        """设置数字输入框样式"""
        widget.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QSpinBox:focus {
                border-color: #40a9ff;
            }
        """) 