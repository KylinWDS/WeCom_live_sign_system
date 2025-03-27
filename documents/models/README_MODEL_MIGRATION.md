# 数据模型重构与迁移

## 背景

为了优化系统架构，提高数据一致性和查询性能，我们对系统中的数据模型进行了重构，主要是将 `WatchStat`、`LiveViewer` 和 `SignRecord` 三个相关联的模型合并为一个统一的 `LiveViewer` 模型。

## 重构目标

1. 减少表之间的关联查询，提高查询效率
2. 统一数据访问接口，简化代码逻辑
3. 提高数据完整性和一致性
4. 增强模型的功能，如增加奖励机制支持

## 实施内容

### 1. 模型合并

将三个模型的字段和功能合并到新的 `LiveViewer` 模型中：
- 基本用户信息 (userid, name, user_type, department)
- 观看统计 (watch_time, is_comment, is_mic)
- 签到记录 (is_signed, sign_time, sign_type)
- 奖励机制 (is_reward_eligible, reward_amount, reward_status)

### 2. 代码更新

- 更新关键文件中的模型引用
  - `src/core/database.py`
  - `src/core/export_manager.py`
  - `src/core/stats_manager.py`
  - 其他使用旧模型的文件

### 3. 数据迁移工具

创建了 `tools/migrate_to_new_viewer.py` 用于将旧模型的数据迁移到新模型中：
- 从 WatchStat 迁移观看数据
- 从 SignRecord 迁移签到数据 
- 更新直播统计数据

### 4. 引用检查工具

创建了 `tools/check_model_references.py` 用于检查代码中对废弃模型的引用：
- 扫描整个代码库
- 识别需要更新的引用
- 提供修改建议
- 支持简单引用的自动修复

## 使用指南

### 数据迁移

```bash
# 模拟迁移，不实际修改数据库
python tools/migrate_to_new_viewer.py --dry-run

# 强制执行迁移
python tools/migrate_to_new_viewer.py --force

# 只迁移特定直播ID的数据
python tools/migrate_to_new_viewer.py --living-id 123

# 限制处理记录数
python tools/migrate_to_new_viewer.py --limit 1000
```

### 引用检查

```bash
# 检查src目录下的所有Python文件
python tools/check_model_references.py --path src

# 自动修复简单引用问题
python tools/check_model_references.py --path src --fix

# 显示详细信息
python tools/check_model_references.py --path src --verbose
```

## 注意事项

1. 旧的 `WatchStat` 和 `SignRecord` 模型将在后续版本中移除，请及时更新代码
2. 查询签到记录时使用 `LiveViewer.is_signed == True` 作为过滤条件
3. 如果您的代码中有自定义查询，请参考 `documents/models/LiveViewer.md` 了解字段映射关系
4. 在迁移过程中可能存在一些复杂的引用难以自动处理，请检查工具输出的建议并手动修改

## 遗留问题

以下文件中的模型引用尚待处理：
- `src/ui/pages/sign_page.py`
- `src/ui/pages/home_page.py`
- `src/ui/pages/live_list_page.py`
- `src/core/sign_import_manager.py`

## 后续计划

1. 完成所有代码中对旧模型的引用更新
2. 从代码库中移除废弃的模型文件
3. 优化新模型的查询性能
4. 添加更完善的单元测试 