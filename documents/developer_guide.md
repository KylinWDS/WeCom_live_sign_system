# 企业微信直播签到系统 - 开发指南

本文档为企业微信直播签到系统的开发指南，旨在帮助开发者理解系统架构、代码结构和开发规范。

## 系统架构

企业微信直播签到系统采用模块化设计，主要分为以下几个核心模块：

### 核心架构

```
WeCom_live_sign_system/
│
├── launcher.py           # 应用启动入口
├── src/                  # 源代码目录
│   ├── main.py           # 主程序入口
│   ├── app.py            # 应用上下文
│   ├── config/           # 配置模块
│   ├── models/           # 数据模型
│   ├── controllers/      # 控制器
│   ├── views/            # 视图
│   ├── utils/            # 工具函数
│   └── resources/        # 资源文件
├── tools/                # 构建和工具脚本
└── documents/            # 文档
```

### 技术栈

- **编程语言**: Python 3.8+
- **GUI框架**: PySide6/PyQt6
- **数据库**: SQLite (SQLAlchemy ORM)
- **API交互**: requests库
- **数据处理**: pandas, numpy
- **构建工具**: PyInstaller

## 模块说明

### 启动模块 (launcher.py)

启动器负责显示启动画面、加载主程序并处理启动期间的异常。详细设计见[launcher.md](launcher.md)。

```python
class SplashScreen:
    # 管理启动画面
    
class AppLauncher:
    # 负责应用程序初始化和启动
```

### 应用上下文 (src/app.py)

应用上下文管理全局状态、配置和服务：

```python
class AppContext:
    # 管理应用生命周期和全局状态
    
    def initialize(self):
        # 初始化应用
        
    def run(self):
        # 运行主应用程序循环
        
    def shutdown(self):
        # 安全关闭应用
```

### 数据模型 (src/models/)

系统的核心数据模型包括：

- **User**: 用户信息
- **Department**: 部门信息
- **Live**: 直播信息
- **LiveViewer**: 观看和签到信息
- **Corporation**: 企业信息

详细模型定义参见[models/README.md](models/README.md)。

## 开发规范

### 代码风格

- 遵循PEP 8规范
- 使用4个空格进行缩进
- 行长度不超过120个字符
- 使用有意义的变量名和函数名

```python
# 推荐的命名风格
class UserManager:
    def get_user_by_id(self, user_id):
        # 实现细节
        pass
```

### 注释规范

- 使用文档字符串（docstring）描述类和函数
- 复杂逻辑需添加行内注释
- 使用英文编写注释

```python
def calculate_sign_rate(live_id):
    """
    Calculate the sign-in rate for a specific live session.
    
    Args:
        live_id (int): The ID of the live session
        
    Returns:
        float: The sign-in rate as a percentage
    """
    # Implementation details
    pass
```

### 异常处理

- 使用明确的异常类型
- 不要捕获所有异常（避免使用`except:`）
- 提供有用的错误信息

```python
try:
    result = api_function()
except ApiConnectionError as e:
    logger.error(f"API连接失败: {e}")
    show_error_dialog("无法连接到企业微信API，请检查网络连接")
```

## 开发流程

### 环境设置

1. 克隆仓库并设置虚拟环境:
```bash
git clone https://github.com/yourusername/WeCom_live_sign_system.git
cd WeCom_live_sign_system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 分支策略

- **main**: 稳定的生产代码
- **develop**: 开发分支，用于集成功能
- **feature/xxx**: 新功能分支
- **bugfix/xxx**: 错误修复分支

## 扩展指南

### 添加新模型

1. 在`src/models/`目录下创建新模型文件
2. 定义模型类，继承自`Base`
3. 实现必要的关系和方法
4. 在`src/models/__init__.py`中注册模型

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class NewModel(Base):
    __tablename__ = 'new_model'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    # 其他字段和关系
```

### 添加新视图

1. 在`src/views/`目录下创建新视图文件
2. 实现视图类，通常继承自`QWidget`或`QMainWindow`
3. 在适当的地方集成到现有UI

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton

class NewFeatureView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        button = QPushButton("执行操作")
        button.clicked.connect(self.on_button_clicked)
        layout.addWidget(button)
```

## 测试与调试

### 单元测试

- 使用pytest框架编写测试
- 测试文件放在`tests/`目录下
- 测试命名规范：`test_[模块名].py`

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_user_controller.py
```

### 日志使用

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.debug("详细调试信息")
    logger.info("操作信息")
    logger.warning("警告信息")
    logger.error("错误信息")
```

## 发布流程

### 版本控制

版本号遵循语义化版本规范：`主版本.次版本.修订版本`

### 发布步骤

1. 更新`CHANGELOG.md`
2. 更新版本号（`src/config/version.py`）
3. 合并到`main`分支
4. 创建版本标签
5. 运行构建脚本

```bash
# 创建版本标签
git tag -a v1.0.0 -m "版本1.0.0发布"
git push origin v1.0.0

# 构建应用
./build.sh  # 或 build.bat (Windows)
```

## 资源与参考

- [PySide6 文档](https://doc.qt.io/qtforpython-6/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [企业微信API文档](https://developer.work.weixin.qq.com/document/)
- [PyInstaller 文档](https://pyinstaller.readthedocs.io/) 