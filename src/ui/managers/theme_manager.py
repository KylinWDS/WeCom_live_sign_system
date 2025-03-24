from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.utils.logger import get_logger
from .style import StyleManager

logger = get_logger(__name__)

class ThemeManager:
    """主题管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.current_theme = "light"
            self._setup_system_theme_detection()
    
    def _setup_system_theme_detection(self):
        """设置系统主题检测"""
        try:
            # 获取系统主题
            app = QApplication.instance()
            if app:
                app.paletteChanged.connect(self._on_palette_changed)
        except Exception as e:
            logger.error(f"设置系统主题检测失败: {str(e)}")
    
    def _on_palette_changed(self):
        """系统主题变化处理"""
        try:
            if self.current_theme == "system":
                self.apply_theme("system")
        except Exception as e:
            logger.error(f"处理系统主题变化失败: {str(e)}")
    
    def get_system_theme(self) -> str:
        """获取系统主题
        
        Returns:
            str: 系统主题，"light" 或 "dark"
        """
        try:
            app = QApplication.instance()
            if app:
                palette = app.palette()
                # 检查背景色亮度
                bg_color = palette.color(palette.Window)
                brightness = (bg_color.red() * 299 + bg_color.green() * 587 + bg_color.blue() * 114) / 1000
                return "dark" if brightness < 128 else "light"
            return "light"
        except Exception as e:
            logger.error(f"获取系统主题失败: {str(e)}")
            return "light"
    
    def apply_theme(self, theme: str):
        """应用主题
        
        Args:
            theme: 主题名称，"system"、"light" 或 "dark"
        """
        try:
            self.current_theme = theme
            app = QApplication.instance()
            if not app:
                return
                
            # 获取样式表
            if theme == "system":
                system_theme = self.get_system_theme()
                style = getattr(StyleManager, f"get_{system_theme}_style")()
            elif theme == "light":
                style = StyleManager.get_light_style()
            elif theme == "dark":
                style = StyleManager.get_dark_style()
            else:
                style = StyleManager.get_light_style()  # 默认使用亮色主题
            
            # 应用样式
            app.setStyleSheet(style)
            logger.info(f"应用主题成功: {theme}")
            
        except Exception as e:
            logger.error(f"应用主题失败: {str(e)}")
    
    def get_current_theme(self) -> str:
        """获取当前主题
        
        Returns:
            str: 当前主题名称
        """
        return self.current_theme 