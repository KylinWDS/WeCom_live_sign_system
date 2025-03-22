# PySide6导入
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox,
                             QToolButton, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QClipboard
from PySide6.QtWidgets import QApplication

# UI相关导入
from ..managers.style import StyleManager
from ..managers.theme_manager import ThemeManager
from ..utils.widget_utils import WidgetUtils
from ..managers.animation import AnimationManager
from .main_window import MainWindow

# 核心功能导入
from ...core.config_manager import ConfigManager
from ...core.database import DatabaseManager
from ...core.auth_manager import AuthManager

# 工具类导入
from ...utils.logger import get_logger
from ...utils.network import NetworkUtils

# 模型导入
from ...models.corporation import Corporation
from ...models.user import User

logger = get_logger(__name__)

class LoginWindow(QMainWindow):
    """登录窗口"""
    
    def __init__(self, auth_manager: AuthManager, config_manager: ConfigManager, db_manager: DatabaseManager):
        super().__init__()
        self.auth_manager = auth_manager
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.main_window = None
        
        # 初始化主题管理器
        self.theme_manager = ThemeManager()
        
        self.init_ui()
        
        # 应用主题设置
        self._apply_theme()
        
        # 获取并显示IP
        self.update_ip_info()
    
    def update_ip_info(self):
        """更新IP信息"""
        try:
            ip = NetworkUtils.get_public_ip()
            if ip:
                self.ip_label.setText(f"当前IP: {ip}")
                self.copy_ip_btn.setEnabled(True)
                
                # 记录IP到数据库
                from src.core.ip_record_manager import IPRecordManager
                with self.db_manager.get_session() as session:
                    ip_record_manager = IPRecordManager(session)
                    ip_record_manager.add_ip(ip, 'manual')
            else:
                self.ip_label.setText("无法获取IP地址")
                self.copy_ip_btn.setEnabled(False)
        except Exception as e:
            logger.error(f"获取IP地址失败: {str(e)}")
            self.ip_label.setText("获取IP地址失败")
            self.copy_ip_btn.setEnabled(False)
    
    def copy_ip(self):
        """复制IP地址"""
        try:
            ip = NetworkUtils.get_public_ip()
            if ip:
                clipboard = QApplication.clipboard()
                clipboard.setText(ip)
                QMessageBox.information(self, "提示", "IP地址已复制到剪贴板")
            else:
                QMessageBox.warning(self, "警告", "无法获取IP地址")
        except Exception as e:
            logger.error(f"复制IP地址失败: {str(e)}")
            QMessageBox.warning(self, "错误", "复制IP地址失败")
    
    def _apply_theme(self):
        """应用主题设置"""
        try:
            # 从配置获取主题设置
            theme = self.config_manager.get_theme()
            
            # 应用主题
            self.theme_manager.apply_theme(theme)
            
        except Exception as e:
            logger.error(f"应用主题失败: {str(e)}")
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("企业微信直播签到系统")
        self.setFixedSize(400, 500)
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel("企业微信直播签到系统")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(title_label)
        
        # IP信息
        ip_layout = QHBoxLayout()
        ip_layout.setSpacing(5)
        self.ip_label = QLabel("正在获取IP地址...")
        self.ip_label.setStyleSheet("color: #666666;")
        ip_layout.addWidget(self.ip_label)
        
        # 添加复制链接
        self.copy_ip_btn = QLabel("复制")
        self.copy_ip_btn.setStyleSheet("""
            QLabel {
                color: #1890ff;
                cursor: pointer;
                padding: 0 5px;
            }
            QLabel:hover {
                color: #40a9ff;
                text-decoration: underline;
            }
        """)
        self.copy_ip_btn.mousePressEvent = lambda e: self.copy_ip()
        ip_layout.addWidget(self.copy_ip_btn)
        
        # 添加警告图标和提示
        warning_label = QLabel("⚠️")
        warning_label.setStyleSheet("color: #faad14;")
        warning_label.setToolTip("点击查看IP配置说明")
        warning_label.mousePressEvent = lambda e: self.show_ip_config_tip()
        ip_layout.addWidget(warning_label)
        
        layout.addLayout(ip_layout)
        
        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # 用户名
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.textChanged.connect(self.on_username_changed)
        form_layout.addRow("用户名:", self.username_edit)
        
        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.returnPressed.connect(self.on_login)  # 添加回车键事件处理
        form_layout.addRow("密码:", self.password_edit)
        
        # 企业选择
        self.corp_combo = QComboBox()
        self.corp_combo.setEditable(True)
        self.corp_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.corp_combo.currentTextChanged.connect(self.on_corp_changed)
        form_layout.addRow("企业名称:", self.corp_combo)
        
        layout.addLayout(form_layout)
        
        # 企业信息
        self.corp_info = QLabel()
        self.corp_info.setWordWrap(True)
        self.corp_info.setStyleSheet("color: #666666; font-size: 12px; margin-top: 5px;")
        layout.addWidget(self.corp_info)
        
        # 登录按钮
        self.login_btn = QPushButton("登录")
        self.login_btn.setFixedWidth(200)
        self.login_btn.clicked.connect(self.on_login)
        login_btn_layout = QHBoxLayout()
        login_btn_layout.addStretch()
        login_btn_layout.addWidget(self.login_btn)
        login_btn_layout.addStretch()
        layout.addLayout(login_btn_layout)
        
        # 免责声明
        disclaimer = QLabel(
            "免责声明：本软件仅供个人测试使用，请勿用于商业用途。"
            "使用本软件即表示您同意遵守相关法律法规。"
        )
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet("color: #999999; font-size: 12px; margin-top: 10px;")
        layout.addWidget(disclaimer)
        
        # 设置样式
        self.setStyleSheet(StyleManager.get_login_style())
        
        # 加载企业列表
        self.load_corp_list()
    
    def load_corp_list(self):
        """加载企业列表"""
        try:
            # 先从数据库获取企业列表
            with self.db_manager.get_session() as session:
                corporations = session.query(Corporation).filter_by(status=True).all()
                # 在会话关闭前获取所有需要的数据
                corp_data = []
                for corp in corporations:
                    corp_data.append({
                        'name': corp.name,
                        'corp_id': corp.corp_id,
                        'agent_id': corp.agent_id,
                        'status': corp.status
                    })
                
            if corp_data:
                # 如果数据库中有企业信息，使用数据库中的信息
                self.corp_combo.clear()
                for corp in corp_data:
                    self.corp_combo.addItem(corp['name'])
                
                # 显示第一个企业的信息
                if corp_data:
                    self.on_corp_changed(corp_data[0]['name'])
            else:
                # 如果数据库中没有企业信息，从配置文件获取
                corporations = self.config_manager.get_corporations()
                self.corp_combo.clear()
                for corp in corporations:
                    self.corp_combo.addItem(corp["name"])
                
                # 如果有企业，显示第一个企业的信息
                if corporations:
                    self.on_corp_changed(corporations[0]["name"])
                    
        except Exception as e:
            logger.error(f"加载企业列表失败: {str(e)}")
            QMessageBox.warning(self, "警告", "加载企业列表失败")
    
    def on_username_changed(self, text: str):
        """用户名输入变化事件"""
        # 如果是root-admin，禁用企业选择
        if text.strip().lower() == "root-admin":
            self.corp_combo.setEnabled(False)
            self.corp_combo.setCurrentText("")
            self.corp_info.setText("超级管理员无需选择企业")
        else:
            self.corp_combo.setEnabled(True)
            # 恢复企业信息显示
            corp_name = self.corp_combo.currentText()
            if corp_name:
                self.on_corp_changed(corp_name)
    
    def on_corp_changed(self, corpname: str):
        """企业选择改变"""
        try:
            # 如果是root-admin，不显示企业信息
            if self.username_edit.text().strip().lower() == "root-admin":
                self.corp_info.setText("超级管理员无需选择企业")
                return
                
            # 先从数据库获取企业信息
            with self.db_manager.get_session() as session:
                corp = session.query(Corporation).filter_by(name=corpname).first()
                if corp:
                    # 在会话关闭前获取所有需要的数据
                    corp_info = {
                        'name': corp.name,
                        'corp_id': corp.corp_id,
                        'agent_id': corp.agent_id,
                        'status': corp.status
                    }
                    # 使用获取到的数据更新显示
                    # info_text = f"企业ID: {corp_info['corp_id']}\n"
                    # info_text += f"应用ID: {corp_info['agent_id']}\n"
                    # info_text += f"状态: {'启用' if corp_info['status'] else '禁用'}"
                    # self.corp_info.setText(info_text)
                    self.corp_info.setText("企业信息已加载")
                else:
                    # 如果数据库中没有企业信息，从配置文件获取
                    corp = self.config_manager.get_corporation(corpname)
                    if corp:
                        # info_text = f"企业ID: {corp['corpid']}\n"
                        # info_text += f"应用ID: {corp['agentid']}\n"
                        # info_text += f"状态: {'启用' if corp['status'] else '禁用'}"
                        # self.corp_info.setText(info_text)
                        self.corp_info.setText("企业信息已加载")
                    else:
                        self.corp_info.setText("")
        except Exception as e:
            logger.error(f"更新企业信息失败: {str(e)}")
            self.corp_info.setText("")
    
    def on_login(self):
        """登录按钮点击"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "警告", "请输入用户名和密码")
            return
        
        # 如果是root-admin，不需要验证企业
        if username.lower() == "root-admin":
            corpname = None
        else:
            corpname = self.corp_combo.currentText().strip()
            if not corpname:
                QMessageBox.warning(self, "警告", "请选择或输入企业名称")
                return
        
        try:
            success, message = self.auth_manager.login(username, password, corpname)
            if success:
                logger.info(f"用户 {username} 登录成功")
                # 获取完整的用户信息并在新的会话中使用
                session = self.db_manager.Session()
                try:
                    user = session.query(User).filter_by(login_name=username).first()
                    if user:
                        # 创建主窗口并保持会话
                        self.main_window = MainWindow(
                            user,  # 传递完整的用户对象
                            self.config_manager,
                            self.db_manager,
                            self.auth_manager
                        )
                        # 将会话保存到主窗口中
                        self.main_window.db_session = session
                        self.main_window.show()
                        self.close()
                    else:
                        session.close()
                        QMessageBox.warning(self, "错误", "获取用户信息失败")
                except Exception as e:
                    session.close()
                    raise e
            else:
                QMessageBox.warning(self, "错误", message)
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            QMessageBox.critical(self, "错误", "登录失败，请稍后重试")
    
    def show_ip_config_tip(self):
        """显示IP配置提示弹窗"""
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QDialog, QApplication, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QScrollArea
        
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        window_width = int(screen_size.width() * 0.4)  # 屏幕宽度的40%
        window_height = int(screen_size.height() * 0.67)  # 屏幕高度的2/3
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("IP配置说明")
        dialog.setFixedSize(window_width, window_height)
        dialog.setModal(True)  # 设置为模态对话框
        
        # 创建主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(0, 0, 10, 0)  # 右边留出滚动条的空间
        
        # 创建说明文本标签
        text_label = QLabel()
        text_label.setOpenExternalLinks(True)
        text_label.setTextFormat(Qt.TextFormat.RichText)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                line-height: 1.6;
                color: #333333;
            }
        """)
        
        # 设置文本内容
        text_label.setText("""
            <div style='margin-bottom: 20px;'>
                <h3 style='margin: 0 0 15px 0; color: #1890ff;'>IP白名单配置说明</h3>
                
                <p style='margin: 0 0 15px 0;'>请按照以下步骤在企业微信后台配置IP白名单：</p>
                
                <ol style='margin: 0 0 15px 20px; padding: 0;'>
                    <li style='margin-bottom: 10px;'>登录企业微信管理后台</li>
                    <li style='margin-bottom: 10px;'>进入【应用管理】-&gt;【应用】-&gt;【直播签到】</li>
                    <li style='margin-bottom: 10px;'>在"企业可信IP"中配置IP白名单</li>
                    <li style='margin-bottom: 10px;'>添加以下IP地址到白名单中</li>
                </ol>
                
                <p style='color: #ff4d4f; font-weight: bold; margin: 15px 0; padding: 10px; background-color: #fff1f0; border: 1px solid #ffccc7; border-radius: 4px;'>
                    注意：请在完成IP配置后等待5分钟再进行登录，未配置或未生效的IP白名单会导致接口调用失败
                </p>
                
                <p style='margin: 15px 0;'>
                    <a href='https://work.weixin.qq.com/wework_admin/frame#apps/modApiApp' 
                       style='color: #1890ff; text-decoration: none; font-size: 14px; display: inline-block; margin-top: 10px;'>
                        点击此处打开企业微信后台配置页面 &gt;
                    </a>
                </p>
            </div>
        """)
        
        content_layout.addWidget(text_label)
        
        # 获取IP列表
        current_ip = NetworkUtils.get_public_ip()
        from src.core.ip_record_manager import IPRecordManager
        from src.utils.ip_suggestion import IPSuggestion
        from src.models.ip_record import IPRecord
        
        with self.db_manager.get_session() as session:
            ip_record_manager = IPRecordManager(session)
            ip_suggestion = IPSuggestion(ip_record_manager)
            
            # 使用优化后的方法获取IP列表，传入当前session
            ip_list = ip_suggestion.generate_and_save_ips(100, session)
            
            # 如果当前IP存在且不在数据库中，添加为manual类型
            if current_ip:
                existing_ip = session.query(IPRecord).filter_by(
                    ip=current_ip
                ).first()
                if not existing_ip:
                    ip_record_manager.add_ip(current_ip, 'manual')
                    if current_ip not in ip_list:
                        ip_list.insert(0, current_ip)  # 确保当前IP在列表开头
            
            session.commit()  # 提交所有更改
        
        # 创建IP列表标签
        ip_list_label = QLabel("建议添加的IP地址列表：")
        ip_list_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333333;
                margin-top: 10px;
            }
        """)
        content_layout.addWidget(ip_list_label)
        
        # 创建IP显示区域
        ip_display = QLabel()
        ip_display.setWordWrap(True)
        ip_display.setStyleSheet("""
            QLabel {
                background-color: #fafafa;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 15px;
                margin-top: 5px;
                font-family: monospace;
                font-size: 13px;
                line-height: 1.8;
                color: #333333;
            }
        """)
        
        # 构建IP显示文本，每行显示5个IP，用分号分隔
        ip_text = ""
        for i in range(0, len(ip_list), 5):
            line_ips = ip_list[i:i+5]
            ip_text += "; ".join(line_ips)
            if i + 5 < len(ip_list):
                ip_text += ";\n"
        
        # 添加IP数量统计
        ip_count = len(ip_list)
        ip_text = f"共 {ip_count} 个IP地址：\n\n" + ip_text
        
        ip_display.setText(ip_text)
        content_layout.addWidget(ip_display)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        # 复制按钮
        copy_btn = QPushButton("复制IP列表")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
        """)
        copy_btn.clicked.connect(lambda: self.copy_ip_list(ip_list))
        button_layout.addWidget(copy_btn)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #666666;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #40a9ff;
                color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #e6f7ff;
            }
        """)
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        # 设置窗口标志
        dialog.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowTitleHint
        )
        
        # 显示对话框
        dialog.exec()
    
    def copy_ip_list(self, ip_list):
        """复制IP列表到剪贴板"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(";".join(ip_list))
            QMessageBox.information(self, "提示", "IP列表已复制到剪贴板")
        except Exception as e:
            logger.error(f"复制IP列表失败: {str(e)}")
            QMessageBox.warning(self, "错误", "复制IP列表失败") 