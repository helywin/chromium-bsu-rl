# 进程协议 v1 与快照 schema v2

[English](protocol.md) | [简体中文](protocol.zh-CN.md) · [Python API](api.zh-CN.md)

此协议可由其他语言独立实现。默认实时模式接受人工操作；同步模式提供 step/reset，
有显示上下文时还提供 render。所有模式均导出敌弹、道具和累计事件，不提供奖励或稳定敌机 ID。

## 传输与命令

Linux/POSIX 子进程通过标准输入输出交换 UTF-8 JSON，每行一个对象。
启动前设置 `CHROMIUM_BSU_RL_PROTOCOL=1`、独立且短于 180 字节的
`CHROMIUM_BSU_RL_STATE_DIR`，以及 `CHROMIUM_BSU_DATA` 和 `CHROMIUM_BSU_SCORE`。
通常使用 `GameClient`，它负责环境隔离。旧游戏日志重定向到 stderr，专用 stdout 描述符传输响应。

请求包含 `protocol_version: 1`、严格递增的正 int32 `request_id`、字符串 `command`。
一个客户端同一时间只发送一个请求；上限为请求 8192 字节、响应 1 MiB，JSON 嵌套受限。
成功响应含 `ok: true` 与 `result`；失败响应含 `ok: false` 与 `error.code/message`。
客户端应校验版本和请求 ID。超限响应关闭连接，不截断快照伪造数据。

所有模式支持 `hello`、`snapshot`、`close`。设置 `CHROMIUM_BSU_RL_SYNCHRONOUS=1`
后支持 `step`、`reset`；非 headless 同步模式支持 `render`。

```json
{"protocol_version":1,"request_id":1,"command":"hello"}
{"protocol_version":1,"request_id":2,"command":"reset","seed":7}
{"protocol_version":1,"request_id":3,"command":"step","action":13,"ticks":5}
{"protocol_version":1,"request_id":4,"command":"close"}
```

逐条发送并读取对应响应。`action` 为 0..17 的完整按键状态，`ticks` 为 1..50 整数，均不接受布尔值。
编号见[动作表](api.zh-CN.md#动作与时间)。step 返回 snapshot、actual_ticks、累计 episode_tick、
累计 simulated_seconds 和 terminated。每 tick 为 0.02 秒模拟时间。
`hero_dead` 或 `level_over` 终止第一关回合，此后 step 返回 `episode_ended`，直到 reset。

错误代码包括 `invalid_json`、`invalid_request`、`invalid_seed`、`invalid_action`、
`unsupported_command`、`request_too_large`。无法识别请求 ID 时响应可能为 null，严格客户端应关闭。
传输失败后不要重试结果不确定的 step。EOF 关闭受控游戏；Python 超时或解析失败只回收自己创建的进程。

## hello 与版本

当前实现为 `chromium-bsu-rl/seeded-reset-v3`，上游版本为 `0.9.16.1`。
包版本、协议版本 1、快照 schema 2、行为版本分别管理。
能力字段包括 live_snapshot、step、reset、seed、headless、deterministic、render、
render_free_steps、enemy_bullets、powerups、episode_events、shield_damage、projectile_damage。

能力按当前模式报告，headless 表示所选模式。`deterministic=false` 不表示不能重复种子，
而是没有跨构建、跨平台的通用确定性保证。使用能力前应检查声明，不能只猜测版本。

## 快照字段

快照在主线程完整循环边界复制，序列化期间不更新游戏。
实时 snapshot 不等于推进一个 tick；菜单或暂停状态只适合诊断。

| 字段 | 含义 |
| --- | --- |
| `schema_version` | 当前为 2，原始快照版本，不是策略观察版本 |
| `mode` | game/menu/level_over/hero_dead |
| `paused`, `game_frame`, `level`, `speed_adjustment` | 原始全局状态；game_frame 在关卡变化时重置 |
| `player` | position、keyboard_motion、lives_counter、score、damage、shields、visible、ammo_stock |
| `enemies` | type、position、raw_velocity、size、damage；只读遍历，无稳定 ID |
| `enemy_bullets` | id、type、position、velocity_per_tick、sprite_half_size、damage |
| `rng_cursor` | 随机表游标，仅供诊断 |
| `powerups` | id、type、position、power、next_displacement |
| `episode_events` | 下文累计事件对象 |

位置为世界坐标，x 向右、y 向上，玩家重置位置为 `(0,-3,25)`。
键盘量不是世界速度，y 约定不同；伤害初始 -500，不能解释为剩余 HP；生命计数初始 4，不能由零判断结束。
敌机速度不概括全部特殊运动；敌弹速度为每 tick 位移，贴图半尺寸不是碰撞边界。

敌弹和道具 ID 在同一回合内稳定且为正数，重置后重新开始。数组可以包含屏幕外对象，
顺序不能作为策略排序。道具类型 0 护盾、1 超级护盾、2 修复、3/4/5 弹药 00/01/02。
power 是补充倍率，非得分；next_displacement 是下次更新在水平边界截断前的二维位移，
含阻尼 `1-speedAdj+speedAdj*0.982` 与纵向滚动，不承诺多 tick 恒定速度。

## 带种子重置

`reset` 要求整数 seed 0..4294967295，不接受 bool、浮点数、字符串或 null。
无效请求不改变游戏。游戏在同一进程内重建回合对象，在 GUI 模式保留 SDL/GL 上下文，
重建随机表、控制累积量、第一关状态、玩家资源、武器状态、对象池、计数和 ID。
episode_tick 归零；初始快照不推进模拟，需要立即更新画面时另调 render。

可在游戏中途或终止后重置，调用方负责保存此前的终止观察。
初始 mode 为 game、不暂停、第一关、得分 0、生命计数 4、伤害 -500、护盾 500、弹药库存空。
同种子/动作/构建/平台/配置的轨迹可重复，但 libc RNG 与浮点行为随平台变化；
不同种子也不保证序列不同，例如 libc 可能让 0 和 1 等价。未显式 reset 时仍按时间初始化。

## 真正无显示模式

设置 `CHROMIUM_BSU_RL_HEADLESS=1` 并启用协议与同步模式。
不初始化 SDL 视频、窗口、GL 上下文、纹理/字体或音频，仍执行游戏构造、物理、碰撞和相关视觉状态更新。
不需要 Xvfb，但二进制仍链接常规 GUI 库。
hello 报告 headless=true、render=false、step/reset/render_free_steps=true。
render 请求失败且不推进；回放应另建 GUI 进程。同步命令循环通过 stdin 轮询唤醒，没有旧的每轮 2 ms 固定睡眠。

## 累计事件与伤害归因

hello 对应能力为 true 时，必须存在相应字段。计数非负，基础计数为 int64，分数与伤害为有限数值。
reset 清零；snapshot/render 不改变它们。只在同一回合内做差，不跨 reset 相减。

| 字段 | 语义 |
| --- | --- |
| enemies_destroyed | 非静默受损敌机移除，包含碰撞和连锁爆炸；排除逃逸、reset 和普通清理 |
| enemies_escaped | 敌机经过 y < -14 |
| lives_lost | 实际 lives-- 次数，包括逃逸、受损、自毁 |
| pickups | 玩家碰撞消耗道具，包括资源已满时的拾取 |
| missed_powerups | 道具经过 y < -12 后移除 |
| pickup_score / missed_powerup_score | 对应路径实际增加的原始分数 |
| shield_damage | doDamage 中吸收的护盾资源，最多为当前资源；不含被动衰减、补充和清理，非仅敌弹来源 |
| projectile_damage | 玩家弹药实际扣除的敌机 HP，不含溢出伤害 |
| projectile_damage_fraction | 有效伤害除以各目标初始 HP 的累计值 |
| projectile_kills | 弹药使敌机 damage 从 <= 0 转为 > 0 的次数 |

弹药归因排除碰撞、超级炸弹和清场，持续弹药可能逐 tick 计入。
这些字段只做测量，物理、计分、随机数不读取它们。
Python 公开 `PowerUpState` 与 `EpisodeEvents`；旧构建缺失的可选字段返回 None，
不能当作零值。广告能力与字段不一致时解析失败。详见 [API 兼容规则](api.zh-CN.md#兼容性与异常)。
