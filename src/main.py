# 标准库导入
import sys
import os
import traceback
import json

# PySide6导入
from PySide6.QtWidgets import QApplication, QMessageBox

# UI相关导入
from .ui.windows.login_window import LoginWindow
from .ui.components.dialogs.init_wizard import InitWizard

# 核心功能导入
from .core.database import DatabaseManager
from .core.config_manager import ConfigManager
from .core.auth_manager import AuthManager

# 工具类导入
from .utils.logger import get_logger, setup_logger

# 应用上下文导入
from .app import init_app_context


def show_error_dialog(title: str, message: str):
    """显示错误对话框"""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setDetailedText(traceback.format_exc())
    msg_box.exec()


def get_config_path():
    """获取配置文件路径
    
    Returns:
        tuple: (配置目录路径, 是否需要初始化)
    """
    # 默认配置目录
    default_config_dir = os.path.join(os.path.expanduser("~"), ".wecom_live_sign")
    default_config_file = os.path.join(default_config_dir, "config.json")

    # 确保默认配置目录存在
    os.makedirs(default_config_dir, exist_ok=True)

    # 如果默认配置文件不存在，创建默认配置
    if not os.path.exists(default_config_file):
        default_config = {
            "initialized": False,  # 是否已初始化
            "paths": {
                "config": "",  # 配置文件路径
                "data": "",  # 数据库路径
                "log": "",  # 日志路径
                "backup": ""  # 备份路径
            }
        }
        try:
            with open(default_config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"创建默认配置文件失败: {str(e)}")
            return default_config_dir, True

    # 读取默认配置文件
    try:
        with open(default_config_file, 'r', encoding='utf-8') as f:
            default_config = json.load(f)
            initialized = default_config.get('initialized', False)

            # 如果已经初始化，检查所有路径是否都已配置
            if initialized:
                paths = default_config.get('paths', {})
                if all(paths.values()) and all(os.path.exists(path) for path in paths.values()):
                    return paths['config'], False

            # 如果未初始化或路径配置不完整，需要进行初始化
            return default_config_dir, True

    except Exception as e:
        print(f"读取默认配置文件失败: {str(e)}")
        return default_config_dir, True


def main():
    """主程序入口"""
    try:
        # 创建应用实例
        app = QApplication(sys.argv)

        # 获取配置路径
        config_dir, need_init = get_config_path()

        # 初始化配置管理器
        config_manager = ConfigManager()
        config_manager.config_dir = config_dir  # 先设置配置目录

        # 设置默认日志目录（在用户配置目录下）
        default_log_dir = os.path.join(os.path.expanduser("~"), ".wecom_live_sign", "logs")

        if need_init:
            # 首次运行时使用默认日志配置
            setup_logger(
                log_dir=default_log_dir,
                log_level="INFO",
                log_retention=30
            )
            logger = get_logger(__name__)

            # 创建数据库管理器和认证管理器（空配置）
            db_manager = DatabaseManager()
            auth_manager = AuthManager(db_manager)
            
            # 初始化应用上下文
            init_app_context(db_manager, config_manager, auth_manager)

            # 首次运行，显示初始化向导
            wizard = InitWizard(db_manager, config_manager, auth_manager)
            if wizard.exec() != InitWizard.Accepted:
                logger.info("用户取消初始化")
                return

            # 获取已初始化的管理器
            config_manager = wizard.config_manager
            db_manager = wizard.db_manager
            auth_manager = wizard.auth_manager
            
            # 更新应用上下文
            init_app_context(db_manager, config_manager, auth_manager)

            # 使用用户配置的日志设置
            paths = config_manager.config.get("paths", {})
            log_path = paths.get("log", default_log_dir)  # 如果用户没有指定，使用默认路径
            log_level = config_manager.get("system.log_level", "INFO")
            log_retention = config_manager.get("system.log_retention", 30)
            setup_logger(log_path, log_level, log_retention)
            logger = get_logger(__name__)

        else:
            # 正常启动流程
            if not config_manager.initialize(config_dir):
                raise RuntimeError("初始化配置管理器失败")

            # 设置日志记录器
            paths = config_manager.config.get("paths", {})
            log_path = paths.get("log", default_log_dir)  # 如果用户没有指定，使用默认路径
            log_level = config_manager.get("system.log_level", "INFO")
            log_retention = config_manager.get("system.log_retention", 30)
            setup_logger(log_path, log_level, log_retention)
            logger = get_logger(__name__)

            # 初始化数据库管理器
            db_manager = DatabaseManager()
            if not db_manager.initialize(config_manager.get_database_config()):
                raise RuntimeError("初始化数据库失败")

            # 正常启动时只检查并创建缺失的表
            db_manager.init_db(force_recreate=False)
            
            # 初始化认证管理器
            auth_manager = AuthManager(db_manager)
            
            # 初始化应用上下文
            init_app_context(db_manager, config_manager, auth_manager)

        # 显示登录窗口
        login_window = LoginWindow(auth_manager, config_manager, db_manager)
        login_window.show()

        # 运行应用
        return app.exec()

    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        show_error_dialog("错误", f"程序启动失败: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
