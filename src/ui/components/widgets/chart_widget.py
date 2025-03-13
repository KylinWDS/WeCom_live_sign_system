from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np
from typing import List, Dict, Any

class ChartWidget(QWidget):
    """图表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建绘图窗口
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)
        
    def plot_line(self, x_data: List[Any], y_data: List[Any], 
                  title: str = "", x_label: str = "", y_label: str = "",
                  color: str = "#1f77b4"):
        """绘制折线图
        
        Args:
            x_data: X轴数据
            y_data: Y轴数据
            title: 图表标题
            x_label: X轴标签
            y_label: Y轴标签
            color: 线条颜色
        """
        self.plot_widget.clear()
        self.plot_widget.setTitle(title)
        self.plot_widget.setLabel("left", y_label)
        self.plot_widget.setLabel("bottom", x_label)
        
        # 绘制折线
        self.plot_widget.plot(x_data, y_data, pen=color)
        
    def plot_bar(self, x_data: List[Any], y_data: List[Any],
                 title: str = "", x_label: str = "", y_label: str = "",
                 color: str = "#1f77b4"):
        """绘制柱状图
        
        Args:
            x_data: X轴数据
            y_data: Y轴数据
            title: 图表标题
            x_label: X轴标签
            y_label: Y轴标签
            color: 柱状图颜色
        """
        self.plot_widget.clear()
        self.plot_widget.setTitle(title)
        self.plot_widget.setLabel("left", y_label)
        self.plot_widget.setLabel("bottom", x_label)
        
        # 创建柱状图
        bar_graph = pg.BarGraphItem(x=range(len(x_data)), height=y_data, width=0.6)
        self.plot_widget.addItem(bar_graph)
        
        # 设置X轴刻度
        self.plot_widget.getAxis("bottom").setTicks([[(i, str(x)) for i, x in enumerate(x_data)]])
        
    def plot_pie(self, data: Dict[str, float],
                 title: str = "", colors: List[str] = None):
        """绘制饼图
        
        Args:
            data: 数据字典,key为标签,value为数值
            title: 图表标题
            colors: 颜色列表
        """
        self.plot_widget.clear()
        self.plot_widget.setTitle(title)
        
        # 计算百分比
        total = sum(data.values())
        percentages = [v/total for v in data.values()]
        
        # 创建饼图
        pie = pg.PieChartItem(values=percentages, labels=list(data.keys()),
                            colors=colors or ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"])
        self.plot_widget.addItem(pie)
        
    def plot_scatter(self, x_data: List[float], y_data: List[float],
                    title: str = "", x_label: str = "", y_label: str = "",
                    color: str = "#1f77b4"):
        """绘制散点图
        
        Args:
            x_data: X轴数据
            y_data: Y轴数据
            title: 图表标题
            x_label: X轴标签
            y_label: Y轴标签
            color: 散点颜色
        """
        self.plot_widget.clear()
        self.plot_widget.setTitle(title)
        self.plot_widget.setLabel("left", y_label)
        self.plot_widget.setLabel("bottom", x_label)
        
        # 绘制散点
        scatter = pg.ScatterPlotItem(x=x_data, y=y_data, pen=color, brush=color)
        self.plot_widget.addItem(scatter)
        
    def save_to_excel(self, worksheet):
        """保存图表到Excel
        
        Args:
            worksheet: Excel工作表对象
        """
        # 获取图表图像
        img = self.plot_widget.grab()
        
        # 保存到Excel
        worksheet.insert_image("A1", img) 