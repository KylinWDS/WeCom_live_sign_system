from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QSize, QRect
from PySide6.QtWidgets import QWidget
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AnimationManager:
    """动画管理器"""
    
    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300):
        """淡入动画
        
        Args:
            widget: 目标控件
            duration: 动画时长(毫秒)
        """
        try:
            widget.setWindowOpacity(0)
            widget.show()
            
            animation = QPropertyAnimation(widget, b"windowOpacity")
            animation.setDuration(duration)
            animation.setStartValue(0)
            animation.setEndValue(1)
            animation.setEasingCurve(QEasingCurve.InOutCubic)
            animation.start()
        except Exception as e:
            logger.error(f"淡入动画失败: {str(e)}")
            
    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300):
        """淡出动画
        
        Args:
            widget: 目标控件
            duration: 动画时长(毫秒)
        """
        try:
            animation = QPropertyAnimation(widget, b"windowOpacity")
            animation.setDuration(duration)
            animation.setStartValue(1)
            animation.setEndValue(0)
            animation.setEasingCurve(QEasingCurve.InOutCubic)
            animation.finished.connect(widget.hide)
            animation.start()
        except Exception as e:
            logger.error(f"淡出动画失败: {str(e)}")
            
    @staticmethod
    def slide_in(widget: QWidget, direction: str = "right", duration: int = 300):
        """滑入动画
        
        Args:
            widget: 目标控件
            direction: 方向("left", "right", "up", "down")
            duration: 动画时长(毫秒)
        """
        try:
            widget.show()
            start_pos = widget.pos()
            end_pos = start_pos
            
            if direction == "left":
                widget.move(start_pos.x() + widget.width(), start_pos.y())
                end_pos = start_pos
            elif direction == "right":
                widget.move(start_pos.x() - widget.width(), start_pos.y())
                end_pos = start_pos
            elif direction == "up":
                widget.move(start_pos.x(), start_pos.y() + widget.height())
                end_pos = start_pos
            elif direction == "down":
                widget.move(start_pos.x(), start_pos.y() - widget.height())
                end_pos = start_pos
                
            animation = QPropertyAnimation(widget, b"pos")
            animation.setDuration(duration)
            animation.setStartValue(widget.pos())
            animation.setEndValue(end_pos)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()
        except Exception as e:
            logger.error(f"滑入动画失败: {str(e)}")
            
    @staticmethod
    def slide_out(widget: QWidget, direction: str = "right", duration: int = 300):
        """滑出动画
        
        Args:
            widget: 目标控件
            direction: 方向("left", "right", "up", "down")
            duration: 动画时长(毫秒)
        """
        try:
            start_pos = widget.pos()
            end_pos = start_pos
            
            if direction == "left":
                end_pos = QPoint(start_pos.x() - widget.width(), start_pos.y())
            elif direction == "right":
                end_pos = QPoint(start_pos.x() + widget.width(), start_pos.y())
            elif direction == "up":
                end_pos = QPoint(start_pos.x(), start_pos.y() - widget.height())
            elif direction == "down":
                end_pos = QPoint(start_pos.x(), start_pos.y() + widget.height())
                
            animation = QPropertyAnimation(widget, b"pos")
            animation.setDuration(duration)
            animation.setStartValue(start_pos)
            animation.setEndValue(end_pos)
            animation.setEasingCurve(QEasingCurve.InCubic)
            animation.finished.connect(widget.hide)
            animation.start()
        except Exception as e:
            logger.error(f"滑出动画失败: {str(e)}")
            
    @staticmethod
    def scale_in(widget: QWidget, duration: int = 300):
        """缩放进入动画
        
        Args:
            widget: 目标控件
            duration: 动画时长(毫秒)
        """
        try:
            widget.setWindowOpacity(0)
            widget.show()
            
            # 保存原始大小
            original_size = widget.size()
            
            # 设置初始大小为0
            widget.resize(0, 0)
            
            # 创建大小动画
            size_animation = QPropertyAnimation(widget, b"size")
            size_animation.setDuration(duration)
            size_animation.setStartValue(QSize(0, 0))
            size_animation.setEndValue(original_size)
            size_animation.setEasingCurve(QEasingCurve.OutBack)
            
            # 创建透明度动画
            opacity_animation = QPropertyAnimation(widget, b"windowOpacity")
            opacity_animation.setDuration(duration)
            opacity_animation.setStartValue(0)
            opacity_animation.setEndValue(1)
            opacity_animation.setEasingCurve(QEasingCurve.InOutCubic)
            
            # 同时启动两个动画
            size_animation.start()
            opacity_animation.start()
        except Exception as e:
            logger.error(f"缩放进入动画失败: {str(e)}")
            
    @staticmethod
    def scale_out(widget: QWidget, duration: int = 300):
        """缩放退出动画
        
        Args:
            widget: 目标控件
            duration: 动画时长(毫秒)
        """
        try:
            # 保存原始大小
            original_size = widget.size()
            
            # 创建大小动画
            size_animation = QPropertyAnimation(widget, b"size")
            size_animation.setDuration(duration)
            size_animation.setStartValue(original_size)
            size_animation.setEndValue(QSize(0, 0))
            size_animation.setEasingCurve(QEasingCurve.InBack)
            
            # 创建透明度动画
            opacity_animation = QPropertyAnimation(widget, b"windowOpacity")
            opacity_animation.setDuration(duration)
            opacity_animation.setStartValue(1)
            opacity_animation.setEndValue(0)
            opacity_animation.setEasingCurve(QEasingCurve.InOutCubic)
            
            # 同时启动两个动画
            size_animation.start()
            opacity_animation.start()
            
            # 动画结束后隐藏控件
            opacity_animation.finished.connect(widget.hide)
        except Exception as e:
            logger.error(f"缩放退出动画失败: {str(e)}")
            
    @staticmethod
    def shake(widget: QWidget, duration: int = 500, distance: int = 10):
        """抖动动画
        
        Args:
            widget: 目标控件
            duration: 动画时长(毫秒)
            distance: 抖动距离(像素)
        """
        try:
            start_pos = widget.pos()
            
            # 创建位置动画
            animation = QPropertyAnimation(widget, b"pos")
            animation.setDuration(duration)
            
            # 设置关键帧
            key_values = []
            for i in range(10):
                if i % 2 == 0:
                    key_values.append(QPoint(start_pos.x() + distance, start_pos.y()))
                else:
                    key_values.append(QPoint(start_pos.x() - distance, start_pos.y()))
                    
            # 添加关键帧
            for i, value in enumerate(key_values):
                animation.setKeyValueAt(i / len(key_values), value)
                
            # 设置结束位置为原始位置
            animation.setEndValue(start_pos)
            animation.setEasingCurve(QEasingCurve.OutElastic)
            animation.start()
        except Exception as e:
            logger.error(f"抖动动画失败: {str(e)}") 