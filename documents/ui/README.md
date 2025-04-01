# UI 模块文档

## 概述
UI 模块负责系统的用户界面实现，包括窗口、页面、组件等。该模块使用 PySide6/PyQt6 框架构建现代化的图形用户界面，支持系统颜色、明亮、暗色三种主题切换。

## 与启动器的集成

UI模块经过优化，解决了跨线程UI操作的问题。所有UI组件都在主线程中创建和操作，确保了系统在各种平台上的稳定性，特别是在macOS上。启动画面的实现采用Tkinter，避免了早期加载PyQt可能导致的问题。

## 目录结构

### 1. 组件 (components/)
包含可重用的 UI 组件。

主要组件：
- 自定义按钮
- 输入框
- 表格
- 对话框
- 导航栏
- 状态栏
- 进度条
- 初始化向导组件

### 2. 管理器 (managers/)
管理 UI 相关的状态和行为。

主要管理器：
- 主题管理器 (ThemeManager)
- 布局管理器 (LayoutManager)
- 事件管理器 (EventManager)
- 状态管理器 (StateManager)
- 窗口管理器 (WindowManager)
- 菜单管理器 (MenuManager)

### 3. 工具类 (utils/)
UI 相关的工具函数。

主要工具：
- 样式工具 (StyleUtils)
- 布局工具 (LayoutUtils)
- 事件工具 (EventUtils)
- 资源工具 (ResourceUtils)
- 动画工具 (AnimationUtils)
- 图标工具 (IconUtils)

### 4. 窗口 (windows/)
系统的主要窗口。

主要窗口：
- 主窗口 (MainWindow)
- 登录窗口 (LoginWindow)
- 设置窗口 (SettingsWindow)
- 初始化向导窗口 (InitWizardWindow)
- 直播管理窗口 (LiveManagementWindow)
- 签到管理窗口 (SignManagementWindow)

### 5. 页面 (pages/)
系统的各个功能页面。

主要页面：
- 首页 (HomePage)
- 直播列表页 (LiveListPage)
- 直播详情页 (LiveDetailPage)
- 签到管理页 (SignManagementPage)
- 数据统计页 (StatisticsPage)
- 系统设置页 (SettingsPage)
- 企业管理页 (CorporationManagementPage)
- 用户管理页 (UserManagementPage)

## 主要功能

### 1. 初始化向导
- 引导用户完成首次配置
- 数据存储路径配置
- 企业微信配置
- 管理员账户配置
- 配置验证和保存

### 2. 主题管理
- 支持系统颜色、明亮、暗色三种主题
- 即时主题切换
- 主题预览
- 主题持久化
- 自定义主题样式表

### 3. 布局管理
- 响应式布局
- 布局模板
- 布局切换
- 布局保存
- 多显示器支持

### 4. 事件处理
- 事件绑定
- 事件传播
- 事件过滤
- 事件日志
- 自定义事件

### 5. 状态管理
- 页面状态
- 组件状态
- 数据状态
- 状态同步
- 状态持久化

### 6. 进度显示
- 启动进度条
- 操作进度对话框
- 后台任务进度
- 导入导出进度
- 数据同步进度

## 线程安全

UI模块确保所有UI操作都在主线程中完成，避免跨线程UI访问问题：

1. **事件队列**: 后台线程通过事件队列将UI更新请求发送到主线程
2. **信号和槽**: 使用Qt的信号槽机制在线程间安全通信
3. **线程安全的调用**: 提供线程安全的UI更新方法
4. **专用UI线程**: 所有UI组件都在主线程创建和操作

```python
class ThreadSafeUI:
    @staticmethod
    def safe_call(func, *args, **kwargs):
        """在主线程中安全调用UI函数"""
        if QThread.currentThread() is QApplication.instance().thread():
            # 当前已在主线程，直接调用
            return func(*args, **kwargs)
        else:
            # 在其他线程，使用事件循环安全调用
            result = None
            event = threading.Event()
            
            def call_in_main_thread():
                nonlocal result
                result = func(*args, **kwargs)
                event.set()
                
            QMetaObject.invokeMethod(MainWindow.instance(), 
                                     "safe_call_slot",
                                     Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(callable, call_in_main_thread))
            event.wait()
            return result
```

## 使用示例

### 1. 创建主窗口
```python
from src.ui.windows.main_window import MainWindow

class App:
    def __init__(self):
        self.window = MainWindow()
        self.window.show()
```

### 2. 使用自定义组件
```python
from src.ui.components.custom_button import CustomButton

class MyPage:
    def __init__(self):
        self.button = CustomButton("点击我")
        self.button.clicked.connect(self.on_button_click)
```

### 3. 主题切换
```python
from src.ui.managers.theme_manager import ThemeManager

theme_manager = ThemeManager()
# 切换到暗色主题
theme_manager.set_theme("dark")
```

### 4. 布局管理
```python
from src.ui.utils.layout_utils import create_layout

class MyWidget:
    def __init__(self):
        self.layout = create_layout("vertical")
        self.layout.add_widget(self.button)
        self.layout.add_widget(self.input)
```

### 5. 进度对话框
```python
from src.ui.components.progress_dialog import ProgressDialog

class DataExporter:
    def export_data(self, file_path):
        progress = ProgressDialog("正在导出数据...", parent=self)
        progress.show()
        
        try:
            for i in range(100):
                # 执行导出操作
                progress.set_value(i)
                progress.set_status(f"正在处理第 {i+1} 项...")
                time.sleep(0.05)
                
            progress.set_value(100)
            progress.set_status("导出完成")
        finally:
            progress.close()
```

## 组件说明

### 1. 自定义按钮 (CustomButton)
- 支持多种样式
- 状态反馈
- 动画效果
- 事件处理
- 图标支持
- 提示文本

### 2. 初始化向导 (InitWizard)
- 多步骤配置
- 表单验证
- 配置预览
- 返回修改功能
- 自动保存
- 引导说明

### 3. 表格 (CustomTable)
- 排序功能
- 过滤功能
- 分页功能
- 导出功能
- 自定义列宽
- 行高亮
- 右键菜单

### 4. 进度条 (ProgressBar)
- 确定模式
- 不确定模式
- 状态文本
- 取消选项
- 动画效果
- 主题适配

## 页面说明

### 1. 首页
- 企业信息配置
- 用户登录
- 系统状态
- 快捷操作
- 最近直播
- 待办事项

### 2. 直播管理页
- 直播列表
- 直播创建
- 直播详情
- 签到管理
- 数据统计
- 导入导出

### 3. 数据统计页
- 数据展示
- 图表分析
- 数据导出
- 报表生成
- 趋势分析
- 用户画像

### 4. 系统设置页
- 基本设置
- 高级设置
- 权限设置
- 备份设置
- 主题设置
- 关于信息

## 性能优化

UI模块采用多种性能优化策略：

1. **延迟加载**: 页面和组件按需加载，减少启动时间
2. **虚拟滚动**: 大型列表使用虚拟滚动，减少内存占用
3. **缓存机制**: 缓存频繁使用的组件和数据
4. **批量更新**: 合并多次UI更新为一次操作
5. **异步加载**: 大型数据异步加载，避免阻塞UI线程

```python
class LazyLoadedPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._placeholder = QLabel("加载中...", self)
        
    def showEvent(self, event):
        if not self._loaded:
            QTimer.singleShot(0, self._init_content)
        super().showEvent(event)
        
    def _init_content(self):
        # 初始化页面内容
        self._placeholder.hide()
        # ... 初始化组件
        self._loaded = True
```

## 注意事项
1. UI 组件应该保持一致性
2. 注意性能优化
3. 保持代码可维护性
4. 注意用户体验
5. 做好错误处理
6. 支持国际化
7. 注意可访问性
8. 所有UI操作必须在主线程中执行
9. 长时间操作应该在工作线程中执行，避免阻塞UI 