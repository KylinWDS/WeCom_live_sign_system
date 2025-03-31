# LiveViewer 模型

LiveViewer 模型是一个整合了观看统计（WatchStat）、观众（LiveViewer）和签到记录（SignRecord）功能的统一模型。

## 设计目标

- 简化数据模型，减少表之间的关联查询
- 提高数据完整性和一致性
- 简化代码逻辑，统一数据访问接口
- 改进系统性能，减少多表连接操作

## 模型结构

### 基本属性

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | Integer | 主键 |
| living_id | Integer | 关联直播ID |
| userid | String | 用户ID |
| name | String | 用户名称 |
| user_source | Enum | 用户来源（内部/外部） |
| user_type | Integer | 用户类型：1-微信用户，2-企业微信用户 |
| department | String | 部门名称 |
| department_id | String | 部门ID |

### 观看信息（原 WatchStat）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| watch_time | Integer | 观看时长(秒) |
| is_comment | Integer | 是否评论(0-否,1-是) |
| is_mic | Integer | 是否连麦(0-否,1-是) |
| access_channel | String | 访问渠道 |

### 签到信息（原 SignRecord）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| is_signed | Boolean | 是否已签到 |
| sign_time | DateTime | 签到时间 |
| sign_type | String | 签到类型(自动/手动/导入) |
| sign_location | JSON | 签到地点 |

### 其他信息

| 字段名 | 类型 | 说明 |
|-------|------|------|
| invitor_userid | String | 邀请人ID |
| invitor_name | String | 邀请人名称 |
| ip | String | 用户IP |
| location | JSON | 用户地理位置 |
| device_info | JSON | 设备信息 |
| is_reward_eligible | Boolean | 是否符合奖励条件 |
| reward_amount | Float | 红包奖励金额 |
| reward_status | String | 奖励发放状态 |

## 迁移说明

迁移工具 `tools/migrate_to_new_viewer.py` 用于将旧模型的数据迁移到新模型中。迁移过程如下：

1. 从 WatchStat 模型迁移观看数据
2. 从 SignRecord 模型迁移签到数据
3. 更新直播统计数据

### 迁移命令

```bash
python tools/migrate_to_new_viewer.py [--dry-run] [--force] [--limit NUMBER] [--living-id ID]
```

参数说明：
- `--dry-run`: 模拟运行，不实际修改数据库
- `--force`: 强制执行，即使已有数据也覆盖
- `--limit`: 限制处理的记录数
- `--living-id`: 只处理特定直播ID的数据

## 使用示例

```python
from src.models.live_viewer import LiveViewer, UserSource

# 创建新的观众记录
viewer = LiveViewer(
    living_id=123,
    userid="user001",
    name="张三",
    user_source=UserSource.INTERNAL,
    user_type=2,
    department="研发部",
    department_id="1"
)

# 更新观看统计
viewer.update_watch_stats(
    watch_time=600,  # 10分钟
    is_comment=1,
    is_mic=0
)

# 记录签到
viewer.record_sign(
    sign_time=datetime.now(),
    sign_type="自动签到",
    location={"address": "公司", "latitude": 39.908, "longitude": 116.397}
)

# 检查奖励条件
is_eligible = viewer.check_reward_criteria()

# 设置奖励金额
if is_eligible:
    viewer.set_reward_amount(10.0, status="待发放")
```

## 注意事项

1. 旧的 WatchStat 和 SignRecord 模型的接口会逐步废弃
2. 代码中对 SignRecord 的引用已更新为使用 LiveViewer
3. 查询签到记录时使用 `LiveViewer.is_signed == True` 的条件
4. 开发时请使用 LiveViewer 模型提供的方法管理观看和签到数据 