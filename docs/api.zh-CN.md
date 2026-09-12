# Python API

[English](api.md) | [简体中文](api.zh-CN.md) · [首页](../README.zh-CN.md)

先完成[安装与构建](installation.zh-CN.md)。下列公开类型均可从 `chromium_rl` 导入；
返回状态采用冻结 dataclass 和 tuple。

## GameClient

```python
GameClient(
    binary=None, data_directory=None, video_driver=None, timeout=10.0, debug=False,
    synchronous=False, render_each_step=True, headless=False,
)
```

`binary` 和 `data_directory` 接受 `pathlib.Path`，默认定位可编辑源码目录下的本地构建与 `game/data`。
使用 wheel 时请显式传入两者。`video_driver` 可指定 `"x11"` 等 SDL 后端；
`timeout` 为正的有限响应超时秒数；`debug=True` 开启原生日志。

`headless=True` 要求同时设置 `synchronous=True, render_each_step=False`；
关闭逐步绘图也要求同步模式。默认客户端打开实时游戏菜单，同步模式直接开始第一关。
每个客户端由一个调用方管理，使用 `with GameClient(...) as game:` 清理进程。

| 成员 | 契约 |
| --- | --- |
| `capabilities: Capabilities` | 启动时协商得到的原生能力 |
| `snapshot() -> Snapshot` | 读取状态，不推进同步游戏 |
| `reset(seed: int) -> Snapshot` | 同进程重置第一关；种子 0..4294967295，不接受 bool |
| `step(action: Action, *, ticks: int = 1) -> StepResult` | 保持动作并执行 1..50 个完整 tick；终止时提前停止 |
| `render() -> Snapshot` | 显示当前状态而不推进；要求同步 GUI 模式 |
| `close() -> None` | 关闭并回收自己创建的进程；可重复调用 |

不调用 `reset(seed)` 时，启动保留基于时间的初始化。复现需要相同构建、平台、配置、种子和动作/tick 序列。
`deterministic` 保持 false，因为不承诺任意环境或跨平台逐位一致。

## 动作与时间

Python 公开接口使用枚举，不接受裸整数。

| 移动 | 不开火 | 开火 |
| --- | --- | --- |
| 释放移动 | `IDLE = 0` | `FIRE = 9` |
| 上 | `UP = 1` | `UP_FIRE = 10` |
| 下 | `DOWN = 2` | `DOWN_FIRE = 11` |
| 左 | `LEFT = 3` | `LEFT_FIRE = 12` |
| 右 | `RIGHT = 4` | `RIGHT_FIRE = 13` |
| 左上 | `UP_LEFT = 5` | `UP_LEFT_FIRE = 14` |
| 右上 | `UP_RIGHT = 6` | `UP_RIGHT_FIRE = 15` |
| 左下 | `DOWN_LEFT = 7` | `DOWN_LEFT_FIRE = 16` |
| 右下 | `DOWN_RIGHT = 8` | `DOWN_RIGHT_FIRE = 17` |

每个动作替换完整按键状态；重复方向视为持续按住。`IDLE` 释放按键，移动逐渐衰减。
每 tick 使用原版 50 fps 参考尺度 `speedAdj=1`，对应 0.02 秒模拟时间，逐 tick 检查碰撞。
墙钟等待不推进同步游戏。

`StepResult` 包含 `snapshot`、`actual_ticks`、累计 `episode_tick`、累计 `simulated_seconds`
和 `terminated`。`hero_dead` 或 `level_over` 终止的是**单关回合**，不代表整局任务。
接口不提供奖励、截断标志或自动重置；调用方的决策次数上限与原生终止分开处理。

## 状态与单位

| 类型／字段 | 含义 |
| --- | --- |
| `Snapshot.mode` | `game`、`menu`、`level_over`、`hero_dead` |
| `paused`、`game_frame`、`level`、`speed_adjustment` | 游戏原始值；`game_frame` 不是累计 episode tick |
| `player: PlayerState` | 位置、键盘累积量、生命计数、得分、伤害、护盾、可见性和三种弹药库存 |
| `player.position` | 世界 x/y/z，非像素；x 向右、y 向上；重置后 `(0, -3, 25)` |
| `player.keyboard_motion` | 输入累积量，非世界速度；y 方向约定不同 |
| `player.lives_counter` | 初始值为 4 的原始计数，不能由零推断终止 |
| `player.damage`、`shields` | 初始伤害 -500、护盾 500；damage 不是剩余生命值 |
| `enemies: tuple[EnemyState, ...]` | 类型、世界位置、原始速度、尺寸、伤害；没有稳定敌机 ID |
| `enemy_bullets: tuple[EnemyBulletState, ...]` | 回合内 ID、类型、位置、每 tick 位移、贴图半尺寸、原始伤害 |
| `powerups: tuple[PowerUpState, ...] \| None` | 回合内 ID、类型、位置、原始补充倍率 `power`、`next_displacement` |
| `episode_events: EpisodeEvents \| None` | 下面说明的累计事件 |
| `rng_cursor: int \| None` | RNG 诊断值，不建议作为策略输入 |

敌机原始速度不能描述所有特殊运动。敌弹贴图尺寸**不是碰撞范围**。
道具位移只预测下一次更新在水平边界截断前的位移，受阻尼、移除和拾取影响。
道具类型：0 护盾、1 超级护盾、2 修复、3/4/5 对应弹药 00/01/02。
ID 在 reset 后重新计数，列表顺序不是固定策略排序；列表可能包含屏幕外对象。
完整原始字段见[协议](protocol.zh-CN.md)。

## 回合事件

只对同一回合的快照做差，reset 会清零。

| 字段 | 含义 |
| --- | --- |
| `enemies_destroyed` | 所有来源造成的非静默受损敌机移除，不仅是弹药击杀 |
| `enemies_escaped` | 敌机经过 y < -14，每次会触发损命 |
| `lives_lost` | 实际减命次数，包括逃逸、伤害和自毁；奖励加命不会掩盖损失 |
| `pickups`、`missed_powerups` | 被消耗的道具数，以及经过 y < -12 的道具数 |
| `pickup_score`、`missed_powerup_score` | 对应路径实际增加的分数 |
| `shield_damage` | 实际吸收的护盾资源，不超过当时资源；排除自然衰减、补充和清理 |
| `projectile_damage` | 玩家弹药实际扣除的敌机 HP，排除溢出伤害 |
| `projectile_damage_fraction` | 有效伤害除以目标初始 HP 的累计值 |
| `projectile_kills` | 弹药使敌机 damage 从 <= 0 变为 > 0 的次数 |

弹药归因排除碰撞、超级炸弹和清场伤害；持续弹药可能在多个 tick 计入。
护盾损伤涵盖全部 `doDamage` 调用，并非仅敌弹来源。原生物理与计分不读取这些诊断计数；
奖励由消费项目自行定义。

## 兼容性与异常

`Capabilities` 公开 `implementation`、`upstream_version`、`live_snapshot`、`step`、`reset`、
`seed`、`headless`、`deterministic`、`render`、`render_free_steps`、`enemy_bullets`、`powerups`、
`episode_events`、`shield_damage`、`projectile_damage`。

客户端接受 schema 1 和 2。旧构建缺少道具或事件时，公开字段为 `None`，与空元组或实测零值不同。
旧事件结构中的伤害扩展字段也可缺失，三项弹药字段必须一起出现。
若原生端声明支持某能力却缺少数据，解析会失败。依赖某项能力前应检查 capability；未知新增字段可忽略。

`ValueError` 表示本地参数不合法；`RemoteError` 表示有效的原生错误响应，连接仍可用。
`ProtocolError` 表示传输失败或状态不合法，客户端会回收子进程，随后需要重建客户端。
异常包含游戏日志尾部，命令不会自动重试。更新 Python 包时应同步重建原生程序。
