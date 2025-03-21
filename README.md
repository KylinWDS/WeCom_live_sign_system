# 企业微信直播邀请签到系统

## 项目简介
这是一个基于 Python3 开发的企业微信直播邀请签到系统，用于管理和统计企业微信直播相关的数据。系统提供图形化界面，支持直播预约、签到管理、数据统计等功能。

## 系统要求
- Python 3.x
- SQLite 数据库
- 企业微信开发者账号
- 操作系统：Windows/Linux/MacOS

## 功能特性

### 1. 用户界面
- 支持系统颜色、明亮、暗色三种主题切换
- 美观的图形化界面
- 响应式设计
- 用户友好的操作体验

### 2. 企业微信集成
- 企业信息配置
- 应用授权管理
- Token 自动获取与刷新
- IP 白名单管理
- 接口调用监控

### 3. 直播管理
- 直播预约创建
- 直播列表管理
- 直播详情查看
- 直播数据统计
- 直播状态监控
- 直播取消功能

### 4. 签到管理
- 签到信息导入
- 签到数据统计
- 签到记录导出
- 签到报表生成
- 签到数据分析

### 5. 用户权限
- 超级管理员（root-admin）
- 企业微信管理员
- 普通用户
- 权限分级管理
- 操作日志记录

### 6. 数据管理
- 数据导入导出
- 数据备份恢复
- 数据清理
- 数据统计报表
- 数据可视化

## 安装说明

### 1. 克隆项目
```bash
git clone [项目地址]
cd WeCom_live_sign_system
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置系统
- 复制 `config.json.example` 为 `config.json`
- 修改配置文件中的相关参数
- 配置数据库连接信息
- 设置日志路径

### 4. 初始化系统
```bash
python init_system.py
```

## 使用说明
详细的使用说明请参考 `documents` 目录下的文档：
- [系统配置指南](documents/config/README.md)
- [API 接口文档](documents/api/README.md)
- [用户界面说明](documents/ui/README.md)
- [数据模型说明](documents/models/README.md)
- [工具类说明](documents/utils/README.md)
- [核心功能说明](documents/core/README.md)

## 开发说明

### 1. 项目结构
```
WeCom_live_sign_system/
├── src/                # 源代码目录
│   ├── api/           # API 接口
│   ├── core/          # 核心功能
│   ├── models/        # 数据模型
│   ├── ui/            # 用户界面
│   └── utils/         # 工具类
├── documents/         # 文档目录
├── tests/            # 测试目录
├── data/             # 数据目录
├── logs/             # 日志目录
└── config/           # 配置目录
```

### 2. 开发环境配置
- Python 3.x
- PyQt6
- SQLite3
- 其他依赖见 requirements.txt

### 3. 代码规范
- 遵循 PEP 8 规范
- 使用类型注解
- 编写详细注释
- 保持代码简洁

### 4. 测试说明
- 单元测试
- 集成测试
- 功能测试
- 性能测试

## 注意事项
1. 首次使用需要配置企业微信相关信息
2. 请确保网络环境稳定
3. 定期备份数据库文件
4. 注意保护企业微信的 Secret 信息
5. 及时更新 IP 白名单
6. 定期清理日志文件
7. 注意数据安全
8. 遵守相关法律法规

## 常见问题
1. 如何获取企业微信配置信息？
2. 如何处理 IP 白名单问题？
3. 如何备份和恢复数据？
4. 如何更新系统？
5. 如何处理 Token 过期问题？

## 技术支持
- 提交 Issue
- 联系技术支持
- 查看常见问题
- 参考文档

## 更新日志
### v0.0.1 (2025-03-13)
- 初始版本发布
- 基础功能实现
- 文档完善

## 许可证
MIT License

## 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 致谢
感谢所有贡献者的付出！




