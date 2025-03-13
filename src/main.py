# 标准库导入
import sys
import os
import traceback

# PySide6导入
from PySide6.QtWidgets import QApplication

# UI相关导入
from src.ui.windows.login_window import LoginWindow
from src.ui.components.dialogs.init_wizard import InitWizard

# 核心功能导入
from src.core.database import DatabaseManager
from src.core.config_manager import ConfigManager
from src.core.auth_manager import AuthManager
from src.core.initialization import initialize_config_manager

# 工具类导入
from src.utils.logger import get_logger

# 初始化ConfigManager
config_manager = initialize_config_manager()

logger = get_logger(__name__)

def main():
    """主程序入口"""
    try:
        # 创建应用
        logger.info("创建应用...")
        app = QApplication(sys.argv)
        
        try:
            # 初始化管理器
            logger.info("初始化数据库管理器...")
            db_manager = DatabaseManager()
            logger.info("数据库管理器初始化成功")
            
            logger.info("初始化认证管理器...")
            auth_manager = AuthManager(db_manager)
            logger.info("认证管理器初始化成功")
        except Exception as init_error:
            logger.error(f"初始化管理器失败: {str(init_error)}\n{traceback.format_exc()}")
            raise
        
        # 检查是否首次运行
        logger.info("检查是否首次运行...")
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
        logger.info("显示登录窗口...")
        login_window = LoginWindow(db_manager, config_manager, auth_manager)
        login_window.show()
        
        # 运行应用
        logger.info("程序启动成功")
        sys.exit(app.exec())
        
    except Exception as e:
        error_msg = f"程序启动失败: {str(e)}\n"
        error_msg += "详细错误信息:\n"
        error_msg += traceback.format_exc()
        logger.error(error_msg)
        raise

if __name__ == "__main__":
    main()