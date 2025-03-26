# PySide6导入
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox,
                             QToolButton, QMessageBox, QFormLayout, QCheckBox, QFrame,
                             QGraphicsDropShadowEffect, QStyledItemDelegate)
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QIcon, QClipboard, QMouseEvent, QColor
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

# API导入
from ...api.wecom import WeComAPI

from src import __version__  # 添加导入 __version__

logger = get_logger(__name__)

class LoginWindow(QMainWindow):
    """登录窗口"""
    
    def __init__(self, auth_manager: AuthManager, config_manager: ConfigManager, db_manager: DatabaseManager):
        super().__init__()
        self.auth_manager = auth_manager
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.main_window = None
        
        # 拖动窗口相关变量
        self.dragging = False
        self.drag_position = QPoint()
        
        # 初始化主题管理器
        self.theme_manager = ThemeManager()
        
        # 记住密码的保存周期（天）
        self.remember_password_days = 7
        
        self.init_ui()
        
        # 获取并显示IP
        self.update_ip_info()
        
        # 加载保存的登录信息
        self.load_saved_credentials()
    
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
        # 基本窗口设置
        self.setWindowTitle("企业微信直播签到系统")
        self.setFixedSize(480, 680)  # 调整窗口高度
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 设置透明背景，配合阴影效果
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 20, 25, 20)  # 调整上下边距
        main_layout.setSpacing(12)  # 减小整体间距
        
        # 添加标题栏
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # 添加IP显示区域
        ip_layout = self.create_ip_section()
        main_layout.addLayout(ip_layout)
        
        # 创建登录表单部分
        form_widget = self.create_login_form()
        main_layout.addWidget(form_widget)
        
        # 创建登录按钮和记住密码行
        login_row = QHBoxLayout()
        login_row.setContentsMargins(0, 10, 0, 5) # 增加上边距
        
        # 左侧弹性空间
        login_row.addStretch(1)
        
        # 创建登录按钮
        login_button = self.create_login_button()
        login_row.addWidget(login_button)
        
        # 记住密码部分
        remember_container = QHBoxLayout()
        remember_container.setContentsMargins(20, 0, 0, 0) # 左边添加20px间距
        remember_container.setAlignment(Qt.AlignmentFlag.AlignVCenter) # 垂直居中对齐
        
        # 创建记住密码复选框
        self.remember_checkbox = QCheckBox("记住密码")
        self.remember_checkbox.setObjectName("rememberCheckbox")
        self.remember_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        remember_container.addWidget(self.remember_checkbox)
        
        # 添加提示标签
        remember_tip = QLabel(f"(有效期{self.remember_password_days}天)")
        remember_tip.setObjectName("rememberTip")
        remember_container.addWidget(remember_tip)
        
        # 将记住密码部分添加到登录行
        login_row.addLayout(remember_container)
        
        # 右侧弹性空间
        login_row.addStretch(1)
        
        # 添加登录行到主布局
        main_layout.addLayout(login_row)
        
        # 添加底部免责声明和版权信息
        footer_widget = self.create_footer()
        main_layout.addWidget(footer_widget)
        
        # 设置窗口为无框
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 设置整体样式
        self.apply_styles()
        
        # 添加动画管理器
        self.animation_manager = AnimationManager()
        
        # 加载企业列表
        self.load_corp_list()
        
        # 确保用户名输入框获得焦点
        self.username_edit.setFocus()
    
    def create_header(self):
        """创建标题栏"""
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)  # 减少下边距
        
        # 创建Logo和标题部分
        logo_title_layout = QHBoxLayout()
        logo_title_layout.setSpacing(12)  # 增加logo和标题之间的间距
        
        # Logo标签 - 使用圆形彩色背景
        logo_label = QLabel("K")  # 简化为单个字母，更现代
        logo_label.setFixedSize(45, 45)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setObjectName("logoLabel")
        logo_title_layout.addWidget(logo_label)
        
        # 标题标签 - 使用更大更粗的字体
        title_label = QLabel("企业微信直播签到系统")
        title_label.setObjectName("titleLabel")
        logo_title_layout.addWidget(title_label)
        
        # 将Logo和标题添加到标题栏
        header_layout.addLayout(logo_title_layout)
        header_layout.addStretch()
        
        # 创建最小化和关闭按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  # 按钮之间的间距
        
        # 最小化按钮
        min_btn = QPushButton("-")
        min_btn.setFixedSize(32, 32)
        min_btn.setObjectName("minButton")
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(min_btn)
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self.close)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(close_btn)
        
        header_layout.addLayout(button_layout)
        
        return header_layout
    
    def create_ip_section(self):
        """创建IP显示区域"""
        ip_layout = QHBoxLayout()
        ip_layout.setContentsMargins(0, 5, 0, 10)  # 调整上下边距
        ip_layout.setSpacing(8)
        
        # IP卡片容器
        ip_widget = QWidget()
        ip_widget.setObjectName("ipInfoWidget")
        ip_widget.setFixedHeight(36)  # 设置固定高度
        ip_widget_layout = QHBoxLayout(ip_widget)
        ip_widget_layout.setContentsMargins(10, 0, 10, 0)  # 减少上下边距
        ip_widget_layout.setSpacing(8)
        
        # IP图标
        ip_icon = QLabel("🌐")
        ip_icon.setObjectName("ipIcon")
        ip_widget_layout.addWidget(ip_icon)
        
        # IP标签
        self.ip_label = QLabel("正在获取IP地址...")
        self.ip_label.setObjectName("ipLabel")
        ip_widget_layout.addWidget(self.ip_label)
        
        # 复制按钮
        self.copy_ip_btn = QLabel("复制")
        self.copy_ip_btn.setObjectName("copyIpBtn")
        self.copy_ip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_ip_btn.mousePressEvent = lambda e: self.copy_ip()
        ip_widget_layout.addWidget(self.copy_ip_btn)
        
        # 警告图标
        warning_label = QLabel("详情")
        warning_label.setObjectName("ipDetailBtn")
        warning_label.setProperty("warning", "true")
        warning_label.setToolTip("点击查看IP配置详情说明")
        warning_label.setCursor(Qt.CursorShape.PointingHandCursor)
        warning_label.mousePressEvent = lambda e: self.show_ip_config_tip()
        ip_widget_layout.addWidget(warning_label)
        
        # 添加右侧空白
        ip_widget_layout.addStretch()
        
        # 将卡片添加到主布局
        ip_layout.addWidget(ip_widget)
        
        return ip_layout
    
    def create_login_form(self):
        """创建登录表单部分"""
        # 创建表单容器
        form_widget = QFrame()
        form_widget.setObjectName("formContainer")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(25, 15, 25, 20)  # 进一步减少内边距
        form_layout.setSpacing(10)  # 进一步减小元素间距
        
        # 创建表单标题
        form_title = QLabel("账号登录")
        form_title.setObjectName("formTitle")
        form_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_title.setFixedHeight(30)  # 设置固定高度
        form_layout.addWidget(form_title)
        
        # 在标题和表单之间添加一点空间
        form_layout.addSpacing(0)
        
        # 创建用户名输入框组件
        username_widget = QWidget()
        username_layout = QVBoxLayout(username_widget)
        username_layout.setContentsMargins(0, 0, 0, 0)
        username_layout.setSpacing(3)  # 进一步减少标签和输入框的间距
        
        username_label = QLabel("用户名")
        username_label.setObjectName("inputLabel")
        username_layout.addWidget(username_label)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setObjectName("usernameEdit")
        self.username_edit.setFixedHeight(42)  # 保持固定高度
        self.username_edit.textChanged.connect(self.on_username_changed)
        username_layout.addWidget(self.username_edit)
        
        form_layout.addWidget(username_widget)
        
        # 创建密码输入框组件
        password_widget = QWidget()
        password_layout = QVBoxLayout(password_widget)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(3)  # 进一步减少标签和输入框的间距
        
        password_label = QLabel("密码")
        password_label.setObjectName("inputLabel")
        password_layout.addWidget(password_label)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setObjectName("passwordEdit")
        self.password_edit.setFixedHeight(42)  # 保持固定高度
        self.password_edit.returnPressed.connect(self.on_login)
        password_layout.addWidget(self.password_edit)
        
        form_layout.addWidget(password_widget)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        separator.setFixedHeight(1)  # 设置固定高度为1像素
        form_layout.addWidget(separator)
        
        # 创建企业选择部分
        corp_widget = QWidget()
        corp_layout = QVBoxLayout(corp_widget)
        corp_layout.setContentsMargins(0, 0, 0, 0)
        corp_layout.setSpacing(5)  # 标签与下拉框之间的间距
        
        corp_label = QLabel("企业选择")
        corp_label.setObjectName("inputLabel")
        corp_layout.addWidget(corp_label)
        
        self.corp_combo = QComboBox()
        self.corp_combo.setEditable(False)  # 设置为不可编辑
        self.corp_combo.setObjectName("corpCombo")
        self.corp_combo.setFixedHeight(42)  # 保持固定高度
        self.corp_combo.currentTextChanged.connect(self.on_corp_changed)
        self.corp_combo.setItemDelegate(QStyledItemDelegate())  # 使用标准代理，改善样式
        self.corp_combo.setPlaceholderText("请选择企业")  # 设置占位文本
        corp_layout.addWidget(self.corp_combo)
        
        # 企业信息标签，用独立的标签显示
        self.corp_info = QLabel("")
        self.corp_info.setObjectName("corpInfo")
        self.corp_info.setFixedHeight(25)  # 增加高度，确保有足够空间
        self.corp_info.setAlignment(Qt.AlignmentFlag.AlignLeft)
        corp_layout.addWidget(self.corp_info)
        
        form_layout.addWidget(corp_widget)
        
        return form_widget
    
    def create_login_button(self):
        """创建登录按钮"""
        self.login_btn = QPushButton("登 录")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setFixedSize(240, 36)  # 调整高度，与复选框更好地对齐
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.on_login)
        
        # 创建加载中指示器效果
        self.login_btn.setProperty("loading", False)
        
        return self.login_btn
    
    def create_footer(self):
        """创建底部免责声明和版权信息"""
        footer_widget = QWidget()
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 10, 0, 0)
        footer_layout.setSpacing(15)
        
        # 添加免责声明
        disclaimer = QLabel(
            "免责声明：本软件仅供个人测试使用，请勿用于商业用途。"
            "使用本软件即表示您同意遵守相关法律法规。"
            f"version_{__version__}"
        )
        disclaimer.setWordWrap(True)
        disclaimer.setObjectName("disclaimer")
        footer_layout.addWidget(disclaimer)
        return footer_widget
    
    def apply_styles(self):
        """应用样式"""
        # 主样式
        qss = """
            /* 全局样式 */
            QWidget {
                font-family: "PingFang SC", "Helvetica Neue", Arial, sans-serif;
                color: #333333;
            }
            
            /* 标题样式 */
            #titleLabel {
                font-size: 22px;
                font-weight: bold;
                color: #1890ff;
                margin-left: 5px;
            }
            
            #logoLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1890ff, stop:1 #36cfc9);
                border-radius: 22px;
                padding: 0px;
                text-align: center;
            }
            
            /* 窗口控制按钮样式 */
            #closeButton, #minButton {
                font-size: 20px;
                font-weight: bold;
                color: #909399;
                background-color: transparent;
                border: none;
                border-radius: 16px;
            }
            #closeButton:hover {
                color: #ffffff;
                background-color: #f56c6c;
            }
            #minButton:hover {
                color: #ffffff;
                background-color: #909399;
            }
            
            /* IP信息样式 */
            #ipInfoWidget {
                background-color: #f0f7ff;
                border-radius: 8px;
                border: 1px solid #e6f7ff;
            }
            #ipIcon {
                font-size: 14px;
                color: #1890ff;
            }
            #ipLabel {
                font-size: 13px;
                color: #606266;
            }
            #copyIpBtn {
                font-size: 13px;
                color: #1890ff;
                text-decoration: underline;
                padding: 0 2px;
            }
            #copyIpBtn:hover {
                color: #40a9ff;
            }
            #ipDetailBtn {
                font-size: 13px;
                color: #f56c6c;
                padding: 0 2px;
            }
            #ipDetailBtn:hover {
                color: #ff7875;
                text-decoration: underline;
            }
            
            /* 表单容器样式 */
            #formContainer {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #ebeef5;
            }
            
            /* 表单标题 */
            #formTitle {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 2px;  /* 减少底部边距 */
            }
            
            /* 表单标签样式 */
            #inputLabel {
                font-size: 14px;
                color: #606266;
                margin-left: 2px;
                margin-bottom: 0px;  /* 移除底部边距 */
            }
            
            /* 输入框样式 */
            QLineEdit, QComboBox {
                font-size: 14px;
                padding: 8px 15px;  /* 减少内边距以适应固定高度 */
                border: 1px solid #dcdfe6;
                border-radius: 8px;
                background-color: #f5f7fa;
                selection-background-color: #e6f7ff;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #1890ff;
                background-color: #ffffff;
                outline: none;
                padding: 7px 14px;  /* 边框加粗时保持整体尺寸 */
            }
            QLineEdit:hover, QComboBox:hover {
                border: 1px solid #c0c4cc;
            }
            
            /* 下拉框特有样式 - 隐藏下拉箭头 */
            QComboBox {
                padding-right: 12px;
            }
            QComboBox::drop-down {
                width: 0;
                border: none;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
            }
            
            /* 下拉列表样式 */
            QComboBox QAbstractItemView {
                border: 1px solid #1890ff;
                border-radius: 6px;
                padding: 5px;
                background-color: white;
                selection-background-color: #e6f7ff;
            }
            
            /* 企业信息标签 */
            #corpInfo {
                font-size: 12px;
                color: #909399;
                margin: 5px;
                padding: 0;
                text-align: left;
            }
            
            /* 分隔线样式 */
            #separator {
                background-color: #ebeef5;
                height: 1px;
                margin: 1px 0;  /* 减少分隔线上下边距 */
            }
            
            /* 登录按钮样式 */
            #loginButton {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1890ff, stop:1 #36cfc9);
                border: none;
                border-radius: 25px;
            }
            #loginButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #40a9ff, stop:1 #5cdbd3);
            }
            #loginButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #096dd9, stop:1 #13a8a8);
            }
            
            /* 加载中状态 */
            #loginButton[loading="true"] {
                color: transparent;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1890ff, stop:1 #36cfc9);
            }
            
            /* 免责声明样式 */
            #disclaimer {
                font-size: 12px;
                color: #909399;
                text-align: center;
                padding: 5px;
            }
            
            /* 设置QLineEdit的选择背景 */
            QLineEdit {
                selection-color: white;
                selection-background-color: #1890ff;
            }
            
            /* 记住密码复选框样式 - 移除，使用系统默认样式 */
            /* 仅保留文本大小和提示文本样式 */
            #rememberTip {
                font-size: 12px;
                color: #909399;
                margin-left: 5px;
            }
        """
        self.setStyleSheet(qss)
        
        # 为窗口添加圆角和阴影
        window_effect = """
            #centralwidget {
                background-color: #f0f2f5;
                border-radius: 12px;
            }
        """
        self.centralWidget().setObjectName("centralwidget")
        self.centralWidget().setStyleSheet(window_effect)
        
        # 应用窗口阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 0)
        self.centralWidget().setGraphicsEffect(shadow)
        
        # 应用表单容器阴影
        form_shadow = QGraphicsDropShadowEffect(self.findChild(QFrame, "formContainer"))
        form_shadow.setBlurRadius(15)
        form_shadow.setColor(QColor(0, 0, 0, 30))
        form_shadow.setOffset(0, 2)
        self.findChild(QFrame, "formContainer").setGraphicsEffect(form_shadow)
        
        # 应用登录按钮阴影
        login_btn_shadow = QGraphicsDropShadowEffect(self.login_btn)
        login_btn_shadow.setBlurRadius(15)
        login_btn_shadow.setColor(QColor(24, 144, 255, 100))
        login_btn_shadow.setOffset(0, 4)
        self.login_btn.setGraphicsEffect(login_btn_shadow)
    
    def load_corp_list(self):
        """加载企业列表"""
        try:
            # 先清空下拉框
            self.corp_combo.clear()
            
            # 添加空白选项作为默认值
            self.corp_combo.addItem("")
            
            # 从数据库获取企业列表
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
                # 添加企业到下拉框
                for corp in corp_data:
                    self.corp_combo.addItem(corp['name'])
            else:
                # 如果数据库中没有企业信息，从配置文件获取
                corporations = self.config_manager.get_corporations()
                for corp in corporations:
                    self.corp_combo.addItem(corp["name"])
                    
            # 选择第一项（空白选项）
            self.corp_combo.setCurrentIndex(0)
            self.corp_info.setText("")
                    
        except Exception as e:
            logger.error(f"加载企业列表失败: {str(e)}")
            QMessageBox.warning(self, "警告", "加载企业列表失败")
    
    def on_username_changed(self, text: str):
        """当用户名变更时的处理"""
        is_root_admin = text.lower().strip() == "root-admin"
        
        # 如果是root-admin，则禁用企业选择和记住密码选项
        if is_root_admin:
            # 设置企业选择不可用
            self.corp_combo.setEnabled(False)
            # 清空企业选择框内容
            self.corp_combo.clear()  # 完全清空所有选项
            # 取消选中记住密码复选框
            self.remember_checkbox.setChecked(False)
            # 禁用记住密码复选框
            self.remember_checkbox.setEnabled(False)
            # 显示超级管理员提示信息
            self.corp_info.setText("超级管理员无需选择企业")
            # 减少UI刷新次数，只在最后刷新一次
            self.update()
        else:
            # 普通用户，启用企业选择
            self.corp_combo.setEnabled(True)
            # 如果企业列表为空，重新加载企业列表
            if self.corp_combo.count() == 0:
                self.load_corp_list()
            # 启用记住密码复选框
            self.remember_checkbox.setEnabled(True)
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
        # 显示加载状态
        self.login_btn.setText("登录中...")
        self.login_btn.setProperty("loading", True)
        self.login_btn.setEnabled(False)
        self.login_btn.style().unpolish(self.login_btn)
        self.login_btn.style().polish(self.login_btn)
        self.login_btn.update()
        
        # 给UI一些时间来更新显示
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._perform_login)
    
    def _perform_login(self):
        """执行实际的登录逻辑"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not username or not password:
            self.reset_login_button()
            QMessageBox.warning(self, "警告", "请输入用户名和密码")
            return
        
        # 如果是root-admin，不需要验证企业
        if username.lower() == "root-admin":
            corpname = None
            # 确保root-admin不保存凭据
            self.remember_checkbox.setChecked(False)
            self.remember_checkbox.setEnabled(False)
            # 彻底清除企业选择
            self.corp_combo.clear()
            self.corp_combo.setEnabled(False)
            self.corp_info.setText("超级管理员无需选择企业")
            # 减少UI刷新
            self.update()
        else:
            corpname = self.corp_combo.currentText().strip()
            if not corpname:
                self.reset_login_button()
                QMessageBox.warning(self, "警告", "请选择企业")
                return
        
        try:
            success, message = self.auth_manager.login(username, password, corpname)
            if success:
                logger.info(f"用户 {username} 登录成功")
                
                # 保存登录凭据（如果选择了记住密码且不是root-admin）
                if username.lower() != "root-admin" and self.remember_checkbox.isChecked():
                    self.save_credentials(username, password, corpname)
                elif not self.remember_checkbox.isChecked():
                    # 如果取消了记住密码选项，删除之前保存的凭据
                    self.delete_saved_credentials()
                
                # 获取完整的用户信息并在新的会话中使用
                session = self.db_manager.Session()
                try:
                    user = session.query(User).filter_by(login_name=username).first()
                    if user:
                        # 非root-admin用户需要测试企业微信API连通性
                        if username.lower() != "root-admin":
                            try:
                                # 获取企业信息
                                corp = None
                                wecom_api = None
                                
                                # 优先使用用户ID和前端传递的企业名称查询企业模型
                                logger.info(f"使用企业名称[{corpname}]和用户企业ID[{user.corpid}]查询企业信息")
                                corp = session.query(Corporation).filter_by(name=corpname, corp_id=user.corpid, status=True).first()
                                # 如果仍然没有有效的企业信息，提示用户联系管理员
                                if not corp:
                                    error_msg = "无法获取有效的企业信息，请联系超级管理员(root-admin)登录账户维护"
                                    logger.warning(error_msg)
                                    self.reset_login_button()
                                    QMessageBox.warning(self, "企业信息缺失", error_msg)
                                    return
                                logger.info(f"找到企业信息: {corp.name}")
                                # 创建WeComAPI实例
                                wecom_api = WeComAPI(
                                    corpid=corp.corp_id,
                                    corpsecret=corp.corp_secret,
                                    agent_id=corp.agent_id
                                )
                                
                                # 用于API测试的用户ID
                                user_id = user.wecom_code if user.wecom_code else user.login_name
                                
                                # 测试企业微信API连通性
                                logger.info(f"正在测试企业微信API连通性: 用户={user_id}")
                                wecom_api.test_connection(user_id)
                                logger.info("企业微信API连通性测试成功")
                                
                            except Exception as e:
                                error_message = str(e)
                                logger.error(f"企业微信API连通性测试失败: {error_message}")
                                
                                # 使用错误处理器处理企业微信API错误
                                from src.utils.error_handler import ErrorHandler
                                error_handler = ErrorHandler()
                                continue_login = error_handler.handle_wecom_api_error(e, self, self.db_manager)
                                
                                if not continue_login:
                                    self.reset_login_button()
                                    return
                                # 如果用户选择继续使用，则继续创建主窗口
                        
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
                        self.reset_login_button()
                        QMessageBox.warning(self, "错误", "获取用户信息失败")
                except Exception as e:
                    session.close()
                    self.reset_login_button()
                    raise e
            else:
                self.reset_login_button()
                QMessageBox.warning(self, "错误", message)
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            self.reset_login_button()
            QMessageBox.critical(self, "错误", "登录失败，请稍后重试")
    
    def reset_login_button(self):
        """重置登录按钮状态"""
        self.login_btn.setText("登 录")
        self.login_btn.setProperty("loading", False)
        self.login_btn.setEnabled(True)
        self.login_btn.style().unpolish(self.login_btn)
        self.login_btn.style().polish(self.login_btn)
        self.login_btn.update()
    
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

    def load_saved_credentials(self):
        """加载保存的登录凭据"""
        try:
            # 不为 root-admin 加载保存的凭据
            if self.username_edit.text().lower() == "root-admin":
                # 确保记住密码复选框为未选中状态
                self.remember_checkbox.setChecked(False)
                # 禁用记住密码复选框
                self.remember_checkbox.setEnabled(False)
                return
                
            with self.db_manager.get_session() as session:
                # 从设置表中获取保存的登录凭据
                from src.models.settings import Settings
                setting = session.query(Settings).filter_by(name="remember_password", type="user").first()
                
                if setting and setting.value and setting.config:
                    import json
                    from datetime import datetime, timedelta
                    
                    # 解析保存的数据
                    try:
                        saved_data = json.loads(setting.value)
                        # 检查是否过期
                        saved_time = datetime.fromisoformat(saved_data.get("timestamp", ""))
                        if datetime.now() - saved_time > timedelta(days=self.remember_password_days):
                            # 凭据已过期，删除
                            session.delete(setting)
                            session.commit()
                            return
                            
                        # 提取用户名和密码
                        username = saved_data.get("username", "")
                        password = saved_data.get("password", "")
                        corpname = saved_data.get("corpname", "")
                        
                        # 不为超级管理员加载
                        if username.lower() == "root-admin":
                            return
                            
                        # 填充到表单
                        self.username_edit.setText(username)
                        self.password_edit.setText(password)
                        
                        # 选择对应的企业
                        index = self.corp_combo.findText(corpname)
                        if index >= 0:
                            self.corp_combo.setCurrentIndex(index)
                            
                        # 选中记住密码复选框
                        self.remember_checkbox.setChecked(True)
                    except Exception as e:
                        logger.error(f"解析保存的登录凭据失败: {str(e)}")
        except Exception as e:
            logger.error(f"加载保存的登录凭据失败: {str(e)}")

    def save_credentials(self, username, password, corpname):
        """保存登录凭据"""
        try:
            # 不保存 root-admin 的凭据
            if username.lower() == "root-admin":
                return
                
            # 判断是否需要保存
            if not self.remember_checkbox.isChecked():
                # 如果取消了记住密码，则删除之前保存的
                with self.db_manager.get_session() as session:
                    from src.models.settings import Settings
                    setting = session.query(Settings).filter_by(name="remember_password", type="user").first()
                    if setting:
                        session.delete(setting)
                        session.commit()
                return
                
            # 准备保存的数据
            import json
            from datetime import datetime
            
            saved_data = {
                "username": username,
                "password": password,
                "corpname": corpname,
                "timestamp": datetime.now().isoformat()
            }
            
            # 保存到数据库
            with self.db_manager.get_session() as session:
                from src.models.settings import Settings
                
                # 查找已有设置
                setting = session.query(Settings).filter_by(name="remember_password", type="user").first()
                
                if setting:
                    # 更新现有设置
                    setting.value = json.dumps(saved_data)
                    setting.updated_at = datetime.now()
                else:
                    # 创建新设置
                    setting = Settings(
                        name="remember_password",
                        value=json.dumps(saved_data),
                        type="user",
                        description="记住密码设置",
                        config={"expiry_days": self.remember_password_days}
                    )
                    session.add(setting)
                    
                session.commit()
                logger.info(f"保存登录凭据成功: {username}")
        except Exception as e:
            logger.error(f"保存登录凭据失败: {str(e)}")

    def delete_saved_credentials(self):
        """删除保存的登录凭据"""
        try:
            with self.db_manager.get_session() as session:
                # 从设置表中获取保存的登录凭据
                from src.models.settings import Settings
                setting = session.query(Settings).filter_by(name="remember_password", type="user").first()
                
                if setting:
                    session.delete(setting)
                    session.commit()
                    logger.info(f"删除登录凭据成功: {self.username_edit.text()}")
        except Exception as e:
            logger.error(f"删除登录凭据失败: {str(e)}")

    # 重写鼠标事件方法，实现窗口拖动
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if event.buttons() & Qt.MouseButton.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept() 