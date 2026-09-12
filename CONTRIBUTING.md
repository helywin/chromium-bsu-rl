# Contributing / 贡献指南

[English](#english) | [简体中文](#简体中文)

## English

English and Chinese issues and pull requests are welcome. Keep discussion
respectful, specific and focused on reproducible behavior. Small documentation
fixes can go straight to a PR; discuss public API or gameplay changes in an issue
so consumers can assess compatibility.

Prepare the [Linux build prerequisites](docs/installation.md), then use a project
venv. Build outputs, logs, models and local captures belong in ignored `build/`
or `artifacts/`; distribution files go in ignored `dist/`.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
bash scripts/build_chromium_rl.sh
.venv/bin/python scripts/check_repository.py
.venv/bin/python -m mypy
.venv/bin/python -m unittest discover -s tests -v
```

The default test command includes **real native headless tests** and therefore
needs a built game. Display tests are skipped unless explicitly enabled:

```bash
RUN_CHROMIUM_GUI_TESTS=1 LIBGL_ALWAYS_SOFTWARE=1 \
  xvfb-run -a .venv/bin/python -m unittest discover -s tests -v
```

To check Python only, without a native build:

```bash
.venv/bin/python -m unittest discover -s tests -p test_state.py -v
.venv/bin/python -m unittest discover -s tests -p test_client.py -v
```

Verify distributions when changing packaging, native integration or public API:

```bash
.venv/bin/python -m build --no-isolation
.venv/bin/python -m twine check dist/*
.venv/bin/python scripts/check_distribution.py --native
```

The last command validates archive contents/licenses, installs the wheel into a
fresh venv, builds the extracted source distribution using the supported script,
and runs its headless example outside the checkout. Docker equivalents are in
the [installation guide](docs/installation.md#docker).

Preserve upstream notices. Add a dated description to each modified upstream
source file and update [game/LOCAL_CHANGES.md](game/LOCAL_CHANGES.md). Do not
regenerate tracked Autotools output; the build script works in an isolated copy.
Keep Python APIs typed and fail explicitly when native capability/data is missing.
Update both language guides and [CHANGELOG.md](CHANGELOG.md) for public changes.
Describe protocol, schema and game behavior changes separately.

Report exact test commands and outcomes in PRs. Xvfb is display-dependent evidence;
headless tests must not need it. Native game changes need native regression
evidence. Interface tests do not demonstrate successful learning or full-game
completion. Never include credentials, personal paths or generated models in a PR.

For a release, complete these checks on the candidate commit, review both READMEs
and the license/source inventory, then document the supported platform and exact
artifact contents. Version 0.2.0 is currently an unreleased source/package change;
CI runs only when a tag is pushed; branch pushes, PRs and manual dispatch do not
start it. CI does not publish to PyPI or create a release automatically.

## 简体中文

欢迎中文或英文 Issue 与 PR。讨论应尊重他人、具体并围绕可复现行为。
小型文档修正可直接提交 PR；公开 API 或游戏规则改动建议先在 Issue 讨论兼容性。

先准备 [Linux 构建依赖](docs/installation.zh-CN.md)，使用项目虚拟环境。
构建、日志、模型和本地截图放在忽略提交的 `build/` 或 `artifacts/`，分发文件放在 `dist/`。
上面的命令依次完成：安装开发依赖、构建游戏、检查文档链接、严格类型检查、默认测试。

默认测试包含**真实原生无显示测试**，因此必须先构建游戏；GUI 测试需显式设置
`RUN_CHROMIUM_GUI_TESTS=1`。使用 Xvfb 的命令验证显示路径，不能作为真正 headless 证据。
只检查 Python 时，执行上方 `test_state.py` 与 `test_client.py` 两条命令，不需要原生构建。

修改打包、原生集成或公开 API 时，执行上方分发检查命令。
`check_distribution.py --native` 会核对包内容与许可、在新 venv 安装 wheel、从解压后的源码包
独立构建游戏，并在仓库外运行无显示示例。容器方式见[安装指南](docs/installation.zh-CN.md#docker)。

保留上游声明；修改上游源码文件时，在文件中写明日期与变更，并更新
[game/LOCAL_CHANGES.md](game/LOCAL_CHANGES.md)。不要在受跟踪目录中重新生成 Autotools 产物。
Python API 保持类型声明，原生能力或数据缺失时明确报错。
公开行为变化要同步两种语言的指南与 [CHANGELOG.md](CHANGELOG.md)，分别说明协议、快照和游戏行为变化。

PR 应报告准确验证命令与结果。原生游戏变更需要原生回归证据；接口测试不能证明训练成功或整局通关。
不要提交凭据、个人路径或生成的模型。

发布前，在候选提交上完成上述检查，核对双语首页、许可和来源清单，再说明平台与产物内容。
0.2.0 当前是尚未发布的源码/包更新。CI 仅由推送 tag 触发，普通分支 push、PR 和手动 dispatch 均不会启动；
CI 不会自动发布 PyPI 包或创建发行版。
