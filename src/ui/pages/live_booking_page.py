from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTextEdit, QComboBox,
                             QDateTimeEdit, QSpinBox, QMessageBox, QGroupBox,
                             QFormLayout, QCalendarWidget)
from PySide6.QtCore import Qt, QDateTime, QTime, Signal
from PySide6.QtGui import QIcon, QPalette, QColor
from ..managers.style import StyleManager
from ..utils.widget_utils import WidgetUtils
from src.utils.logger import get_logger
from src.ui.managers.animation import AnimationManager
from src.utils.performance_manager import PerformanceManager
from src.utils.error_handler import ErrorHandler
from src.models.live_booking import LiveBooking
from src.models.user import User
from src.core.database import DatabaseManager
from src.api.wecom import WeComAPI
from src.core.task_manager import TaskManager
from datetime import datetime
import pandas as pd
import os
from ..components.widgets.custom_datetime_widget import CustomDateTimeWidget

logger = get_logger(__name__)

class LiveBookingPage(QWidget):
    """直播预约页面"""
    
    def __init__(self, db_manager: DatabaseManager, wecom_api: WeComAPI, task_manager: TaskManager, user_id=None):
        super().__init__()
        self.db_manager = db_manager
        self.wecom_api = wecom_api
        self.task_manager = task_manager
        self.performance_manager = PerformanceManager()
        self.error_handler = ErrorHandler()
        self.user_id = user_id  # 用户ID而不是用户对象
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("liveBookingPage")
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # 减小主布局的间距
        layout.setContentsMargins(15, 15, 15, 15)  # 减小主布局的边距
        
        # 创建表单
        form_group = self._create_form_group()
        layout.addWidget(form_group)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)  # 减小按钮布局的上边距
        
        # 保存按钮
        save_btn = QPushButton("创建直播")
        save_btn.setObjectName("primaryButton")
        save_btn.setMinimumWidth(120)
        save_btn.setMinimumHeight(36)
        save_btn.clicked.connect(self._on_save)
        
        # 重置按钮
        reset_btn = QPushButton("重置")
        reset_btn.setObjectName("defaultButton")
        reset_btn.setMinimumWidth(120)
        reset_btn.setMinimumHeight(36)
        reset_btn.clicked.connect(self._clear_form)
        
        button_layout.addStretch()
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 加载用户列表
        self._load_users()
        
    def _create_form_group(self) -> QGroupBox:
        """创建表单组"""
        group = QGroupBox("直播信息")
        
        layout = QFormLayout(group)
        layout.setSpacing(5)  # 减小表单项之间的间距
        layout.setContentsMargins(15, 20, 15, 15)  # 减小表单组的边距
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # 主播信息
        self.anchor_combo = QComboBox()
        self.anchor_combo.setEditable(True)
        self.anchor_combo.setPlaceholderText("请选择或输入主播ID")
        self.anchor_combo.setMinimumWidth(300)
        layout.addRow(self._create_label("主播"), self.anchor_combo)
        
        # 直播标题
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("请输入直播标题(最多20个字符)")
        self.title_input.setMinimumWidth(300)
        layout.addRow(self._create_label("标题"), self.title_input)
        
        # 时间选择部分
        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(10)  # 设置适当的间距
        
        # 使用更紧凑的布局和统一的标签样式
        label_style = """
            QLabel {
                color: #606266;
                font-size: 14px;
                padding: 0;
                margin: 0;
                min-height: 36px;
                line-height: 36px;
                background: transparent;
            }
        """
        
        # 开始时间容器
        start_container = QWidget()
        start_layout = QHBoxLayout(start_container)
        start_layout.setContentsMargins(0, 0, 0, 0)
        start_layout.setSpacing(2)
        
        from_label = QLabel("从")
        from_label.setFixedWidth(20)
        from_label.setStyleSheet(label_style)
        from_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.start_time = CustomDateTimeWidget()
        self.start_time.setDateTime(QDateTime.currentDateTime().addSecs(600))
        self.start_time.dateTimeChanged.connect(self._on_time_changed)
        self.start_time.setWidth(200)
        
        start_layout.addWidget(from_label)
        start_layout.addWidget(self.start_time)
        
        # 结束时间容器
        end_container = QWidget()
        end_layout = QHBoxLayout(end_container)
        end_layout.setContentsMargins(0, 0, 0, 0)
        end_layout.setSpacing(2)
        
        to_label = QLabel("至")
        to_label.setFixedWidth(20)
        to_label.setStyleSheet(label_style)
        to_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.end_time = CustomDateTimeWidget()
        self.end_time.setDateTime(QDateTime.currentDateTime().addSecs(7800))
        self.end_time.dateTimeChanged.connect(self._on_time_changed)
        self.end_time.setWidth(200)
        
        end_layout.addWidget(to_label)
        end_layout.addWidget(self.end_time)
        
        # 时长显示容器
        duration_container = QWidget()
        duration_layout = QHBoxLayout(duration_container)
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(2)
        
        duration_label = QLabel("时长")
        duration_label.setFixedWidth(30)
        duration_label.setStyleSheet(label_style)
        duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 时长显示样式
        duration_style = """
            QSpinBox {
                border: 1px solid #DCDFE6;
                border-radius: 4px;
                padding: 0 5px;
                min-height: 36px;
                background: #F5F7FA;
            }
        """
        
        self.duration = QSpinBox()
        self.duration.setRange(1, 24 * 3600)
        self.duration.setValue(7200)
        self.duration.setSuffix(" 秒")
        self.duration.setReadOnly(True)
        self.duration.setButtonSymbols(QSpinBox.NoButtons)
        self.duration.setFixedWidth(80)
        self.duration.setAlignment(Qt.AlignRight)
        self.duration.setStyleSheet(duration_style)
        
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration)
        
        # 设置每个部分的固定高度以确保对齐
        start_container.setFixedHeight(36)
        end_container.setFixedHeight(36)
        duration_container.setFixedHeight(36)
        
        # 将三个容器添加到主布局，并添加适当的伸缩因子以控制间距
        time_layout.addWidget(start_container)
        time_layout.addWidget(end_container)
        time_layout.addWidget(duration_container)
        
        # 添加伸缩因子以确保三个容器均匀分布
        time_layout.addStretch(1)
        
        # 设置表单布局的行间距
        layout.addRow(self._create_label("时间"), time_widget)
        
        # 直播类型
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "通用直播",
            "小班课",
            "大班课",
            "企业培训",
            "活动直播"
        ])
        self.type_combo.setCurrentText("企业培训")
        self.type_combo.setMinimumWidth(300)
        layout.addRow(self._create_label("类型"), self.type_combo)
        
        # 直播描述
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("请输入直播描述(最多100个字符)")
        self.desc_input.setMinimumWidth(300)
        self.desc_input.setMaximumHeight(100)
        layout.addRow(self._create_label("描述"), self.desc_input)
        
        return group
        
    def _create_label(self, text: str) -> QLabel:
        """创建统一样式的表单标签"""
        label = QLabel(f"{text}:")
        label.setMinimumWidth(70)
        label.setFixedHeight(36)
        label.setStyleSheet("""
            QLabel {
                color: #606266;
                font-size: 14px;
                padding: 0;
                margin: 0;
                min-height: 36px;
                line-height: 36px;
                background: transparent;
            }
        """)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label
        
    def _load_users(self):
        """加载用户列表"""
        try:
            with self.db_manager.get_session() as session:
                # 获取当前用户信息（如果有用户ID）
                current_user = None
                if self.user_id:
                    current_user = session.query(User).filter_by(userid=self.user_id).first()
                
                # 如果无法获取当前用户，获取最后登录的用户作为默认值
                if not current_user:
                    current_user = session.query(User).order_by(User.last_login.desc()).first()
                    if current_user:
                        self.user_id = current_user.userid
                
                # 清空下拉列表
                self.anchor_combo.clear()
                
                if current_user and current_user.login_name.lower() == "root-admin":
                    # 如果是超级管理员，加载除root-admin外的所有用户
                    users = session.query(User).filter(
                        User.login_name != "root-admin",
                        User.is_active == True
                    ).all()
                    
                    # 添加用户到下拉列表
                    for user in users:
                        # 使用login_name作为值，而不是wecom_code
                        user_login_name = user.login_name
                        # 显示格式：用户名(登录名|所属企业名称)
                        display_name = f"{user.name} ({user_login_name}|{user.corpname or '未知企业'})"
                        self.anchor_combo.addItem(display_name, user_login_name)
                else:
                    # 非超级管理员，只显示自己
                    if current_user:
                        # 使用login_name作为值，而不是wecom_code
                        user_login_name = current_user.login_name
                        display_name = f"{current_user.name} ({user_login_name}|{current_user.corpname or '未知企业'})"
                        self.anchor_combo.addItem(display_name, user_login_name)
                
                # 设置当前用户为默认值（如果不是root-admin的话）
                if current_user and current_user.login_name.lower() != "root-admin":
                    # 使用login_name作为值，而不是wecom_code
                    current_user_login_name = current_user.login_name
                    index = self.anchor_combo.findData(current_user_login_name)
                    if index >= 0:
                        self.anchor_combo.setCurrentIndex(index)
                        
        except Exception as e:
            logger.error(f"加载用户列表失败: {str(e)}")
            self.error_handler.handle_error(e, self, "加载用户列表失败")
        
    def _on_time_changed(self):
        """时间变化事件处理"""
        try:
            start = self.start_time.dateTime()
            end = self.end_time.dateTime()
            
            # 确保结束时间不早于开始时间
            if end <= start:
                end = start.addSecs(3600)  # 默认至少1小时
                self.end_time.setDateTime(end)
                return
            
            # 计算时间差（秒）
            duration = start.secsTo(end)
            
            # 限制最大时长为24小时
            if duration > 24 * 3600:
                end = start.addSecs(24 * 3600)
                self.end_time.setDateTime(end)
                duration = 24 * 3600
            
            # 更新时长显示
            self.duration.setValue(duration)
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "计算时长失败")

    @PerformanceManager.measure_operation("validate_input")
    def _validate_input(self) -> bool:
        """验证输入"""
        try:
            # 验证主播ID
            if not self.anchor_combo.currentText().strip():
                ErrorHandler.handle_warning("请输入主播ID", self)
                return False
                
            # 验证直播标题
            title = self.title_input.text().strip()
            if not title:
                ErrorHandler.handle_warning("请输入直播标题", self)
                return False
            if len(title) > 20:
                ErrorHandler.handle_warning("直播标题不能超过20个字符", self)
                return False
                
            # 验证时间
            start = self.start_time.dateTime()
            end = self.end_time.dateTime()
            if end <= start:
                ErrorHandler.handle_warning("结束时间必须晚于开始时间", self)
                return False
            
            duration = start.secsTo(end)
            if duration > 24 * 3600:
                ErrorHandler.handle_warning("直播时长不能超过24小时", self)
                return False
                
            # 验证直播描述
            desc = self.desc_input.toPlainText().strip()
            if len(desc) > 100:
                ErrorHandler.handle_warning("直播描述不能超过100个字符", self)
                return False
                
            # 验证直播类型
            type_index = self.type_combo.currentIndex()
            if type_index not in [0, 3, 4]:  # 不是通用直播、企业培训或活动直播
                reply = ErrorHandler.handle_question(
                    "当前选择的直播类型可能会创建失败，是否继续？",
                    self,
                    "提示"
                )
                if not reply:
                    return False
                    
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "验证输入失败")
            return False
        
    @PerformanceManager.measure_operation("save_live_info")
    def _on_save(self):
        """保存直播信息"""
        try:
            # 验证输入
            if not self._validate_input():
                return
                
            # 获取主播的登录名（用于查询应用ID）和企业微信ID（用于创建直播）
            login_name = self.anchor_combo.currentData()  # 这是登录名，用于查询应用ID
            anchor_id = login_name  # 默认使用登录名作为企业微信ID
            
            # 查询用户的wecom_code，如果有则使用它作为企业微信ID
            with self.db_manager.get_session() as session:
                from src.models.user import User
                user = session.query(User).filter_by(login_name=login_name).first()
                if user and user.wecom_code:
                    anchor_id = user.wecom_code
            
            # 获取输入数据
            data = {
                "anchor_userid": anchor_id,  # 使用企业微信ID作为主播ID
                "theme": self.title_input.text().strip(),
                "living_start": int(self.start_time.dateTime().toSecsSinceEpoch()),
                "living_duration": self.duration.value(),
                "description": self.desc_input.toPlainText().strip(),
                "type": self.type_combo.currentIndex(),
                "agentid": self.db_manager.get_agent_id_by_user(login_name)  # 使用登录名查询应用ID
            }
            
            # 显示确认对话框
            reply = ErrorHandler.handle_question(
                f"确认创建直播？\n\n"
                f"主播: {self.anchor_combo.currentText()}\n"
                f"标题: {data['theme']}\n"
                f"开始时间: {self.start_time.dateTime().toString('yyyy-MM-dd hh:mm:ss')}\n"
                f"时长: {data['living_duration']}秒\n"
                f"类型: {self.type_combo.currentText()}\n"
                f"描述: {data['description']}",
                self,
                "创建确认"
            )
            
            if not reply:
                return
                
            # 创建直播
            result = self.wecom_api.create_live(**data)
            
            if result["errcode"] == 0:
                # 保存到数据库
                live = self.save_live_info(result["livingid"], data)
                
                # 调度详情拉取任务
                self.task_manager.schedule_live_info_task(
                    result["livingid"],
                    data["living_start"]
                )
                
                # 显示成功对话框
                from src.ui.components.dialogs.live_dialogs import LiveCreateSuccessDialog
                dialog = LiveCreateSuccessDialog(result, self)
                dialog.navigate_to_list.connect(self._navigate_to_live_list)
                dialog.exec()
                
                # 清空表单
                self._clear_form()
                
            else:
                ErrorHandler.handle_error(
                    Exception(result["errmsg"]),
                    self,
                    "创建直播失败"
                )
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存直播信息失败")

    def _navigate_to_live_list(self):
        """导航到直播列表页面"""
        try:
            # 通知父窗口或主窗口切换到直播列表页面
            # 由于不同的UI结构可能有不同的实现方式，这里找到主窗口并调用相应方法
            from src.ui.windows.main_window import MainWindow
            
            # 向上遍历父窗口，找到主窗口
            parent = self.parent()
            while parent and not isinstance(parent, MainWindow):
                parent = parent.parent()
                
            if parent and isinstance(parent, MainWindow):
                # 如果找到主窗口，切换到直播列表页面
                # 假设主窗口有switchToLiveList方法
                if hasattr(parent, 'switchToLiveList'):
                    parent.switchToLiveList()
                elif hasattr(parent, 'home_page') and hasattr(parent.home_page, 'switchToLiveList'):
                    parent.home_page.switchToLiveList()
                else:
                    logger.warning("无法切换到直播列表页面：未找到切换方法")
            else:
                logger.warning("无法切换到直播列表页面：未找到主窗口")
        except Exception as e:
            logger.error(f"切换到直播列表页面时出错: {str(e)}")

    def _clear_form(self):
        """清空表单"""
        self.title_input.clear()
        self.start_time.setDateTime(QDateTime.currentDateTime().addSecs(600))
        self.end_time.setDateTime(QDateTime.currentDateTime().addSecs(7800))
        self.duration.setValue(7200)
        self.type_combo.setCurrentText("企业培训")
        self.desc_input.clear()
        self._load_users()  # 重新加载用户列表
        
    def save_live_info(self, livingid: str, data: dict):
        """保存直播信息到数据库"""
        try:
            with self.db_manager.get_session() as session:
                # 获取当前用户对应的企业名称
                from src.models.user import User
                current_user = None
                if self.user_id:
                    current_user = session.query(User).filter_by(userid=self.user_id).first()
                
                # 获取企业名称
                corpname = current_user.corpname if current_user and current_user.corpname else "未知企业"
                
                live = LiveBooking(
                    livingid=livingid,
                    anchor_userid=data["anchor_userid"],
                    theme=data["theme"],
                    living_start=datetime.fromtimestamp(data["living_start"]),
                    living_duration=data["living_duration"],
                    description=data["description"],
                    type=data["type"],
                    status=0,  # 预约中
                    corpname=corpname,  # 添加企业名称
                    agentid=data["agentid"]  # 应用ID
                )
                session.add(live)
                session.commit()
                return live
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存直播信息到数据库失败")
            raise 