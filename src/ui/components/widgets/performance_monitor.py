from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import QTimer
from utils.logger import get_logger
from datetime import datetime, timedelta
import psutil
import os

logger = get_logger(__name__)

class PerformanceMonitor(QWidget):
    """性能监控组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # 创建定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(60000)  # 每分钟更新一次
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建控制区域
        control_layout = QHBoxLayout()
        
        # 时间范围选择
        control_layout.addWidget(QLabel("时间范围:"))
        self.time_range = QComboBox()
        self.time_range.addItems(["最近1小时", "最近24小时", "最近7天", "最近30天"])
        self.time_range.currentIndexChanged.connect(self.update_stats)
        control_layout.addWidget(self.time_range)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.update_stats)
        control_layout.addWidget(refresh_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "操作类型", "总次数", "平均耗时(ms)", "最大耗时(ms)", "最小耗时(ms)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # 创建系统资源监控
        resource_layout = QHBoxLayout()
        
        # CPU使用率
        self.cpu_label = QLabel("CPU使用率: 0%")
        resource_layout.addWidget(self.cpu_label)
        
        # 内存使用率
        self.memory_label = QLabel("内存使用率: 0%")
        resource_layout.addWidget(self.memory_label)
        
        # 磁盘使用率
        self.disk_label = QLabel("磁盘使用率: 0%")
        resource_layout.addWidget(self.disk_label)
        
        resource_layout.addStretch()
        layout.addLayout(resource_layout)
        
    def update_stats(self):
        """更新性能统计"""
        try:
            # 获取时间范围
            time_range = self.time_range.currentText()
            end_time = datetime.now()
            
            if time_range == "最近1小时":
                start_time = end_time - timedelta(hours=1)
            elif time_range == "最近24小时":
                start_time = end_time - timedelta(days=1)
            elif time_range == "最近7天":
                start_time = end_time - timedelta(days=7)
            else:  # 最近30天
                start_time = end_time - timedelta(days=30)
                
            # 获取性能日志
            logs = self.get_performance_logs(start_time, end_time)
            
            # 更新表格
            self.table.setRowCount(len(logs))
            for row, (operation, stats) in enumerate(logs.items()):
                self.table.setItem(row, 0, QTableWidgetItem(operation))
                self.table.setItem(row, 1, QTableWidgetItem(str(stats["count"])))
                self.table.setItem(row, 2, QTableWidgetItem(f"{stats['avg']:.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{stats['max']:.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(f"{stats['min']:.2f}"))
                
            # 更新系统资源使用情况
            self.update_system_resources()
            
        except Exception as e:
            logger.error(f"更新性能统计失败: {str(e)}")
            
    def get_performance_logs(self, start_time: datetime, end_time: datetime) -> dict:
        """获取性能日志
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            性能统计信息
        """
        # TODO: 从日志文件读取性能数据
        # 这里需要实现从日志文件读取性能数据的逻辑
        return {}
        
    def update_system_resources(self):
        """更新系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent()
            self.cpu_label.setText(f"CPU使用率: {cpu_percent}%")
            
            # 内存使用率
            memory = psutil.virtual_memory()
            self.memory_label.setText(f"内存使用率: {memory.percent}%")
            
            # 磁盘使用率
            disk = psutil.disk_usage("/")
            self.disk_label.setText(f"磁盘使用率: {disk.percent}%")
            
        except Exception as e:
            logger.error(f"更新系统资源使用情况失败: {str(e)}")
            
    def closeEvent(self, event):
        """关闭事件"""
        self.timer.stop()
        super().closeEvent(event) 