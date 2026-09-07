# Python训练接口与加速设计

状态：源码导入、本地构建和只读Python客户端已完成；同步GUI的step原型已实现，阶段C部分完成。每tick仍绘图，完整更新/渲染拆分、reset/seed、奖励与无渲染加速仍待实现。该项目独立于任何课程仓库。证据见 [源码构建记录](validation/source-build.md)、[快照验证](validation/live-snapshot.md)和[同步step契约](synchronous-step.md)，原快照协议见[protocol.md](protocol.md)。

## 仓库布局（拟建）

| 路径 | 职责 |
|---|---|
| `game/` | 上游发布源码和运行资源，保留许可与构建方式 |
| `game/UPSTREAM.md`、`game/LOCAL_CHANGES.md` | 来源摘要、发行补丁、本地修改与行为差异 |
| `game/patches/` | 发行补丁及其摘要、来源、已应用状态 |
| `game/src/rl/` | 同步驱动、状态导出和进程协议 |
| `chromium_rl/`、`pyproject.toml` | 类型化Python客户端、观察编码、Gymnasium包装 |
| `scripts/` | 本仓库独立构建和性能测量工具 |
| `examples/`、`tests/` | 独立使用示例和接口回归检查 |
| `build/`、`artifacts/` | 忽略提交的构建、日志与模型产物 |

上游基准为0.9.16.1归档，SHA512：

```text
1d202c0704e16b31d93c552ae6cfc17caf1182a9ec80730a981cd99c8ca8cb64d4e6e838691aa86e17ea23b7c2c0b1e7b1f4dab91bbc6129f9bf86801f2b27c8
```

导入时重新核验并记录下载URL及Arch的`use_fabs_for_floats.patch`、`ax_check_gl_m4.patch`。先独立导入上游，再记录补丁与改造，保留历史可追踪性。修改文件说明内容和日期；不安装到系统路径或覆盖原游戏。

## 架构与协议

每个环境一个C++子进程，Python经标准输入输出交换逐行JSON，stdout只用于协议，日志写stderr。不先引入socket服务、共享内存或进程内多实例绑定。

命令：`hello/reset/step/snapshot/render/close`。所有消息有协议版本、请求ID；一次仅一个请求在途。hello报告构建与能力，未实现的headless能力不可标真。step不可自动重试；错误、超时、EOF和用户关闭窗口引发明确异常，不伪造经验。客户端只清理自己创建的进程。

先实现类型化原始状态客户端，再提供Gymnasium形式：

```python
# 目标API示意，当前不能运行
from chromium_rl import ChromiumEnv

with ChromiumEnv(render_mode="human") as env:
    observation, info = env.reset(seed=7)
    observation, reward, terminated, truncated, info = env.step(0)
```

不依赖调用者工作目录寻找游戏与资源，资源位置由包/构建产物确定并允许显式覆盖。公开Python接口有返回类型；依赖由本仓库pyproject管理，消费者可以安装本项目，不依赖开发者的本地虚拟环境。

## 动作与时间

首版候选为9种方向（无输入、上、下、左、右、左上、右上、左下、右下）×开火开关，共18项，编号`movement_index + 9 * fire`。

动作设置完整按键状态。提取共享键盘控制计算，保留累积、0.7衰减、整数化和原斜移行为；不直接设置位置，不把释放等同于清零速度。边沿增量只触发一次；OS重复事件不进入训练路径，确定性控制模型与人工控制的差异必须记录。

原更新混在`MainGL::drawGameGL()`中，需拆出逻辑更新，审查其他绘图和过场的副作用。边界为：上次快照→动作→完整逻辑更新→事件与快照。首次`action_repeat=1`，后续可在C++内重复多个tick，但每tick仍做碰撞检测并在结束时立即停下。

加速是正式训练前的必验能力：

- 基准逻辑步暂定0.02秒，固定`speedAdj=1`，需核对50fps基准轨迹；它不是可随意放大的统一物理dt。
- 训练移除sleep、墙钟FPS校准和实时限速，关闭音频与渲染；GUI独立限速，不改变游戏逻辑。
- 单调episode tick与关卡内部gameFrame分开；返回实际tick数及模拟时间。
- action repeat减少决策频率，不是免费加速；固定进模型契约。默认折扣按决策步定义；更改计数语义时同时审查奖励、探索和更新频率。
- 不以放大dt跨过中间碰撞冒充等价加速。若需大外层步长，优先保留内部子步。
- 真正无GL上下文是独立验收；隐藏窗口不能冒充真正headless。
- 比较同seed同动作的慢放、快跑、无渲染轨迹。每步间加墙钟等待、重复render不得改变状态、随机游标或事件。
- 分别测量纯C++、Python采样和带网络更新吞吐，报告ticks/s、decisions/s、updates/s及实时倍率。首个纯采样目标为10倍实时（500tick/s），未测量，不能视为承诺。

## 状态、奖励与结束

原始快照包含episode/tick、玩家位置与控制状态、生命/伤害/护盾/弹药/冷却、对象列表、得分、阶段和本步事件。位置是世界坐标，明确轴与单位；对象ID稳定，不暴露裸指针。敌机vel是否代表真实运动需逐类型核对。

事件在发生处记账，不能仅根据生命净差推断损命次数。Python负责奖励，初版以得分增量为可核对基准，其他奖励后续单因素比较。

Gym包装把可变长对象列表编码为固定槽位、掩码与稳定排序；字段、K值、归一化和溢出统计调查后冻结，不把原始列表直接送入DQN。诊断字段与策略实际输入明确分开，结构化策略不宣称纯视觉策略。

自然失败依据实际内部阶段/生命语义；单关模式可在过关终止，整局模式不可将LevelOver当作最终通关。整局跨关、复活和最终完成判据未实现前拒绝整局模式。外部tick预算为truncated，保留结束观察，无隐式auto-reset。

reset先设置关卡与难度，再初始化；重置对象、控制内部速度、事件、ID、冷却、过场和所有随机状态（含随机表/游标）。禁写用户高分和存档。进程内reset与新进程重开对照，先限定同构建的复现性。

## 里程碑

1. 来源和许可齐全的源码导入、独立构建、原生GUI启动。
2. 类型化只读状态与Python进程协议。
3. 同步动作、逻辑单步、GUI展示且重复render不改状态。
4. reset、seed、事件、关卡与错误处理验证。
5. 固定观察、Gym接口和加速轨迹/吞吐验收。
6. 独立示例训练、冻结评估、GUI回放，随后验证ONNX输出与预处理契约。

每阶段提供可独立复现的命令。源码阅读、编译成功、窗口启动、接口正确、训练成功分别记录；不将文档中的接口视为实现。
