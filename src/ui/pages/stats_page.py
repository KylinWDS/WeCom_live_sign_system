# PySide6导入
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                             QFrame, QTabWidget, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen

# UI相关导入
from src.ui.managers.style import StyleManager
from src.ui.utils.widget_utils import WidgetUtils
from src.ui.components.widgets.chart_widget import ChartWidget
from src.ui.components.dialogs.io_dialog import IODialog
from src.ui.components.dialogs.export_dialog import ExportDialog

# 核心功能导入
from src.core.database import DatabaseManager

# 工具类导入
from src.utils.logger import get_logger

logger = get_logger(__name__)

class StatsPage(QWidget):
    """数据统计页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("statsPage")
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 创建工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # 创建统计卡片
        cards_layout = QHBoxLayout()
        
        # 直播总数卡片
        self.total_lives_card = self._create_stat_card("直播总数", "0")
        cards_layout.addWidget(self.total_lives_card)
        
        # 总观看人数卡片
        self.total_watches_card = self._create_stat_card("总观看人数", "0")
        cards_layout.addWidget(self.total_watches_card)
        
        # 总签到人数卡片
        self.total_signs_card = self._create_stat_card("总签到人数", "0")
        cards_layout.addWidget(self.total_signs_card)
        
        # 平均观看时长卡片
        self.avg_watch_card = self._create_stat_card("平均观看时长", "0分钟")
        cards_layout.addWidget(self.avg_watch_card)
        
        layout.addLayout(cards_layout)
        
        # 创建图表区域
        charts_tab = QTabWidget()
        
        # 每日数据图表
        daily_tab = QWidget()
        daily_layout = QVBoxLayout(daily_tab)
        self.daily_chart = ChartWidget()
        daily_layout.addWidget(self.daily_chart)
        charts_tab.addTab(daily_tab, "每日数据")
        
        # 观看时长分布图表
        duration_tab = QWidget()
        duration_layout = QVBoxLayout(duration_tab)
        self.duration_chart = ChartWidget()
        duration_layout.addWidget(self.duration_chart)
        charts_tab.addTab(duration_tab, "观看时长分布")
        
        # 签到率趋势图表
        sign_rate_tab = QWidget()
        sign_rate_layout = QVBoxLayout(sign_rate_tab)
        self.sign_rate_chart = ChartWidget()
        sign_rate_layout.addWidget(self.sign_rate_chart)
        charts_tab.addTab(sign_rate_tab, "签到率趋势")
        
        layout.addWidget(charts_tab)
        
        # 创建排行表格
        self.ranking_table = self._create_ranking_table()
        layout.addWidget(self.ranking_table)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_main_style())
        
        # 设置控件样式
        WidgetUtils.set_combo_style(self.range_combo)
        WidgetUtils.set_combo_style(self.chart_type_combo)
        WidgetUtils.set_table_style(self.ranking_table)
    
    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 时间范围选择
        layout.addWidget(QLabel("时间范围:"))
        self.range_combo = QComboBox()
        self.range_combo.addItems(["最近7天", "最近30天", "最近90天", "最近365天"])
        self.range_combo.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.range_combo)
        
        # 图表类型选择
        layout.addWidget(QLabel("图表类型:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["折线图", "柱状图", "饼图"])
        self.chart_type_combo.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.chart_type_combo)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("toolButton")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        
        # 导入按钮
        import_btn = QPushButton("导入数据")
        import_btn.clicked.connect(self.show_import_dialog)
        layout.addWidget(import_btn)
        
        # 导出按钮
        export_btn = QPushButton("导出数据")
        export_btn.clicked.connect(self.show_export_dialog)
        layout.addWidget(export_btn)
        
        return toolbar
    
    def _create_stat_card(self, title: str, value: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(100)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)
        
        # 数值
        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        layout.addWidget(value_label)
        
        return card
    
    def _create_ranking_table(self) -> QTableWidget:
        """创建排行表格"""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "直播ID", "标题", "观看人数", "签到人数",
            "总观看时长", "平均观看时长", "签到率"
        ])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        return table
    
    def load_data(self):
        """加载数据"""
        try:
            # 获取时间范围
            range_text = self.range_combo.currentText()
            if range_text == "最近7天":
                days = 7
            elif range_text == "最近30天":
                days = 30
            elif range_text == "最近90天":
                days = 90
            else:
                days = 365
            
            # 获取统计数据
            stats = self.db_manager.get_live_stats(days)
            
            # 更新统计卡片
            self.total_lives_card.findChild(QLabel, "cardValue").setText(str(stats["total_lives"]))
            self.total_watches_card.findChild(QLabel, "cardValue").setText(str(stats["total_watches"]))
            self.total_signs_card.findChild(QLabel, "cardValue").setText(str(stats["total_signs"]))
            self.avg_watch_card.findChild(QLabel, "cardValue").setText(f"{stats['avg_watch_time']:.1f}分钟")
            
            # 更新每日数据图表
            x_data = [d["date"] for d in stats["daily_stats"]]
            y_data = [d["watch_count"] for d in stats["daily_stats"]]
            chart_type = self.chart_type_combo.currentText()
            
            if chart_type == "折线图":
                self.daily_chart.plot_line(x_data, y_data, "每日观看人数统计", "日期", "观看人数")
            elif chart_type == "柱状图":
                self.daily_chart.plot_bar(x_data, y_data, "每日观看人数统计", "日期", "观看人数")
            else:
                self.daily_chart.plot_pie(dict(zip(x_data, y_data)), "每日观看人数统计")
            
            # 更新观看时长分布图表
            duration_data = {
                "0-30分钟": stats["duration_stats"]["0-30"],
                "30-60分钟": stats["duration_stats"]["30-60"],
                "60-90分钟": stats["duration_stats"]["60-90"],
                "90分钟以上": stats["duration_stats"]["90+"]
            }
            self.duration_chart.plot_pie(duration_data, "观看时长分布")
            
            # 更新签到率趋势图表
            x_data = [d["date"] for d in stats["daily_stats"]]
            y_data = [d["sign_rate"] for d in stats["daily_stats"]]
            self.sign_rate_chart.plot_line(x_data, y_data, "签到率趋势", "日期", "签到率(%)")
            
            # 获取排行数据
            rankings = self.db_manager.get_live_rankings(days)
            
            # 更新排行表格
            self.ranking_table.setRowCount(len(rankings))
            for i, r in enumerate(rankings):
                self.ranking_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
                self.ranking_table.setItem(i, 1, QTableWidgetItem(r["title"]))
                self.ranking_table.setItem(i, 2, QTableWidgetItem(str(r["watch_count"])))
                self.ranking_table.setItem(i, 3, QTableWidgetItem(str(r["sign_count"])))
                self.ranking_table.setItem(i, 4, QTableWidgetItem(f"{r['total_duration']:.1f}分钟"))
                self.ranking_table.setItem(i, 5, QTableWidgetItem(f"{r['avg_duration']:.1f}分钟"))
                self.ranking_table.setItem(i, 6, QTableWidgetItem(f"{r['sign_rate']:.1f}%"))
            
            # 调整列宽
            self.ranking_table.resizeColumnsToContents()
            
            logger.info("数据加载成功")
            
        except Exception as e:
            logger.error(f"数据加载失败: {str(e)}")
    
    def show_import_dialog(self):
        """显示导入对话框"""
        dialog = IODialog(self.db_manager, self)
        dialog.exec()
        if dialog.result() == QDialog.DialogCode.Accepted:
            self.load_data()  # 刷新数据
            
    def show_export_dialog(self):
        """显示导出对话框"""
        dialog = ExportDialog(self.db_manager, self)
        dialog.exec() 