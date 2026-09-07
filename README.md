# Chromium B.S.U. for RL

A standalone project for adapting Chromium B.S.U. into a deterministic, accelerated reinforcement-learning environment with Python interfaces and native GUI playback.

**Status: design only.** Game sources have not been imported. There is no working training API, installable Python package, or trained model yet. This is not an official Chromium B.S.U. release.

## 项目目标

- C++运行游戏，Python通过独立子进程调用`reset/step`，读取状态与事件。
- 固定逻辑时间步，无渲染、不限速采样；GUI回放与训练共享游戏逻辑。
- 保留键盘移动模型，提供明确的动作、观察、奖励和终止契约。
- 可独立构建和使用，不依赖课程仓库、个人目录或Isaac Lab。

详见 [接口与加速设计方案](docs/design.md)。上述能力均待实现。

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

计划基于 [Chromium B.S.U.](https://chromium-bsu.sourceforge.net/) 0.9.16.1发布源码。导入时保留上游Clarified Artistic License、版权声明及各资源许可，记录所有本地修改。不对上游代码或资源重新套用其他许可证。

目前仅有项目文档；新增代码的许可说明将在首次代码发布前明确，不应把公开可读等同于已授予任意再分发许可。
