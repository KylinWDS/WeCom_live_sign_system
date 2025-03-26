"""
提供图标访问的工具模块，使用PySide6内置的标准图标
"""
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QStyle, QApplication
import os
from typing import Optional

# 图标映射
ICON_MAP = {
    # 常用图标
    "app_icon": QStyle.SP_DesktopIcon,
    "ok": QStyle.SP_DialogOkButton,
    "cancel": QStyle.SP_DialogCancelButton,
    "close": QStyle.SP_DialogCloseButton,
    "help": QStyle.SP_DialogHelpButton,
    "info": QStyle.SP_MessageBoxInformation,
    "warning": QStyle.SP_MessageBoxWarning,
    "error": QStyle.SP_MessageBoxCritical,
    "question": QStyle.SP_MessageBoxQuestion,
    
    # 状态图标
    "status_success": QStyle.SP_DialogApplyButton,
    "status_warning": QStyle.SP_MessageBoxWarning,
    "status_error": QStyle.SP_MessageBoxCritical,
    "status_waiting": QStyle.SP_BrowserReload,
    
    # 操作图标
    "action_add": QStyle.SP_FileDialogNewFolder,
    "action_delete": QStyle.SP_DialogDiscardButton,
    "action_edit": QStyle.SP_FileDialogDetailedView,
    "action_refresh": QStyle.SP_BrowserReload,
    "action_save": QStyle.SP_DialogSaveButton,
    "action_search": QStyle.SP_FileDialogContentsView,
    "action_settings": QStyle.SP_FileDialogDetailedView,
    "action_export": QStyle.SP_ArrowRight,
    "action_import": QStyle.SP_ArrowLeft,
    
    # 文件图标
    "file": QStyle.SP_FileIcon,
    "folder": QStyle.SP_DirIcon,
    "document": QStyle.SP_FileDialogContentsView,
    
    # 媒体控制图标
    "play": QStyle.SP_MediaPlay,
    "pause": QStyle.SP_MediaPause,
    "stop": QStyle.SP_MediaStop,
    "volume": QStyle.SP_MediaVolume,
    "mute": QStyle.SP_MediaVolumeMuted,
    
    # 导航图标
    "home": QStyle.SP_DirHomeIcon,
    "back": QStyle.SP_ArrowBack,
    "forward": QStyle.SP_ArrowForward,
    "up": QStyle.SP_ArrowUp,
    "down": QStyle.SP_ArrowDown,
    
    # 其他图标
    "computer": QStyle.SP_ComputerIcon,
    "drive": QStyle.SP_DriveHDIcon,
    "network": QStyle.SP_DriveNetIcon,
    "user": QStyle.SP_DirIcon,  # 用目录图标代替用户图标
    
    # 以图标字符作为标签的图标
    "📺": QStyle.SP_TitleBarMenuButton,
    "👥": QStyle.SP_FileDialogListView,
    "✅": QStyle.SP_DialogApplyButton,
    
    # Font Awesome风格图标（用标准图标模拟）
    "fas.calendar-plus": QStyle.SP_FileDialogNewFolder,
    "fas.chart-line": QStyle.SP_FileDialogDetailedView,
    "fas.users-cog": QStyle.SP_DirIcon,
}

def get_icon(icon_name: str, size: Optional[QSize] = None) -> QIcon:
    """
    获取指定名称的图标
    
    Args:
        icon_name: 图标名称
        size: 图标尺寸，如果为None则使用默认尺寸
        
    Returns:
        QIcon对象
    """
    # 获取应用实例
    app = QApplication.instance()
    if not app:
        return QIcon()
    
    # 获取样式
    style = app.style()
    
    # 检查是否在映射中
    if icon_name in ICON_MAP:
        icon = style.standardIcon(ICON_MAP[icon_name])
    else:
        # 如果找不到映射，返回默认图标
        icon = style.standardIcon(QStyle.SP_FileIcon)
    
    # 设置图标尺寸
    if size and not icon.isNull():
        icon.setActualSize(size)
        
    return icon

def get_app_icon() -> QIcon:
    """获取应用图标"""
    return get_icon("app_icon")

def get_action_icon(action_name: str) -> QIcon:
    """获取操作图标"""
    return get_icon(f"action_{action_name}")

def get_status_icon(status_name: str) -> QIcon:
    """获取状态图标"""
    return get_icon(f"status_{status_name}") 