from PySide6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox,
                             QMessageBox, QGroupBox, QFormLayout, QFileDialog,
                             QSpinBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.ui.managers.style import StyleManager
from src.ui.utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from src.utils.error_handler import ErrorHandler
from src.core.database import DatabaseManager
from src.core.config_manager import ConfigManager
from src.core.auth_manager import AuthManager
from src.models.settings import Settings
from src.models.user import User, UserRole
import os
import json
import traceback

logger = get_logger(__name__)

class InitWizard(QWizard):
    """初始化向导"""
    
    def __init__(self, db_manager: DatabaseManager, config_manager: ConfigManager, auth_manager: AuthManager, parent=None):
        try:
            super().__init__(parent)
            self.db_manager = db_manager
            self.config_manager = config_manager
            self.auth_manager = auth_manager
            
            # 初始化路径配置
            self.config_path = None
            self.db_path = None
            self.log_path = None
            self.backup_path = None
            
            # 初始化数据库配置
            self.db_filename = None  # 新增数据库文件名
            self.db_pool_size = None
            self.db_timeout = None
            
            # 初始化管理员配置
            self.admin_password = None
            self.admin_confirm = None
            
            # 初始化企业配置
            self.corp_name = None
            self.corp_id = None
            self.corp_secret = None
            self.agent_id = None
            
            # 初始化日志配置
            self.log_level = None
            self.log_retention = None
            
            self.init_ui()
            
        except Exception as e:
            logger.error(f"初始化向导创建失败: {str(e)}\n{traceback.format_exc()}")
            raise
        
    def init_ui(self):
        """初始化UI"""
        try:
            self.setWindowTitle("系统初始化向导")
            self.setModal(True)
            self.setWizardStyle(QWizard.ModernStyle)
            
            # 添加页面
            self.addPage(self.create_paths_page())
            self.addPage(self.create_database_page())
            self.addPage(self.create_admin_page())
            self.addPage(self.create_corp_page())
            self.addPage(self.create_corp_admin_page())  # 新增企业管理员配置页面
            
            logger.info("初始化向导UI创建成功")
            
        except Exception as e:
            logger.error(f"初始化UI失败: {str(e)}")
            raise
            
    def create_paths_page(self) -> QWizardPage:
        """创建路径设置页面"""
        page = QWizardPage()
        page.setTitle("路径设置")
        page.setSubTitle("请设置系统所需的目录路径")
        
        layout = QFormLayout()
        
        # 配置目录
        config_layout = QHBoxLayout()
        self.config_path = QLineEdit()
        self.config_path.setReadOnly(True)
        self.config_path.setText(self.config_manager.config_dir)
        config_browse = QPushButton("浏览")
        config_browse.clicked.connect(lambda: self.browse_path(self.config_path, "选择配置目录"))
        config_layout.addWidget(self.config_path)
        config_layout.addWidget(config_browse)
        layout.addRow("配置目录:", config_layout)
        
        # 数据目录
        data_layout = QHBoxLayout()
        self.data_path = QLineEdit()
        self.data_path.setText(os.path.join(self.config_manager.config_dir, "data"))
        data_browse = QPushButton("浏览")
        data_browse.clicked.connect(lambda: self.browse_path(self.data_path, "选择数据目录"))
        data_layout.addWidget(self.data_path)
        data_layout.addWidget(data_browse)
        layout.addRow("数据目录:", data_layout)
        
        # 日志目录
        log_layout = QHBoxLayout()
        self.log_path = QLineEdit()
        self.log_path.setText(os.path.join(os.path.expanduser("~"), ".wecom_live_sign", "logs"))
        log_browse = QPushButton("浏览")
        log_browse.clicked.connect(lambda: self.browse_path(self.log_path, "选择日志目录"))
        log_layout.addWidget(self.log_path)
        log_layout.addWidget(log_browse)
        layout.addRow("日志目录:", log_layout)
        
        # 备份目录
        backup_layout = QHBoxLayout()
        self.backup_path = QLineEdit()
        self.backup_path.setText(os.path.join(self.config_manager.config_dir, "backups"))
        backup_browse = QPushButton("浏览")
        backup_browse.clicked.connect(lambda: self.browse_path(self.backup_path, "选择备份目录"))
        backup_layout.addWidget(self.backup_path)
        backup_layout.addWidget(backup_browse)
        layout.addRow("备份目录:", backup_layout)
        
        page.setLayout(layout)
        return page
        
    def create_database_page(self) -> QWizardPage:
        """创建数据库配置页面"""
        page = QWizardPage()
        page.setTitle("数据库配置")
        page.setSubTitle("配置数据库连接参数")
        
        layout = QVBoxLayout(page)
        form_group = QGroupBox("数据库参数")
        form_layout = QFormLayout()
        
        # 数据库文件名
        self.db_filename = QLineEdit()
        self.db_filename.setText("data.db")
        form_layout.addRow("数据库文件名:", self.db_filename)
        
        # 连接池大小
        self.db_pool_size = QSpinBox()
        self.db_pool_size.setRange(1, 20)
        self.db_pool_size.setValue(5)
        self.db_pool_size.setSuffix(" 个连接")
        form_layout.addRow("连接池大小:", self.db_pool_size)
        
        # 连接超时
        self.db_timeout = QSpinBox()
        self.db_timeout.setRange(5, 300)
        self.db_timeout.setValue(30)
        self.db_timeout.setSuffix(" 秒")
        form_layout.addRow("连接超时:", self.db_timeout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 添加说明文本
        note_label = QLabel(
            "说明：\n"
            "1. 数据库文件名：SQLite数据库文件的名称，默认为data.db\n"
            "2. 连接池大小：同时可以维持的数据库连接数量\n"
            "3. 连接超时：数据库连接的最大等待时间\n"
            "如果不确定，建议使用默认值。"
        )
        note_label.setStyleSheet("color: gray;")
        layout.addWidget(note_label)
        
        return page
        
    def create_admin_page(self) -> QWizardPage:
        """创建管理员配置页面"""
        page = QWizardPage()
        page.setTitle("管理员配置")
        page.setSubTitle("设置超级管理员账号")
        
        layout = QVBoxLayout(page)
        form_group = QGroupBox("管理员账号")
        form_layout = QFormLayout()
        
        # 用户名（固定为root-admin）
        username_label = QLabel("root-admin")
        username_label.setStyleSheet("color: gray;")
        form_layout.addRow("用户名:", username_label)
        
        # 密码
        self.admin_password = QLineEdit()
        self.admin_password.setEchoMode(QLineEdit.Password)
        form_layout.addRow("密码:", self.admin_password)
        
        # 确认密码
        self.admin_confirm = QLineEdit()
        self.admin_confirm.setEchoMode(QLineEdit.Password)
        form_layout.addRow("确认密码:", self.admin_confirm)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 添加说明文本
        note_label = QLabel(
            "说明：\n"
            "1. 超级管理员用户名固定为 root-admin\n"
            "2. 密码长度至少8位，必须包含大小写字母、数字和特殊字符\n"
            "3. 请务必牢记密码，忘记密码将无法管理系统"
        )
        note_label.setStyleSheet("color: gray;")
        layout.addWidget(note_label)
        
        return page
        
    def create_corp_page(self) -> QWizardPage:
        """创建企业配置页面"""
        page = QWizardPage()
        page.setTitle("企业信息配置")
        page.setSubTitle("配置企业微信相关信息")
        
        layout = QVBoxLayout(page)
        form_group = QGroupBox("企业信息")
        form_layout = QFormLayout()
        
        # 企业名称
        self.corp_name = QLineEdit()
        form_layout.addRow("企业名称:", self.corp_name)
        
        # 企业ID
        self.corp_id = QLineEdit()
        form_layout.addRow("企业ID:", self.corp_id)
        
        # 应用Secret
        self.corp_secret = QLineEdit()
        self.corp_secret.setEchoMode(QLineEdit.Password)
        form_layout.addRow("应用Secret:", self.corp_secret)
        
        # 应用ID
        self.agent_id = QLineEdit()
        form_layout.addRow("应用ID:", self.agent_id)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 添加说明文本
        note_label = QLabel(
            "说明：\n"
            "1. 以上信息可以在企业微信管理后台获取\n"
            "2. 请确保填写的信息准确，否则可能导致系统无法正常工作\n"
            "3. Secret和应用ID属于敏感信息，请妥善保管"
        )
        note_label.setStyleSheet("color: gray;")
        layout.addWidget(note_label)
        
        return page
        
    def create_corp_admin_page(self) -> QWizardPage:
        """创建企业管理员配置页面"""
        page = QWizardPage()
        page.setTitle("企业管理员配置")
        page.setSubTitle("设置企业管理员账号")
        
        layout = QVBoxLayout(page)
        form_group = QGroupBox("企业管理员账号")
        form_layout = QFormLayout()
        
        # 用户名
        self.corp_admin_username = QLineEdit()
        form_layout.addRow("用户名:", self.corp_admin_username)
        
        # 密码
        self.corp_admin_password = QLineEdit()
        self.corp_admin_password.setEchoMode(QLineEdit.Password)
        form_layout.addRow("密码:", self.corp_admin_password)
        
        # 确认密码
        self.corp_admin_confirm = QLineEdit()
        self.corp_admin_confirm.setEchoMode(QLineEdit.Password)
        form_layout.addRow("确认密码:", self.corp_admin_confirm)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 添加说明文本
        note_label = QLabel(
            "说明：\n"
            "1. 企业管理员将负责管理该企业的直播和签到信息\n"
            "2. 密码长度至少8位，必须包含大小写字母、数字和特殊字符\n"
            "3. 请妥善保管密码"
        )
        note_label.setStyleSheet("color: gray;")
        layout.addWidget(note_label)
        
        return page
        
    def create_finish_page(self) -> QWizardPage:
        """创建完成页面"""
        page = QWizardPage()
        page.setTitle("完成配置")
        page.setSubTitle("系统初始化配置已完成")
        
        layout = QVBoxLayout(page)
        
        # 完成提示
        finish_text = """
        恭喜！系统初始化配置已完成。
        
        接下来系统将：
        1. 创建必要的目录结构
        2. 初始化数据库
        3. 创建超级管理员账号
        4. 保存企业配置信息
        
        点击"完成"按钮开始执行以上操作。
        操作完成后，您可以使用配置的管理员账号登录系统。
        """
        
        label = QLabel(finish_text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        return page
        
    def browse_path(self, line_edit: QLineEdit, title: str):
        """浏览文件夹"""
        path = QFileDialog.getExistingDirectory(
            self,
            title,
            line_edit.text() or os.path.expanduser("~")
        )
        if path:
            line_edit.setText(path)
            
    def validateCurrentPage(self) -> bool:
        """验证当前页面"""
        try:
            current_page = self.currentPage()
            
            # 验证路径配置页面
            if current_page == self.page(0):
                return self.validate_paths_page()
                
            # 验证数据库配置页面
            elif current_page == self.page(1):
                return self.validate_database_page()
                
            # 验证管理员配置页面
            elif current_page == self.page(2):
                return self.validate_admin_page()
                
            # 验证企业配置页面
            elif current_page == self.page(3):
                return self.validate_corp_page()
                
            # 验证企业管理员配置页面
            elif current_page == self.page(4):
                # 如果是点击完成按钮，需要验证所有页面
                if self.nextId() == -1:  # -1表示这是最后一页
                    if not self.validate_paths_page():
                        self.setCurrentIndex(0)  # 返回到第一页
                        return False
                    if not self.validate_database_page():
                        self.setCurrentIndex(1)
                        return False
                    if not self.validate_admin_page():
                        self.setCurrentIndex(2)
                        return False
                    if not self.validate_corp_page():
                        self.setCurrentIndex(3)
                        return False
                    if not self.validate_corp_admin_page():
                        return False
                return self.validate_corp_admin_page()
                
            return True
            
        except Exception as e:
            logger.error(f"验证页面失败: {str(e)}\n{traceback.format_exc()}")
            ErrorHandler.handle_error(str(e), self)
            return False
            
    def validate_paths_page(self) -> bool:
        """验证路径配置页面"""
        # 检查是否填写了所有路径
        if not all([
            self.config_path.text(),
            self.data_path.text(),
            self.log_path.text(),
            self.backup_path.text()
        ]):
            ErrorHandler.handle_error("请填写所有路径", self)
            return False
            
        # 检查路径是否有效
        try:
            for path in [
                self.config_path.text(),
                self.data_path.text(),
                self.log_path.text(),
                self.backup_path.text()
            ]:
                # 检查路径是否是绝对路径
                if not os.path.isabs(path):
                    ErrorHandler.handle_error(f"路径必须是绝对路径: {path}", self)
                    return False
                    
                # 检查父目录是否存在且有写权限
                parent_dir = os.path.dirname(path)
                if os.path.exists(parent_dir):
                    if not os.access(parent_dir, os.W_OK):
                        ErrorHandler.handle_error(f"没有写入权限: {parent_dir}", self)
                        return False
                else:
                    # 如果父目录不存在，递归检查上级目录的权限
                    current_dir = parent_dir
                    while not os.path.exists(current_dir):
                        current_dir = os.path.dirname(current_dir)
                    if not os.access(current_dir, os.W_OK):
                        ErrorHandler.handle_error(f"没有写入权限: {current_dir}", self)
                        return False
                        
        except Exception as e:
            ErrorHandler.handle_error(f"路径验证失败: {str(e)}", self)
            return False
            
        return True
        
    def validate_database_page(self) -> bool:
        """验证数据库配置页面"""
        # 检查数据库文件名
        if not self.db_filename.text():
            ErrorHandler.handle_error("请输入数据库文件名", self)
            return False
            
        if not self.db_filename.text().endswith('.db'):
            ErrorHandler.handle_error("数据库文件名必须以.db结尾", self)
            return False
            
        # 检查文件名是否包含非法字符
        invalid_chars = '<>:"/\\|?*'
        if any(c in self.db_filename.text() for c in invalid_chars):
            ErrorHandler.handle_error(f"数据库文件名不能包含以下字符: {invalid_chars}", self)
            return False
            
        # 检查连接池大小
        if self.db_pool_size.value() < 1:
            ErrorHandler.handle_error("连接池大小必须大于0", self)
            return False
            
        # 检查超时时间
        if self.db_timeout.value() < 5:
            ErrorHandler.handle_error("连接超时时间必须大于5秒", self)
            return False
            
        return True
        
    def validate_admin_page(self) -> bool:
        """验证管理员配置页面"""
        # 检查密码是否填写
        if not self.admin_password.text():
            ErrorHandler.handle_error("请输入管理员密码", self)
            return False
            
        # 检查确认密码是否填写
        if not self.admin_confirm.text():
            ErrorHandler.handle_error("请确认管理员密码", self)
            return False
            
        # 检查密码是否一致
        if self.admin_password.text() != self.admin_confirm.text():
            ErrorHandler.handle_error("两次输入的密码不一致", self)
            return False
            
        # 检查密码强度
        password = self.admin_password.text()
        
        # 检查密码长度
        if len(password) < 8:
            ErrorHandler.handle_error("密码长度必须不少于8位", self)
            return False
            
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not has_upper:
            ErrorHandler.handle_error("密码必须包含大写字母", self)
            return False
            
        if not has_lower:
            ErrorHandler.handle_error("密码必须包含小写字母", self)
            return False
            
        if not has_digit:
            ErrorHandler.handle_error("密码必须包含数字", self)
            return False
            
        if not has_special:
            ErrorHandler.handle_error("密码必须包含特殊字符", self)
            return False
            
        # 检查密码中是否包含用户名
        if "root-admin" in password.lower():
            ErrorHandler.handle_error("密码不能包含用户名", self)
            return False
            
        # 检查密码中是否包含连续字符
        for i in range(len(password) - 2):
            if (ord(password[i+1]) - ord(password[i]) == 1 and 
                ord(password[i+2]) - ord(password[i+1]) == 1):
                ErrorHandler.handle_error("密码不能包含连续字符", self)
                return False
                
        # 检查密码中是否包含重复字符
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                ErrorHandler.handle_error("密码不能包含重复字符", self)
                return False
                
        return True
        
    def validate_corp_page(self) -> bool:
        """验证企业配置页面"""
        # 检查是否填写了所有字段
        if not all([
            self.corp_name.text(),
            self.corp_id.text(),
            self.corp_secret.text(),
            self.agent_id.text()
        ]):
            ErrorHandler.handle_error("请填写所有企业信息", self)
            return False
            
        return True
        
    def validate_corp_admin_page(self) -> bool:
        """验证企业管理员配置页面"""
        # 检查用户名是否填写
        if not self.corp_admin_username.text():
            ErrorHandler.handle_error("请输入企业管理员用户名", self)
            return False
            
        # 检查密码是否填写
        if not self.corp_admin_password.text():
            ErrorHandler.handle_error("请输入企业管理员密码", self)
            return False
            
        # 检查确认密码是否填写
        if not self.corp_admin_confirm.text():
            ErrorHandler.handle_error("请确认企业管理员密码", self)
            return False
            
        # 检查密码是否一致
        if self.corp_admin_password.text() != self.corp_admin_confirm.text():
            ErrorHandler.handle_error("两次输入的密码不一致", self)
            return False
            
        # 检查密码强度
        password = self.corp_admin_password.text()
        
        # 检查密码长度
        if len(password) < 8:
            ErrorHandler.handle_error("密码长度必须不少于8位", self)
            return False
            
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not has_upper:
            ErrorHandler.handle_error("密码必须包含大写字母", self)
            return False
            
        if not has_lower:
            ErrorHandler.handle_error("密码必须包含小写字母", self)
            return False
            
        if not has_digit:
            ErrorHandler.handle_error("密码必须包含数字", self)
            return False
            
        if not has_special:
            ErrorHandler.handle_error("密码必须包含特殊字符", self)
            return False
            
        # 检查密码中是否包含用户名
        if self.corp_admin_username.text().lower() in password.lower():
            ErrorHandler.handle_error("密码不能包含用户名", self)
            return False
            
        # 检查密码中是否包含连续字符
        for i in range(len(password) - 2):
            if (ord(password[i+1]) - ord(password[i]) == 1 and 
                ord(password[i+2]) - ord(password[i+1]) == 1):
                ErrorHandler.handle_error("密码不能包含连续字符", self)
                return False
                
        # 检查密码中是否包含重复字符
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                ErrorHandler.handle_error("密码不能包含重复字符", self)
                return False
                
        return True
        
    def accept(self):
        """完成配置"""
        try:
            # 在执行配置之前再次验证所有页面
            if not self.validateCurrentPage():
                return
                
            logger.info("开始执行初始化配置...")
            
            # 1. 更新默认配置文件中的路径信息
            default_config_dir = os.path.join(os.path.expanduser("~"), ".wecom_live_sign")
            default_config_file = os.path.join(default_config_dir, "config.json")
            
            # 确保默认配置目录存在
            os.makedirs(default_config_dir, exist_ok=True)
            
            default_config = {
                "initialized": True,
                "paths": {
                    "config": self.config_path.text(),
                    "data": self.data_path.text(),
                    "log": self.log_path.text(),
                    "backup": self.backup_path.text()
                }
            }
            
            try:
                with open(default_config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logger.error(f"更新默认配置文件失败: {str(e)}")
                raise RuntimeError("更新默认配置文件失败")
            
            # 2. 创建必要的目录结构
            logger.info("创建目录结构...")
            for path in [
                self.config_path.text(),
                self.data_path.text(),
                self.log_path.text(),
                self.backup_path.text()
            ]:
                os.makedirs(path, exist_ok=True)
            
            # 3. 初始化配置管理器
            logger.info("初始化配置管理器...")
            system_config = {
                "system": {
                    "initialized": True,
                    "config_path": self.config_path.text(),
                    "data_path": self.data_path.text(),
                    "log_path": self.log_path.text(),
                    "backup_path": self.backup_path.text(),
                    "log_level": "INFO",
                    "log_retention": 30,
                    "backup_retention": 30
                },
                "paths": {
                    "config": self.config_path.text(),
                    "data": self.data_path.text(),
                    "log": self.log_path.text(),
                    "backup": self.backup_path.text()
                },
                "database": {
                    "type": "sqlite",
                    "path": os.path.join(self.data_path.text(), self.db_filename.text()),
                    "backup_path": self.backup_path.text(),
                    "pool_size": self.db_pool_size.value(),
                    "timeout": self.db_timeout.value(),
                    "echo": True,  # 开启SQL日志以便调试
                    "pool_recycle": 3600,
                    "pool_pre_ping": True
                },
                "corporations": [{
                    "corpid": self.corp_id.text(),
                    "name": self.corp_name.text(),
                    "corpsecret": self.corp_secret.text(),
                    "agentid": self.agent_id.text(),
                    "status": True,
                    "admin": {
                        "username": self.corp_admin_username.text(),
                        "role": "corp_admin"
                    }
                }]
            }
            
            # 先设置配置目录
            self.config_manager.config_dir = self.config_path.text()
            
            # 然后初始化配置管理器
            if not self.config_manager.initialize(self.config_path.text(), system_config):
                raise RuntimeError("初始化配置管理器失败")
            
            # 4. 初始化数据库
            logger.info("初始化数据库...")
            
            # 判断是否是首次初始化
            if not self.config_manager.config or not self.config_manager.config.get("system", {}).get("initialized", False):
                # 首次初始化，使用向导中的配置
                db_config = {
                    "type": "sqlite",
                    "path": os.path.join(self.data_path.text(), self.db_filename.text()),
                    "backup_path": self.backup_path.text(),
                    "pool_size": self.db_pool_size.value(),
                    "timeout": self.db_timeout.value(),
                    "echo": True,  # 开启SQL日志以便调试
                    "pool_recycle": 3600,
                    "pool_pre_ping": True
                }
            else:
                # 非首次初始化，从配置管理器获取数据库配置
                db_config = self.config_manager.get_database_config()
            
            # 确保数据库目录存在
            os.makedirs(os.path.dirname(db_config["path"]), exist_ok=True)
            
            if not self.db_manager.initialize(db_config):
                raise RuntimeError("初始化数据库失败")
            
            # 创建数据库表
            logger.info("创建数据库表...")
            if not self.db_manager.create_tables():
                raise RuntimeError("创建数据库表失败")
                
            # 初始化数据库，创建root-admin用户
            logger.info("初始化数据库，创建root-admin用户...")
            self.db_manager.init_db(force_recreate=False)
            
            # 设置超级管理员密码
            logger.info("设置超级管理员密码...")
            if not self.auth_manager.set_root_admin_password(self.admin_password.text()):
                raise RuntimeError("设置超级管理员密码失败")
            
            # 创建企业管理员账号
            logger.info("创建企业管理员账号...")
            if not self.auth_manager.create_corp_admin(
                username=self.corp_admin_username.text(),
                password=self.corp_admin_password.text(),
                corp_name=self.corp_name.text()
            ):
                raise RuntimeError("创建企业管理员账号失败")
            
            # 7. 显示成功消息
            success_text = (
                "系统初始化配置已完成！\n\n"
                "配置信息：\n"
                f"- 配置文件：{os.path.join(self.config_path.text(), 'config.json')}\n"
                f"- 数据库文件：{os.path.join(self.data_path.text(), self.db_filename.text())}\n"
                f"- 日志目录：{self.log_path.text()}\n"
                f"- 备份目录：{self.backup_path.text()}\n\n"
                "企业信息：\n"
                f"- 企业名称：{self.corp_name.text()}\n"
                f"- 企业ID：{self.corp_id.text()}\n"
                f"- 应用ID：{self.agent_id.text()}\n\n"
                "账号信息：\n"
                "1. 超级管理员账号：\n"
                "- 用户名：root-admin\n"
                "- 密码：您设置的密码\n\n"
                "2. 企业管理员账号：\n"
                f"- 用户名：{self.corp_admin_username.text()}\n"
                f"- 密码：您设置的密码\n\n"
                "请妥善保管以上信息！"
            )
            
            QMessageBox.information(
                self,
                "初始化完成",
                success_text
            )
            
            logger.info("系统初始化配置完成")
            super().accept()
            
        except Exception as e:
            logger.error(f"初始化配置失败: {str(e)}\n{traceback.format_exc()}")
            ErrorHandler.handle_error(f"初始化配置失败: {str(e)}", self)