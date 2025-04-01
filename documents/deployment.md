# 企业微信直播签到系统 - 打包与部署指南

本文档描述了企业微信直播签到系统的打包和部署流程，包括环境准备、打包工具使用、以及部署后的配置步骤。

## 打包概述

系统使用PyInstaller将Python应用程序打包为独立的可执行文件，支持Windows、MacOS和Linux平台。打包过程将应用程序、依赖库、资源文件等整合为一个单独的目录或单文件，便于分发和部署。

## 环境要求

### 开发环境
- Python 3.8+
- 所有依赖库 (见 requirements.txt)
- PyInstaller 6.0+

### 用户环境
- Windows 10/11 或 macOS 11+ 或 Linux (主流发行版)
- 不需要安装Python或任何依赖
- 互联网连接（用于访问企业微信API）

## 准备工作

1. 安装打包工具：
```bash
pip install pyinstaller
```

2. 确保所有依赖已安装：
```bash
pip install -r requirements.txt
```

3. 验证应用能正常运行：
```bash
python launcher.py
```

## 打包流程

系统提供了自动化打包脚本，简化了打包过程：

### 使用打包脚本

#### macOS / Linux
```bash
chmod +x build.sh
./build.sh
```

#### Windows
```cmd
build.bat
```

### 打包选项

打包脚本提供了多种选项，可通过交互方式选择：

1. **打包架构**
   - 当前架构 (自动检测)
   - Intel (x86_64)
   - Apple Silicon (arm64) (仅macOS)
   - 通用二进制 (Universal Binary) (仅macOS)

2. **打包模式**
   - 目录模式 (快速启动，分发时需要整个目录)
   - 单文件模式 (启动较慢，但分发更简便)

3. **内存优化级别**
   - 低 (最小内存要求: 1024MB)
   - 中 (最小内存要求: 2048MB)
   - 高 (最小内存要求: 4096MB)

4. **调试版本**
   - 是 (包含调试信息，文件更大)
   - 否 (正常版本)

打包脚本还支持自动选择选项，默认延迟为5秒钟，用户可以通过移动鼠标或键盘来打断自动选择并进行手动选择。

## 打包过程

打包过程包括以下步骤：

1. **清理**：删除之前的构建文件和临时目录
2. **创建资源**：生成图标、启动脚本等
3. **收集数据文件**：收集配置文件、模板等静态资源
4. **创建PyInstaller规范**：生成打包配置
5. **执行打包**：调用PyInstaller进行实际打包
6. **后处理**：修复特定平台的问题，如macOS权限等
7. **清理临时文件**：删除不必要的构建产物

## 输出文件

打包完成后，输出位于 `dist` 目录：

### macOS
- `dist/企业微信直播签到系统.app`：应用程序包
- `dist/启动企业微信直播签到系统.command`：启动脚本

### Windows
- `dist/企业微信直播签到系统/企业微信直播签到系统.exe`：应用程序(目录模式)
- 或 `dist/企业微信直播签到系统.exe`：应用程序(单文件模式)

### Linux
- `dist/企业微信直播签到系统/企业微信直播签到系统`：应用程序(目录模式)
- 或 `dist/企业微信直播签到系统`：应用程序(单文件模式)

## 启动流程

打包后的应用程序启动流程：

1. **启动器初始化**：显示启动画面和进度条
2. **环境准备**：初始化运行环境
3. **加载主模块**：导入和执行核心功能
4. **配置检查**：检查配置是否存在
5. **初始化向导**：首次运行时显示初始化向导
6. **登录界面**：进入登录界面进行身份验证
7. **主界面**：加载主界面和功能模块

## 配置文件

### 配置文件位置

系统使用以下配置文件位置：

- **默认配置目录**：`~/.wecom_live_sign_system/`
- **配置文件**：`~/.wecom_live_sign_system/config.json`
- **自定义路径**：通过初始化向导配置

### 配置结构

配置文件的主要结构：

```json
{
  "initialized": true,
  "paths": {
    "config": "/path/to/config",
    "data": "/path/to/data",
    "log": "/path/to/logs",
    "backup": "/path/to/backups"
  },
  "database": {
    "type": "sqlite",
    "path": "/path/to/data/data.db",
    "backup_path": "/path/to/backups",
    "pool_size": 5,
    "timeout": 30
  },
  "system": {
    "log_level": "INFO",
    "log_retention": 30,
    "backup_retention": 30
  },
  "corporations": [
    {
      "corpid": "企业ID",
      "name": "企业名称",
      "corpsecret": "应用Secret",
      "agentid": "应用ID",
      "status": true
    }
  ]
}
```

## 部署注意事项

### 权限问题

- **macOS**：首次运行可能需要在"系统偏好设置 > 安全性与隐私"中允许运行
- **Windows**：可能需要管理员权限或添加到防火墙例外
- **Linux**：确保有执行权限 (`chmod +x`)

### 防火墙配置

确保应用程序能够访问以下域名：
- qyapi.weixin.qq.com
- open.work.weixin.qq.com

### 企业微信IP白名单

应用程序会自动检测IP白名单问题，并提示用户在企业微信后台添加相应IP。

## 常见问题排查

### 应用无法启动

1. **检查日志**：查看日志文件了解错误详情
2. **权限问题**：确认有足够的文件系统权限
3. **防火墙设置**：检查是否被防火墙阻止
4. **缺少依赖**：可能是打包时缺少某些必要模块

### 启动后无法连接企业微信

1. **检查配置**：确认企业ID、Secret等信息正确
2. **IP白名单**：查看是否需要添加当前IP到白名单
3. **网络连接**：确认能够访问企业微信API域名

### 数据迁移

如需迁移已部署应用的数据：

1. 备份配置文件 `~/.wecom_live_sign_system/config.json`
2. 备份数据库文件 (路径见配置文件)
3. 安装新版本
4. 还原配置文件和数据库

## 手动打包详细步骤

如需手动打包，可按以下步骤进行：

```bash
# 基本打包命令
pyinstaller --name "企业微信直播签到系统" \
  --icon tools/assets/app.png \
  --windowed \
  --add-data "src/config:src/config" \
  launcher.py
  
# 添加额外的钩子和数据文件
pyinstaller --name "企业微信直播签到系统" \
  --icon tools/assets/app.png \
  --windowed \
  --additional-hooks-dir . \
  --add-data "src/config:src/config" \
  --add-data "src/resources:src/resources" \
  launcher.py
```

## 附录

### 打包脚本参数

`build.py` 支持以下命令行参数：

```
--onefile          创建单文件可执行文件
--onedir           创建目录模式可执行文件 (默认)
--windowed         创建GUI应用 (无控制台窗口)
--console          创建控制台应用
--debug            包含调试信息
--target-arch      目标架构 (auto, x86_64, arm64, universal)
--memory-level     内存优化级别 (low, medium, high)
```

### 有用的资源

- [PyInstaller 文档](https://pyinstaller.org/en/stable/)
- [企业微信API文档](https://developer.work.weixin.qq.com/document/)
- [SQLite 文档](https://www.sqlite.org/docs.html) 