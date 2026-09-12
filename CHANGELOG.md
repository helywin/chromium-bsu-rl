# Changelog / 变更记录

Python package versions, protocol/schema versions and native behavior IDs are
independent. / Python 包版本、协议/快照版本和原生行为版本分别管理。

## 0.2.0 — Unreleased / 尚未发布

- Add English and Simplified Chinese installation, API, protocol and architecture
  guides, contribution templates and a documented source/wheel distribution path.
- Expose `PowerUpState`, `EpisodeEvents` and instrumentation capability flags in
  the public Python API. Validate advertised fields; preserve missing legacy
  instrumentation as `None`. Existing action and game behavior are unchanged.
- Add a seeded headless example, a non-root Docker development image, Python
  type checks, distribution checks and tag-triggered native headless/display CI.
- Package source, assets and build tooling in the sdist; keep the wheel limited
  to the Python client and license notices. Use modern package metadata.
- Correct outdated capability descriptions and separate historical records from
  current usage. Fail early on unsupported native Windows client execution.

新增完整中英文入口、使用文档、贡献模板与分发流程；公开道具、累计事件和能力类型，
缺失数据与实测零值分开处理。补充无显示示例、非 root 开发容器、类型/包检查和仅由 tag 触发的原生 CI。
源码包包含原生构建所需内容，wheel 保持为纯 Python 客户端。更新过时说明，明确平台边界。
本次不改变动作、物理、奖励或随机数行为。

## 0.1.0 source history / 源码阶段记录

The 2026-09-07 through 2026-09-11 source history introduced the upstream import,
isolated build, live snapshots, synchronous first-level steps, render separation,
seeded reset, headless execution, powerups and cumulative damage/events.
This records repository history, not a claim of a published package release.

2026-09-07 至 2026-09-11 的源码提交逐步完成上游导入、隔离构建、实时快照、单关步进、
绘图分离、带种子重置、无显示模式、道具及伤害/事件测量；此处记录源码历史，不代表曾发布包。

See [native changes](game/LOCAL_CHANGES.md) and [validation records](docs/README.md#validation-records).
