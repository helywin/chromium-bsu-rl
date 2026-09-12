# Public project validation — 2026-09-12

English / 简体中文 · [Documentation index](../README.md)

Scope: the 0.2.0 public API, bilingual guides, build/distribution workflow and
container integration. Native gameplay source remains at the behavior introduced
through `4a15b71`; no physics, RNG or action changes are included in this work.

Environment: Ubuntu 24.04 Linux x86_64 in Docker, with dependencies installed
only in the image, an isolated Python 3.12 venv, and repository-local native
installation via `scripts/build_chromium_rl.sh`.

## Native results

- Full native configure/build/install completed in the development image.
- With networking disabled and no display server, `examples/headless_rollout.py
  --seed 7` reached `hero_dead` after 190 decisions / 948 ticks / 18.96 simulated
  seconds and printed score 5000 plus real powerup and episode-event data.
  This is a scripted interface run, not a learned policy or full-game completion.
- Under Xvfb and software OpenGL, all **24 tests passed**, with no skips. This
  includes GUI/headless same-seed comparison, render invariance, process cleanup,
  native powerups/events and public parser compatibility.
- Strict mypy validation of the public package and examples passed.
- Without a display server, 14 tests passed and 10 display tests were explicitly skipped.

## Distribution results

- Local Markdown checks passed for 29 files and five English/Chinese guide pairs.
- The sdist and wheel built successfully; both passed `twine check`.
- Archive checks verified the complete source/assets/scripts inventory, package
  metadata, `py.typed`, and unchanged license/author notices.
- The wheel installed in a fresh venv outside the checkout. A separate native
  build from the extracted sdist succeeded; its example ran against the installed
  wheel and reproduced the 190-decision / 948-tick headless result.

The Xvfb command needs `docker run --init`: without it, the container's top-level
`xvfb-run` waited without launching Python. The documented commands and CI include
the tested option. Xvfb checks are display-dependent; they do not verify a human
desktop session, native Wayland or visual quality.

## Reproduce

```bash
docker build -t chromium-bsu-rl:local .
docker run --rm --init --network none chromium-bsu-rl:local
docker run --rm --init --network none chromium-bsu-rl:local \
  .venv/bin/python -m unittest discover -s tests -v
docker run --rm --init --network none -e RUN_CHROMIUM_GUI_TESTS=1 \
  -e LIBGL_ALWAYS_SOFTWARE=1 chromium-bsu-rl:local \
  xvfb-run -a .venv/bin/python -m unittest discover -s tests -v
```

Packaging and local-link checks use the commands in [CONTRIBUTING.md](../../CONTRIBUTING.md).
CI defines Python 3.11/3.12/3.13/3.14 package checks and runs only on tag pushes.
No tag or CI run was created for this validation. Local Python 3.12 results alone
do not establish the other matrix entries.

## 中文说明

本记录覆盖 0.2.0 公开接口、中英文指南、构建分发与容器集成，不改变原生游戏物理、随机数或动作。
Ubuntu 24.04 x86_64 容器内完成构建，无显示、无网络的种子 7 示例运行到终止，
190 次决策共执行 948 tick，输出真实事件。Xvfb 软件渲染下 24 项测试全部通过，无跳过；
无显示模式下 14 项通过，10 项显示测试明确跳过。公开包与示例通过严格类型检查。

29 个 Markdown 文件的本地链接和 5 组双语指南检查通过，源码包与 wheel 均通过 twine 检查。
wheel 在仓库外全新虚拟环境中安装，从解压源码包独立构建的游戏成功被它调用，得到相同示例结果。

容器显示测试需要 `--init`，已同步文档与 CI。Xvfb 属于显示路径证据，不能解释为桌面人工验收、
Wayland 验收、训练效果或完整游戏通关。CI 仅由 tag 推送触发，本次没有创建 tag 或运行 CI；
其他 Python 版本以将来的实际 CI 结果为准。
