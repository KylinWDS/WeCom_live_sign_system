# 企业微信直播签到系统

## 项目概述
企业微信直播签到系统是一个用于管理和记录企业微信直播观看情况的应用程序。该系统可以自动同步企业微信的直播数据，记录员工的观看行为，生成签到报表，并提供数据分析功能。

## 功能特性
- 企业微信API集成
- 自动同步直播数据
- 用户观看行为记录
- 签到统计和报表
- 数据导出和分析
- 多主题UI界面
- 自定义配置选项
- 实时数据更新
- 批量数据处理
- 高效并发处理

## 系统要求
- Python 3.8 或更高版本
- 企业微信管理员权限
- 操作系统：Windows/macOS/Linux

## 快速开始

### 安装步骤
1. 克隆项目仓库
   ```bash
   git clone https://github.com/yourusername/wecom_live_sign_system.git
   cd wecom_live_sign_system
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 配置企业微信信息
   - 复制 `config/config.example.json` 到 `config/config.json`
   - 编辑 `config.json` 填入您的企业微信信息

4. 启动程序
   ```bash
   python src/launcher.py
   ```

## 文档
详细的文档可以在 [documents/index.md](documents/index.md) 查看，包括：

### 用户文档
- [用户手册](documents/user_manual.md) - 系统全面的用户使用指南
- [打包与部署指南](documents/deployment.md) - 系统的打包和部署说明

### 开发文档
**注意**: 详细的开发文档仅对内部开发人员开放，请联系项目管理员获取访问权限。

## 贡献指南
我们欢迎所有形式的贡献，无论是新功能、文档改进还是问题修复。请遵循以下步骤：

1. Fork这个仓库
2. 创建您的功能分支
3. 提交您的更改
4. 推送到分支
5. 打开一个Pull Request

## 更新记录

### 版本 1.1.0
- 改进用户体验
- 提升系统性能
- 增强API功能
- 优化多线程处理
- 完善错误处理机制
- 修复已知问题

### 版本 1.0.0
- 初始版本发布
- 实现基本功能
- 完成企业微信API集成
- 建立基础文档体系

## 许可证
本项目采用专有许可证 - 使用前请联系项目维护者获取授权

## 联系方式
- 项目维护者：管理员 - admin@example.com
- 技术支持：support@example.com

## 安全说明
本系统包含敏感业务逻辑和接口，未经授权不得用于商业用途。所有代码和文档均为保密资料，请勿外传。如发现安全问题，请立即联系项目维护者。

## 致谢
感谢所有贡献者的付出！




