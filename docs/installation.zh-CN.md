# 安装与故障排查

[English](installation.md) | [简体中文](installation.zh-CN.md) · [首页](../README.zh-CN.md)

## 支持的使用方式

需要 Linux/POSIX、Bash、Python 3.11+ 和 C++ 工具链。参考容器与 CI 使用 Ubuntu 24.04；
其他 Linux 发行版需要对应的开发包。Windows 用户可在 WSL2 内构建，或运行 Linux Docker 镜像。
客户端使用 POSIX 管道，原生 Windows、macOS 和其他 CPU 架构暂未验证。

## 构建依赖

工具：`g++`、`make`、Autoconf、Automake、`autopoint`、gettext（`msgfmt`）、`pkg-config`。
开发库：SDL2、SDL2_image、OpenGL、GLU、FTGL、Fontconfig、OpenAL、freealut 和
**json-c >= 0.15**。无窗口模式仍链接这些库。

以下是由你管理的 Ubuntu 24.04 主机所需的软件包。命令会安装系统依赖，构建脚本不会自动执行它们。
如需将依赖限制在容器内，请使用后面的 Docker 方式。

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends \
  build-essential autoconf automake autopoint gettext pkg-config \
  libsdl2-dev libsdl2-image-dev libgl1-mesa-dev libglu1-mesa-dev libftgl-dev \
  libfontconfig1-dev libopenal-dev libalut-dev libjson-c-dev \
  python3 python3-venv ca-certificates fonts-dejavu-core
```

虚拟 X 显示测试另需 `xvfb`、`xauth` 和 `libgl1-mesa-dri`。真正无显示测试不需要显示服务。

## 本地构建

```bash
git clone https://github.com/helywin/chromium-bsu-rl.git
cd chromium-bsu-rl
python3 -m venv .venv
.venv/bin/python -m pip install -e .
bash scripts/build_chromium_rl.sh
.venv/bin/python examples/headless_rollout.py --seed 7
```

也可使用已有项目虚拟环境。默认并行编译 4 个任务，用 `CHROMIUM_RL_BUILD_JOBS=2` 调整。
Autotools 在 `build/work.*` 副本内运行，程序位于 `build/install/bin/chromium-bsu-rl`。
副本会保留供排错；确认没有构建正在使用后，可以清理旧副本。

更新原生代码或移动仓库后应重新构建，因为原生安装记录了绝对路径。
上游仍有固定长度路径缓冲区，资源与状态目录应使用短路径；客户端拒绝长度达到 180 字节的资源路径。
建议源码、二进制和客户端使用同一提交。安装 Python 包不会编译游戏。

## 运行模式

| 模式 | 创建方式 | 依赖与行为 |
| --- | --- | --- |
| 人工游玩与实时读取 | `GameClient()` | 需要显示服务和 OpenGL；实时运行，从菜单开始 |
| 每个同步 tick 绘图 | `GameClient(synchronous=True)` | 需要显示服务和 OpenGL；直接开始第一关 |
| 按需绘图 | `GameClient(synchronous=True, render_each_step=False)` | 隐藏 SDL/GL 窗口；`render()` 显示当前状态 |
| 真正无窗口 | `GameClient(synchronous=True, render_each_step=False, headless=True)` | 不创建显示连接或 GL 上下文；不能 `render()` |

所有客户端模式都关闭声音，使用独立临时配置与高分目录，关闭时清理。推荐使用 `with`。
GUI shell 启动脚本使用 `build/state/`。两者都不覆盖 `HOME`。
直接运行内部二进制且未提供隔离环境变量时，仍遵循上游用户目录规则，日常使用请通过客户端或启动脚本。

## Docker

```bash
docker build -t chromium-bsu-rl:local .
docker run --rm --init --network none chromium-bsu-rl:local
docker run --rm --init --network none chromium-bsu-rl:local \
  .venv/bin/python examples/headless_rollout.py --seed 209 --steps 300
docker run --rm --init --network none chromium-bsu-rl:local \
  .venv/bin/python -m unittest discover -s tests -v
```

开发镜像包含源码，以 UID 10001 运行。构建需要访问软件源，上述运行命令关闭网络。
可用 `docker build --build-arg BASE_IMAGE=...` 指定等价的 Ubuntu 24.04 基础镜像。
这些命令无需挂载主机显示服务。

在容器内验证显示路径：

```bash
docker run --rm --init --network none -e RUN_CHROMIUM_GUI_TESTS=1 \
  -e LIBGL_ALWAYS_SOFTWARE=1 chromium-bsu-rl:local \
  xvfb-run -a .venv/bin/python -m unittest discover -s tests -v
```

Xvfb 本身就是显示服务，该检查不等同于真正无显示验证或真实桌面人工验收。

## 集成到其他项目

通过 Git 子模块固定源码版本，使用消费项目的 Linux 虚拟环境执行：

```bash
git submodule add https://github.com/helywin/chromium-bsu-rl.git third_party/chromium-bsu-rl
bash third_party/chromium-bsu-rl/scripts/build_chromium_rl.sh
python -m pip install -e third_party/chromium-bsu-rl
```

克隆消费项目后，用 `git submodule update --init --recursive` 初始化子模块。
在本仓库虚拟环境中构建 wheel：

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
.venv/bin/python scripts/check_distribution.py
```

在消费项目中用 `python -m pip install /absolute/path/to/the.whl` 安装实际生成的 wheel，
再传入原生路径：

```python
from pathlib import Path
from chromium_rl import GameClient

runtime = Path("/absolute/path/to/chromium-bsu-rl")
with GameClient(binary=runtime / "build/install/bin/chromium-bsu-rl",
                data_directory=runtime / "game/data",
                synchronous=True, render_each_step=False, headless=True) as game:
    print(game.reset(7).player.position)
```

wheel 包含 Python 代码、`py.typed` 和许可声明，不包含原生程序及资源。
源码分发包包含游戏源码、资源、脚本、示例和文档，可以作为独立构建目录。
以上命令不假定包已上传 PyPI，也不假定存在预编译游戏发行包。

## 常见问题

| 现象 | 处理方式 |
| --- | --- |
| 缺少工具或 pkg-config 库 | 准备对应开发包；json-c 至少为 0.15 |
| 找不到程序或能力不支持 | 在与客户端一致的源码目录重新构建 |
| wheel 安装后找不到资源 | 用绝对路径指定 `binary` 和包含 `png/` 的 `data_directory` |
| SDL 视频或 GL 初始化失败 | 使用无窗口模式，或检查显示服务与 GL 驱动 |
| Wayland 后端异常 | 有 XWayland 时尝试 `SDL_VIDEODRIVER=x11 bash scripts/run_gui.sh`；原生 Wayland 尚未验收 |
| 无窗口模式无法 `render()` | 新建 GUI 客户端；运行模式在初始化时固定 |
| `episode_ended` | 保存终止快照，再调用 `reset(seed)` |
| `ProtocolError` | 查看异常中的游戏日志尾部并核对版本；传输失败后新建客户端 |
| 相同种子在其他机器上结果不同 | 对齐提交、平台、配置、动作和 tick 序列；不承诺跨平台逐位相同 |

验证命令见[贡献指南](../CONTRIBUTING.md#简体中文)。反馈问题时请附准确命令、提交、运行模式和错误日志。
