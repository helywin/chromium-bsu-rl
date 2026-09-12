# Chromium B.S.U. for RL

[English](README.md) | **简体中文**

[CI：仅推送 tag 时运行](.github/workflows/ci.yml)

用 Python 控制 Chromium B.S.U. 飞行射击游戏：不依赖显示服务执行带种子的模拟步进，
读取类型化游戏状态，也可以在原生游戏窗口中观察同一个运行时。

这是基于 **Chromium B.S.U. 0.9.16.1** 的独立第三方改造项目，与上游官方发行无关。
仓库提供 C++ 游戏运行时和无运行时 Python 依赖的客户端，供实验、工具和其他项目集成。

## 当前能力

| 能力 | 状态 |
| --- | --- |
| 原生游戏窗口与只读实时快照 | 已实现 |
| 18 种移动／开火动作，每次执行 1–50 tick | 已实现；每 tick 对应 0.02 秒模拟时间 |
| 同一进程内带种子重置 | 已实现；仅第一关 |
| 真正无窗口运行 | 已实现；不创建显示服务连接、窗口或 GL 上下文 |
| 按需绘图 | 已实现；使用依赖显示服务的运行模式 |
| 玩家、敌机、敌弹、道具的类型化状态 | 已实现 |
| 战斗、伤害、拾取和损命累计事件 | 已实现 |
| Gymnasium 环境、奖励和观察编码 | 尚未实现 |
| 整局任务、已训练策略与学习性能基准 | 暂未提供 |

项目处于 **Alpha 阶段**。种子重复性限定于相同原生构建、平台和配置。
原始快照是可变长的游戏内部状态，并非完整的策略观察。
将字段用于学习输入或奖励前，请阅读 [API 契约](docs/api.zh-CN.md)。

## 快速开始

源码使用流程面向 **Linux 和 Python 3.11+**。Windows 用户请在 WSL2 内执行下面的命令，
或使用后面的 Docker 方式。本构建流程暂不支持原生 Windows 和 macOS。

先准备[构建依赖](docs/installation.zh-CN.md#构建依赖)，然后执行：

```bash
git clone https://github.com/helywin/chromium-bsu-rl.git
cd chromium-bsu-rl
python3 -m venv .venv
.venv/bin/python -m pip install -e .
bash scripts/build_chromium_rl.sh
.venv/bin/python examples/headless_rollout.py --seed 7
```

示例执行有步数上限的固定动作序列，输出 JSON，包含原生实现版本、模拟 tick 数、
最终得分和累计事件。到达第一关终止状态或决策次数上限时退出；它不训练策略。
成功运行返回退出码 0，并清理自己创建的游戏进程。

构建脚本只检查已有依赖并向 `build/` 写入产物，不安装系统软件。
每个 Python 客户端都有独立的临时配置和高分目录。

### Python 调用

```python
from chromium_rl import Action, GameClient

with GameClient(synchronous=True, render_each_step=False, headless=True) as game:
    initial = game.reset(seed=7)
    for _ in range(200):
        result = game.step(Action.RIGHT_FIRE, ticks=5)
        state = result.snapshot
        print(result.episode_tick, state.player.score, state.episode_events)
        if result.terminated:
            break
```

需要复现时，先调用 `reset(seed)`。终止后的游戏保持冻结，直到显式重置。
动作表示完整按键状态；`IDLE` 释放按键，保留原版移动衰减，不会立即停止飞机。

### 打开原生游戏窗口

需要可用的桌面显示服务和 OpenGL：

```bash
bash scripts/run_gui.sh                         # 从菜单进入，人工游玩
.venv/bin/python examples/watch_snapshot.py     # 游玩时读取状态
.venv/bin/python examples/watch_steps.py        # 观察固定种子的动作序列
.venv/bin/python examples/watch_enemy_bullets.py
```

偶尔查看画面时，可使用 `GameClient(synchronous=True, render_each_step=False)`，
再调用 `game.render()`。这种模式仍创建 SDL/GL 上下文。
使用 `headless=True` 创建的客户端不能中途打开窗口，回放需要另建 GUI 客户端。
详见[运行模式与故障排查](docs/installation.zh-CN.md)。

### Docker 运行

在克隆后的仓库目录中，使用 Linux 容器引擎执行：

```bash
docker build -t chromium-bsu-rl:local .
docker run --rm --init --network none chromium-bsu-rl:local
```

开发镜像包含源码、原生运行时和 Python 虚拟环境，默认以非 root 用户运行无窗口示例。
构建需要联网，示例运行不需要联网，也不依赖预先发布的项目镜像。
详见[容器使用](docs/installation.zh-CN.md#docker)。

## 集成到其他项目

支持可编辑安装、固定提交的 Git 子模块以及本地构建 Python wheel。
wheel **只包含 Python 客户端**，需要通过 `binary=Path(...)` 和
`data_directory=Path(...)` 提供独立构建的游戏及资源。安装 Python 包不会自动编译游戏。

完整命令见[安装与打包](docs/installation.zh-CN.md#集成到其他项目)。有复现需求时请固定仓库提交；
Python 包版本、协议版本、快照版本和游戏行为版本各有用途。

## 文档与开发

| 指南 | English | 简体中文 |
| --- | --- | --- |
| 安装、Docker、打包与排错 | [Read](docs/installation.md) | [阅读](docs/installation.zh-CN.md) |
| Python 接口、动作与状态语义 | [Read](docs/api.md) | [阅读](docs/api.zh-CN.md) |
| 面向其他语言的 JSON-lines 协议 | [Read](docs/protocol.md) | [阅读](docs/protocol.zh-CN.md) |
| 架构与后续方向 | [Read](docs/architecture.md) | [阅读](docs/architecture.zh-CN.md) |
| 无窗口性能与 GPU 加速 | [Read](docs/performance.md) | [阅读](docs/performance.zh-CN.md) |
| 贡献与验证流程 | [Read](CONTRIBUTING.md) | [阅读](CONTRIBUTING.md#简体中文) |

[文档索引与验证记录](docs/README.md) · [变更记录](CHANGELOG.md) ·
[反馈问题](https://github.com/helywin/chromium-bsu-rl/issues) · [安全问题](SECURITY.md)

欢迎中文和英文贡献。CI 仅在推送 tag 时触发，分别执行 Python 检查、原生无显示测试和 Xvfb 下的 SDL/OpenGL 测试。
Xvfb 验证显示路径，不等同于真实桌面人工验收或原生 Wayland 验收。普通分支 push 和 PR 不启动 CI，开发期间使用本地检查。

## 上游与许可

Chromium B.S.U. 由[上游作者](game/AUTHORS)创作。游戏保留
[Clarified Artistic License](game/COPYING)，音效保留
[MIT/Expat 许可](game/data/wav/license.txt)。本仓库原创新增部分默认采用
Clarified Artistic License，各文件已有的第三方声明继续有效。
本项目不替换上游许可证，也不代表上游官方。

[许可范围](LICENSE.md) · [来源记录](game/UPSTREAM.md) ·
[游戏本地改动](game/LOCAL_CHANGES.md) · [上游项目](https://chromium-bsu.sourceforge.net/)
