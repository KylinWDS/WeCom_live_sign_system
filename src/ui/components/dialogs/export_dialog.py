from PySide6.QtWidgets import QComboBox, QProgressBar, QMessageBox
from PySide6.QtCore import Qt
from src.core.export_manager import ExportManager
from src.utils.logger import get_logger
from .io_dialog import IODialog
from .data_dialog import DataDialog

logger = get_logger(__name__)

class ExportDialog(IODialog, DataDialog):
    """导出对话框"""
    
    def __init__(self, db_manager, parent=None):
        IODialog.__init__(self, parent, "导出数据", False)
        DataDialog.__init__(self, parent, "导出数据", ["数据类型", "直播", "选项"])
        
        self.db_manager = db_manager
        self.export_manager = ExportManager(db_manager)
        
        # 创建数据类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["直播数据", "观众数据", "签到数据", "统计报表"])
        self.content_layout.addWidget(self.type_combo)
        
        # 创建直播选择
        self.live_combo = QComboBox()
        self.load_live_list()
        self.content_layout.addWidget(self.live_combo)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.content_layout.addWidget(self.progress_bar)
        
        # 设置按钮
        self.set_ok_button_text("导出")
        self.ok_button.clicked.disconnect()
        self.ok_button.clicked.connect(self.export_data)
        
    def load_live_list(self):
        """加载直播列表"""
        try:
            lives = self.db_manager.get_all_livings()
            self.live_combo.clear()
            self.live_combo.addItem("全部", None)
            for live in lives:
                self.live_combo.addItem(live.title, live.id)
        except Exception as e:
            logger.error(f"加载直播列表失败: {str(e)}")
            
    def export_data(self):
        """导出数据"""
        try:
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 显示忙碌状态
            
            # 获取文件路径
            file_path = self.get_file_path()
            if not file_path:
                return
                
            # 获取数据类型和直播ID
            data_type = self.type_combo.currentText()
            live_id = self.live_combo.currentData()
            
            # 导出数据
            if data_type == "直播数据":
                df = self.export_manager.export_live_data(live_id, ["*"])
            elif data_type == "观众数据":
                df = self.export_manager.export_viewer_data(live_id, ["*"])
            elif data_type == "签到数据":
                df = self.export_manager.export_sign_data(live_id, ["*"])
            else:
                df = self.export_manager.export_stats_report(live_id)
                
            # 保存到Excel
            options = self.get_options()
            self.export_manager.save_to_excel(df, file_path, **options)
                
            QMessageBox.information(self, "成功", "数据导出成功")
            self.accept()
            
        except Exception as e:
            logger.error(f"导出数据失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
        finally:
            self.progress_bar.setVisible(False) 