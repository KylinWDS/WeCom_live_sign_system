# UI 模块文档

## 概述
UI 模块负责系统的用户界面实现，包括窗口、页面、组件等。该模块使用 PyQt6 框架构建现代化的图形用户界面。

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

### 2. 管理器 (managers/)
管理 UI 相关的状态和行为。

主要管理器：
- 主题管理器
- 布局管理器
- 事件管理器
- 状态管理器

### 3. 工具类 (utils/)
UI 相关的工具函数。

主要工具：
- 样式工具
- 布局工具
- 事件工具
- 资源工具

### 4. 窗口 (windows/)
系统的主要窗口。

主要窗口：
- 主窗口
- 登录窗口
- 设置窗口
- 帮助窗口

### 5. 页面 (pages/)
系统的各个功能页面。

主要页面：
- 首页
- 直播管理页
- 数据统计页
- 系统设置页

## 主要功能

### 1. 主题管理
- 支持系统颜色、明亮、暗色三种主题
- 主题切换
- 主题预览
- 主题持久化

### 2. 布局管理
- 响应式布局
- 布局模板
- 布局切换
- 布局保存

### 3. 事件处理
- 事件绑定
- 事件传播
- 事件过滤
- 事件日志

### 4. 状态管理
- 页面状态
- 组件状态
- 数据状态
- 状态同步

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

## 组件说明

### 1. 自定义按钮 (CustomButton)
- 支持多种样式
- 状态反馈
- 动画效果
- 事件处理

### 2. 输入框 (CustomInput)
- 输入验证
- 自动完成
- 历史记录
- 错误提示

### 3. 表格 (CustomTable)
- 排序功能
- 过滤功能
- 分页功能
- 导出功能

### 4. 对话框 (CustomDialog)
- 模态/非模态
- 自定义样式
- 动画效果
- 结果回调

## 页面说明

### 1. 首页
- 企业信息配置
- 用户登录
- 系统状态
- 快捷操作

### 2. 直播管理页
- 直播列表
- 直播创建
- 直播详情
- 数据统计

### 3. 数据统计页
- 数据展示
- 图表分析
- 数据导出
- 报表生成

### 4. 系统设置页
- 基本设置
- 高级设置
- 权限设置
- 备份设置

## 注意事项
1. UI 组件应该保持一致性
2. 注意性能优化
3. 保持代码可维护性
4. 注意用户体验
5. 做好错误处理
6. 支持国际化
7. 注意可访问性 