# 标准库导入
import sys
import os

# PySide6导入
from PySide6.QtWidgets import QApplication

# UI相关导入
from ui.windows.login_window import LoginWindow
from ui.dialogs.init_wizard import InitWizard

# 核心功能导入
from core.database import DatabaseManager
from core.config_manager import ConfigManager
from core.auth_manager import AuthManager

# 工具类导入
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """主程序入口"""
    try:
        # 创建应用
        app = QApplication(sys.argv)
        
        # 初始化管理器
        db_manager = DatabaseManager()
        config_manager = ConfigManager()
        auth_manager = AuthManager(db_manager)
        
        # 检查是否首次运行
        if not config_manager.get("system", {}).get("initialized", False):
            # 显示初始化配置向导
            wizard = InitWizard(db_manager, config_manager, auth_manager)
            if wizard.exec() != InitWizard.Accepted:
                logger.info("用户取消初始化配置")
                return
                
            # 标记为已初始化
            config_manager.set("system.initialized", True)
            config_manager.save_config()
            
        # 显示登录窗口
        login_window = LoginWindow(db_manager, config_manager, auth_manager)
        login_window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"程序启动失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()