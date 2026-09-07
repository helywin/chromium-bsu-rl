# Chromium B.S.U. for RL

A standalone project for adapting Chromium B.S.U. into a deterministic, accelerated reinforcement-learning environment with Python interfaces and native GUI playback.

**Status: typed snapshots and opt-in synchronous GUI steps available.** `GameClient(synchronous=True)` runs one first-level episode under Python control. Reset/seed, render-free accelerated simulation and trained models are not implemented. This is not an official Chromium B.S.U. release.

## 项目目标

- C++运行游戏，Python通过独立子进程调用`reset/step`，读取状态与事件。
- 固定逻辑时间步，无渲染、不限速采样；GUI回放与训练共享游戏逻辑。
- 保留键盘移动模型，提供明确的动作、观察、奖励和终止契约。
- 可独立构建和使用，不依赖课程仓库、个人目录或Isaac Lab。

详见 [接口与加速设计方案](docs/design.md)。上述训练能力均待实现。

## 构建与运行（Linux）

需要已有C/C++编译工具、Autoconf/Automake、gettext（含autopoint）、pkg-config，以及SDL2、SDL2_image、OpenGL/GLU、FTGL、Fontconfig、OpenAL、freealut、json-c（>=0.15）的开发文件。构建脚本会检查依赖，不自动安装或升级软件。

```bash
bash scripts/build_chromium_rl.sh
bash scripts/run_gui.sh
```

默认4个编译任务，可用`CHROMIUM_RL_BUILD_JOBS=2`调整。构建仅在本仓库`build/`进行，不执行sudo或系统安装。每次保留独立`build/work.*`供诊断，重复构建会占用额外磁盘空间。

请通过启动脚本运行：它使用640×480窗口、关闭声音，并将配置与高分隔离在`build/state/`，不会重设HOME。不带这些环境变量直接运行内部二进制仍会使用上游用户目录规则。菜单中进入游戏，支持方向键和组合斜移；字母快捷键可能受输入法影响。

本次窗口验证使用`SDL_VIDEODRIVER=x11 bash scripts/run_gui.sh`（Wayland桌面上的XWayland路径）。默认原生Wayland路径尚未验收，不宣称无界面模式已实现。详见 [构建与启动记录](docs/validation/source-build.md)。

## Python实时状态（已实现，尚非训练环境）

使用你自己的Python 3.11+虚拟环境。以下在独立仓库根目录执行，`<venv>`替换为该虚拟环境路径；先完成上面的本地构建：

```bash
<venv>/bin/python -m pip install -e .
<venv>/bin/python examples/watch_snapshot.py
```

脚本会打开游戏；你从菜单进入并操作飞机，终端每0.5秒显示坐标、生命计数、得分和敌机数。Python读取的是游戏内部数据，不是截图识别，也不依赖输入法。数据接口、单位与边界见 [protocol.md](docs/protocol.md)。

```python
from chromium_rl import GameClient, Snapshot

with GameClient() as game:
    state: Snapshot = game.snapshot()
    print(state.player.position, state.player.score)
```

IDE能识别`Snapshot/PlayerState/EnemyState`字段。每个客户端使用单独的临时配置目录，关闭时清理。当前游戏仍按实时循环运行；读取间隔不等于环境步长，不能把相邻两次读取直接当作可靠DQN经验。

开发者检查（不是学习者练习）：

```bash
<venv>/bin/python -m unittest discover -s tests -p 'test_*.py' -v
# 显式允许打开GUI的集成检查：
RUN_CHROMIUM_GUI_TESTS=1 <venv>/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

## Python同步动作（GUI原型）

```bash
<venv>/bin/python examples/watch_steps.py
```

无需从菜单开始，也无需模拟键盘。脚本演示移动、开火、释放与停顿，退出时关闭自己创建的窗口。

```python
from chromium_rl import Action, GameClient, StepResult

with GameClient(synchronous=True) as game:
    result: StepResult = game.step(Action.RIGHT_FIRE, ticks=1)
    print(result.snapshot.player.position, result.episode_tick)
```

每个内部tick采用原版50fps参考尺度（`speedAdj=1`，标称0.02秒），执行完整更新和绘图。没有step就不推进；连续相同方向视为保持按下，IDLE为释放并衰减，不是瞬间清零。每条指令最多50tick，到死亡或本关完成立即停下。

这是**仅第一关的同步GUI原型**，不是完整Gym环境。仍需要显示服务/GL；绘图与逻辑尚未拆开，无额外render命令，无确定性seed/reset、奖励、子弹快照或整局任务。重新创建客户端才能开新一局。见[同步协议与边界](docs/synchronous-step.md)。

## 获取仓库

```bash
git clone https://github.com/helywin/chromium-bsu-rl.git
```

其他项目也可以使用Git子模块引用一个固定提交：

```bash
git submodule add https://github.com/helywin/chromium-bsu-rl.git third_party/chromium-bsu-rl
# 已经引用本项目的仓库，在克隆后运行：
git submodule update --init --recursive
```

## 上游与许可

基于 [Chromium B.S.U.](https://chromium-bsu.sourceforge.net/) 0.9.16.1发布源码，保留上游Clarified Artistic License、版权声明及音效的MIT/Expat许可。来源摘要见 [UPSTREAM.md](game/UPSTREAM.md)，修改见 [LOCAL_CHANGES.md](game/LOCAL_CHANGES.md)。不对上游代码或资源重新套用其他许可证。

新增脚本与文档许可及第三方边界见 [LICENSE.md](LICENSE.md)。
