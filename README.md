# Chromium B.S.U. for RL

A standalone project for adapting Chromium B.S.U. into a deterministic, accelerated reinforcement-learning environment with Python interfaces and native GUI playback.

**Status: source/build baseline available.** Upstream sources are imported and the repository-local GUI build has been checked on Linux. There is no working training API, accelerated simulation, installable Python package, or trained model yet. This is not an official Chromium B.S.U. release.

## 项目目标

- C++运行游戏，Python通过独立子进程调用`reset/step`，读取状态与事件。
- 固定逻辑时间步，无渲染、不限速采样；GUI回放与训练共享游戏逻辑。
- 保留键盘移动模型，提供明确的动作、观察、奖励和终止契约。
- 可独立构建和使用，不依赖课程仓库、个人目录或Isaac Lab。

详见 [接口与加速设计方案](docs/design.md)。上述训练能力均待实现。

## 构建与运行（Linux）

需要已有C/C++编译工具、Autoconf/Automake、gettext（含autopoint）、pkg-config，以及SDL2、SDL2_image、OpenGL/GLU、FTGL、Fontconfig、OpenAL、freealut的开发文件。构建脚本会检查依赖，不自动安装或升级软件。

```bash
bash scripts/build_chromium_rl.sh
bash scripts/run_gui.sh
```

默认4个编译任务，可用`CHROMIUM_RL_BUILD_JOBS=2`调整。构建仅在本仓库`build/`进行，不执行sudo或系统安装。每次保留独立`build/work.*`供诊断，重复构建会占用额外磁盘空间。

请通过启动脚本运行：它使用640×480窗口、关闭声音，并将配置与高分隔离在`build/state/`，不会重设HOME。不带这些环境变量直接运行内部二进制仍会使用上游用户目录规则。菜单中进入游戏，支持方向键和组合斜移；字母快捷键可能受输入法影响。

本次窗口验证使用`SDL_VIDEODRIVER=x11 bash scripts/run_gui.sh`（Wayland桌面上的XWayland路径）。默认原生Wayland路径尚未验收，不宣称无界面模式已实现。详见 [构建与启动记录](docs/validation/source-build.md)。

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
