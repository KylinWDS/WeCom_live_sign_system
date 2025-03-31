from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QCalendarWidget)
from PySide6.QtCore import Qt, QDateTime, QTime, Signal
from PySide6.QtGui import QIcon

class CustomDateTimeWidget(QWidget):
    """自定义日期时间选择器组件"""
    
    dateTimeChanged = Signal(QDateTime)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_datetime = QDateTime.currentDateTime()
        self._popup = None
        self._focus_type = None  # 'year', 'month', 'day', 'hour', 'minute', 'second'
        self._custom_style = ""
        self._background_color = "white"  # 默认背景色
        self.init_ui()
        
    def init_ui(self):
        # 设置默认样式
        self._default_style = """
            CustomDateTimeWidget {
                background-color: %(bg_color)s;
                border: 1px solid #DCDFE6;
                border-radius: 4px;
                min-width: 200px;
            }
            CustomDateTimeWidget:hover {
                border-color: #409EFF;
            }
            /* 内部所有容器去除边框和背景 */
            QWidget#dateContainer, QWidget#timeContainer, QWidget#controlWidget {
                background-color: %(bg_color)s;
                border: none;
            }
            /* 所有标签的基础样式 */
            QLabel {
                color: #606266;
                font-size: 13px;
                padding: 0;
                margin: 0;
                border: none;
                background-color: %(bg_color)s;
            }
        """
        self.updateStyle()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)  # 设置更小的边距以显示边框
        layout.setSpacing(0)
        
        # 创建显示容器
        self.display_widget = QWidget()
        display_layout = QHBoxLayout(self.display_widget)
        display_layout.setContentsMargins(6, 0, 6, 0)  # 减小左右内边距
        display_layout.setSpacing(0)
        
        # 日期部分容器
        date_container = QWidget()
        date_container.setObjectName("dateContainer")
        date_layout = QHBoxLayout(date_container)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(0)
        date_layout.setAlignment(Qt.AlignCenter)
        
        # 年月日显示
        self.year_label = QLabel()
        self.year_label.setCursor(Qt.IBeamCursor)
        self.year_label.mousePressEvent = lambda e: self._set_focus('year')
        self.year_label.setAlignment(Qt.AlignCenter)
        
        self.year_separator = QLabel("-")
        self.year_separator.setFixedWidth(8)
        self.year_separator.setAlignment(Qt.AlignCenter)
        
        self.month_label = QLabel()
        self.month_label.setCursor(Qt.IBeamCursor)
        self.month_label.mousePressEvent = lambda e: self._set_focus('month')
        self.month_label.setAlignment(Qt.AlignCenter)
        
        self.month_separator = QLabel("-")
        self.month_separator.setFixedWidth(8)
        self.month_separator.setAlignment(Qt.AlignCenter)
        
        self.day_label = QLabel()
        self.day_label.setCursor(Qt.IBeamCursor)
        self.day_label.mousePressEvent = lambda e: self._set_focus('day')
        self.day_label.setAlignment(Qt.AlignCenter)
        
        # 日期下拉按钮
        self.date_dropdown = QLabel("▼")
        self.date_dropdown.setCursor(Qt.PointingHandCursor)
        self.date_dropdown.mousePressEvent = self._show_calendar
        self.date_dropdown.setAlignment(Qt.AlignCenter)
        self.date_dropdown.setStyleSheet("""
            QLabel {
                color: #C0C4CC;
                font-size: 10px;
                padding: 0 3px;
            }
            QLabel:hover {
                color: #409EFF;
            }
        """)
        
        date_layout.addWidget(self.year_label)
        date_layout.addWidget(self.year_separator)
        date_layout.addWidget(self.month_label)
        date_layout.addWidget(self.month_separator)
        date_layout.addWidget(self.day_label)
        date_layout.addWidget(self.date_dropdown)
        
        # 时间部分容器
        time_container = QWidget()
        time_container.setObjectName("timeContainer")
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(0)
        time_layout.setAlignment(Qt.AlignCenter)
        
        # 时分秒显示
        self.hour_label = QLabel()
        self.hour_label.setCursor(Qt.IBeamCursor)
        self.hour_label.mousePressEvent = lambda e: self._set_focus('hour')
        self.hour_label.setAlignment(Qt.AlignCenter)
        
        self.hour_separator = QLabel(":")
        self.hour_separator.setFixedWidth(8)
        self.hour_separator.setAlignment(Qt.AlignCenter)
        
        self.minute_label = QLabel()
        self.minute_label.setCursor(Qt.IBeamCursor)
        self.minute_label.mousePressEvent = lambda e: self._set_focus('minute')
        self.minute_label.setAlignment(Qt.AlignCenter)
        
        self.minute_separator = QLabel(":")
        self.minute_separator.setFixedWidth(8)
        self.minute_separator.setAlignment(Qt.AlignCenter)
        
        self.second_label = QLabel()
        self.second_label.setCursor(Qt.IBeamCursor)
        self.second_label.mousePressEvent = lambda e: self._set_focus('second')
        self.second_label.setAlignment(Qt.AlignCenter)
        
        # 时间下拉按钮
        self.time_dropdown = QLabel("▼")
        self.time_dropdown.setCursor(Qt.PointingHandCursor)
        self.time_dropdown.mousePressEvent = self._show_time_picker
        self.time_dropdown.setAlignment(Qt.AlignCenter)
        self.time_dropdown.setStyleSheet("""
            QLabel {
                color: #C0C4CC;
                font-size: 10px;
                padding: 0 3px;
            }
            QLabel:hover {
                color: #409EFF;
            }
        """)
        
        time_layout.addWidget(self.hour_label)
        time_layout.addWidget(self.hour_separator)
        time_layout.addWidget(self.minute_label)
        time_layout.addWidget(self.minute_separator)
        time_layout.addWidget(self.second_label)
        time_layout.addWidget(self.time_dropdown)
        
        # 上下箭头按钮容器
        control_widget = QWidget()
        control_widget.setObjectName("controlWidget")
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(0)
        control_layout.setAlignment(Qt.AlignCenter)
        
        # 上下箭头按钮
        arrow_style = """
            QLabel {
                color: #C0C4CC;
                font-size: 10px;
                padding: 0 3px;
                min-height: 14px;
                max-height: 14px;
            }
            QLabel:hover {
                color: #409EFF;
            }
        """
        
        self.up_btn = QLabel("▲")
        self.up_btn.setCursor(Qt.PointingHandCursor)
        self.up_btn.mousePressEvent = self._increment_time
        self.up_btn.setAlignment(Qt.AlignCenter)
        self.up_btn.setStyleSheet(arrow_style)
        
        self.down_btn = QLabel("▼")
        self.down_btn.setCursor(Qt.PointingHandCursor) 
        self.down_btn.mousePressEvent = self._decrement_time
        self.down_btn.setAlignment(Qt.AlignCenter)
        self.down_btn.setStyleSheet(arrow_style)
        
        control_layout.addWidget(self.up_btn)
        control_layout.addWidget(self.down_btn)
        
        # 分隔符
        separator = QLabel(" ")
        separator.setFixedWidth(5)
        
        # 添加所有组件
        display_layout.addWidget(date_container)
        display_layout.addWidget(separator)
        display_layout.addWidget(time_container)
        display_layout.addWidget(control_widget)
        display_layout.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.display_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # 更新显示
        self._update_display()
        
    def _set_focus(self, focus_type):
        """设置焦点类型"""
        self._focus_type = focus_type
        self._update_focus_style()
        
    def _update_focus_style(self):
        """更新焦点样式"""
        year = self._current_datetime.toString("yyyy")
        month = self._current_datetime.toString("MM")
        day = self._current_datetime.toString("dd")
        hour = self._current_datetime.toString("HH")
        minute = self._current_datetime.toString("mm")
        second = self._current_datetime.toString("ss")
        
        # 设置年月日
        self.year_label.setText(year if self._focus_type != 'year' else f'<span style="color: #409EFF; font-weight: bold; background-color: {self._background_color}">{year}</span>')
        self.month_label.setText(month if self._focus_type != 'month' else f'<span style="color: #409EFF; font-weight: bold; background-color: {self._background_color}">{month}</span>')
        self.day_label.setText(day if self._focus_type != 'day' else f'<span style="color: #409EFF; font-weight: bold; background-color: {self._background_color}">{day}</span>')
        
        # 设置时分秒
        self.hour_label.setText(hour if self._focus_type != 'hour' else f'<span style="color: #409EFF; font-weight: bold; background-color: {self._background_color}">{hour}</span>')
        self.minute_label.setText(minute if self._focus_type != 'minute' else f'<span style="color: #409EFF; font-weight: bold; background-color: {self._background_color}">{minute}</span>')
        self.second_label.setText(second if self._focus_type != 'second' else f'<span style="color: #409EFF; font-weight: bold; background-color: {self._background_color}">{second}</span>')
        
        # 设置分隔符样式
        separator_style = f"color: #909399; background-color: {self._background_color};"
        self.year_separator.setStyleSheet(separator_style)
        self.month_separator.setStyleSheet(separator_style)
        self.hour_separator.setStyleSheet(separator_style)
        self.minute_separator.setStyleSheet(separator_style)
        
    def _create_calendar(self):
        """创建日历选择器"""
        calendar = QCalendarWidget(self)
        calendar.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        calendar.setGridVisible(True)
        calendar.clicked.connect(self._on_date_changed)
        
        # 优化日历样式
        calendar.setStyleSheet("""
            QCalendarWidget {
                background: white;
                border: 1px solid #DCDFE6;
                border-radius: 4px;
                min-width: 280px;
                min-height: 280px;
            }
            /* 导航栏样式 */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: white;
                border-bottom: 1px solid #EBEEF5;
                padding: 4px;
            }
            /* 工具按钮样式 */
            QCalendarWidget QToolButton {
                color: #606266;
                background: transparent;
                margin: 2px;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #ecf5ff;
                color: #409EFF;
            }
            QCalendarWidget QToolButton:pressed {
                background-color: #409EFF;
                color: white;
            }
            /* 下拉菜单样式 */
            QCalendarWidget QMenu {
                background: white;
                border: 1px solid #DCDFE6;
                border-radius: 4px;
                padding: 5px;
            }
            /* 日期表格样式 */
            QCalendarWidget QTableView {
                outline: none;
                selection-color: #409EFF;
            }
            QCalendarWidget QTableView::item:hover {
                background-color: #ecf5ff;
                color: #409EFF;
            }
            QCalendarWidget QTableView::item:selected {
                background-color: #409EFF;
                color: white;
            }
            /* 日期单元格样式 */
            QCalendarWidget QAbstractItemView:enabled {
                color: #606266;
                background: white;
                selection-background-color: #409EFF;
                selection-color: white;
                outline: none;
            }
            QCalendarWidget QAbstractItemView:!enabled {
                color: #C0C4CC;
            }
            QCalendarWidget QAbstractItemView:enabled:hover {
                background-color: #ecf5ff;
                color: #409EFF;
            }
        """)
        return calendar
        
    def _create_time_picker(self):
        """创建时间选择器"""
        widget = QWidget(self)
        widget.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        
        combo_style = """
            QComboBox {
                border: 1px solid #DCDFE6;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 70px;
                background: white;
                color: #606266;
                font-size: 14px;
            }
            QComboBox:hover {
                border-color: #409EFF;
            }
            QComboBox:focus {
                border-color: #409EFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(resources/icons/down-arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #DCDFE6;
                border-radius: 4px;
                background: white;
                selection-background-color: #ecf5ff;
                selection-color: #409EFF;
            }
            QComboBox QAbstractItemView::item {
                min-height: 30px;
                padding: 0 10px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #F5F7FA;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #ecf5ff;
                color: #409EFF;
            }
        """
        
        # 小时选择
        self.hour_combo = QComboBox()
        self.hour_combo.addItems([f"{i:02d}" for i in range(24)])
        self.hour_combo.currentIndexChanged.connect(self._on_time_changed)
        self.hour_combo.setStyleSheet(combo_style)
        
        # 分钟选择
        self.minute_combo = QComboBox()
        self.minute_combo.addItems([f"{i:02d}" for i in range(60)])
        self.minute_combo.currentIndexChanged.connect(self._on_time_changed)
        self.minute_combo.setStyleSheet(combo_style)
        
        # 秒选择
        self.second_combo = QComboBox()
        self.second_combo.addItems([f"{i:02d}" for i in range(60)])
        self.second_combo.currentIndexChanged.connect(self._on_time_changed)
        self.second_combo.setStyleSheet(combo_style)
        
        # 添加分隔符
        separator_style = "QLabel { color: #909399; font-size: 14px; padding: 0 2px; }"
        separator1 = QLabel(":")
        separator1.setStyleSheet(separator_style)
        separator2 = QLabel(":")
        separator2.setStyleSheet(separator_style)
        
        layout.addWidget(self.hour_combo)
        layout.addWidget(separator1)
        layout.addWidget(self.minute_combo)
        layout.addWidget(separator2)
        layout.addWidget(self.second_combo)
        
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #DCDFE6;
                border-radius: 4px;
            }
        """)
        
        return widget
        
    def _show_calendar(self, event):
        """显示日历"""
        if self._popup and self._popup.isVisible():
            self._popup.hide()
            return
            
        calendar = self._create_calendar()
        calendar.setSelectedDate(self._current_datetime.date())
        
        # 计算弹出位置
        pos = self.mapToGlobal(self.display_widget.pos())
        pos.setY(pos.y() + self.display_widget.height())
        calendar.move(pos)
        
        self._popup = calendar
        calendar.show()
        
    def _show_time_picker(self, event):
        """显示时间选择器"""
        if self._popup and self._popup.isVisible():
            self._popup.hide()
            return
            
        time_picker = self._create_time_picker()
        
        # 设置当前时间
        self.hour_combo.setCurrentText(f"{self._current_datetime.time().hour():02d}")
        self.minute_combo.setCurrentText(f"{self._current_datetime.time().minute():02d}")
        self.second_combo.setCurrentText(f"{self._current_datetime.time().second():02d}")
        
        # 计算弹出位置
        pos = self.mapToGlobal(self.display_widget.pos())
        pos.setX(pos.x() + self.display_widget.width() - time_picker.width())
        pos.setY(pos.y() + self.display_widget.height())
        time_picker.move(pos)
        
        self._popup = time_picker
        time_picker.show()
        
    def _increment_time(self, event):
        """增加时间"""
        if not self._focus_type:
            return
            
        if self._focus_type == 'year':
            self._current_datetime = self._current_datetime.addYears(1)
        elif self._focus_type == 'month':
            self._current_datetime = self._current_datetime.addMonths(1)
        elif self._focus_type == 'day':
            self._current_datetime = self._current_datetime.addDays(1)
        elif self._focus_type == 'hour':
            self._current_datetime = self._current_datetime.addSecs(3600)
        elif self._focus_type == 'minute':
            self._current_datetime = self._current_datetime.addSecs(60)
        elif self._focus_type == 'second':
            self._current_datetime = self._current_datetime.addSecs(1)
        self._update_display()
        self.dateTimeChanged.emit(self._current_datetime)
        
    def _decrement_time(self, event):
        """减少时间"""
        if not self._focus_type:
            return
            
        if self._focus_type == 'year':
            self._current_datetime = self._current_datetime.addYears(-1)
        elif self._focus_type == 'month':
            self._current_datetime = self._current_datetime.addMonths(-1)
        elif self._focus_type == 'day':
            self._current_datetime = self._current_datetime.addDays(-1)
        elif self._focus_type == 'hour':
            self._current_datetime = self._current_datetime.addSecs(-3600)
        elif self._focus_type == 'minute':
            self._current_datetime = self._current_datetime.addSecs(-60)
        elif self._focus_type == 'second':
            self._current_datetime = self._current_datetime.addSecs(-1)
        self._update_display()
        self.dateTimeChanged.emit(self._current_datetime)
        
    def _update_display(self):
        """更新显示"""
        self._update_focus_style()
        
    def _on_date_changed(self, date):
        """处理日期变化"""
        self._current_datetime.setDate(date)
        self._update_display()
        self.dateTimeChanged.emit(self._current_datetime)
        if self._popup:
            self._popup.hide()
        
    def _on_time_changed(self, index):
        """处理时间变化"""
        hour = int(self.hour_combo.currentText())
        minute = int(self.minute_combo.currentText())
        second = int(self.second_combo.currentText())
        self._current_datetime.setTime(QTime(hour, minute, second))
        self._update_display()
        self.dateTimeChanged.emit(self._current_datetime)
        
    def setDateTime(self, datetime):
        """设置日期时间"""
        self._current_datetime = datetime
        self._update_display()
        
    def dateTime(self):
        """获取当前选择的日期时间"""
        return self._current_datetime
        
    def clearDateTime(self):
        """清除日期时间，重置选择器状态"""
        self._current_datetime = QDateTime()  # 创建一个空的日期时间对象
        self._focus_type = None  # 清除焦点
        self._update_display()  # 更新显示
        self.dateTimeChanged.emit(self._current_datetime)  # 发送信号通知变化

    def setBackgroundColor(self, color):
        """设置背景颜色
        
        Args:
            color (str): 背景颜色值，如 'white', '#ffffff' 等
        """
        self._background_color = color
        self.updateStyle()
        
    def setCustomStyle(self, style):
        """设置自定义样式
        
        Args:
            style (str): 自定义的QSS样式字符串
        """
        self._custom_style = style
        self.updateStyle()
        
    def updateStyle(self):
        """更新组件样式"""
        if self._custom_style:
            self.setStyleSheet(self._custom_style)
        else:
            self.setStyleSheet(self._default_style % {"bg_color": self._background_color})
            
    def setWidth(self, width):
        """设置组件宽度
        
        Args:
            width (int): 组件宽度
        """
        self.setMinimumWidth(width)
        # 根据外部宽度调整内部容器最小宽度
        inner_width = width - 2  # 减去边框宽度
        self.display_widget.setMinimumWidth(inner_width)
        # 更新内部布局的边距
        display_layout = self.display_widget.layout()
        if display_layout:
            display_layout.setContentsMargins(6, 0, 6, 0) 