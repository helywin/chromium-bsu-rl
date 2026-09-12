# Documentation / 文档索引

Start with [English](../README.md) or [简体中文](../README.zh-CN.md).
Current guides below describe the present public interface. / 以下指南描述当前接口。

| Guide / 指南 | English | 简体中文 |
| --- | --- | --- |
| Installation / 安装 | [Read](installation.md) | [阅读](installation.zh-CN.md) |
| Python API | [Read](api.md) | [阅读](api.zh-CN.md) |
| Wire protocol / 进程协议 | [Read](protocol.md) | [阅读](protocol.zh-CN.md) |
| Architecture / 架构与方向 | [Read](architecture.md) | [阅读](architecture.zh-CN.md) |
| Performance and GPU acceleration / 性能与 GPU 加速 | [Read](performance.md) | [阅读](performance.zh-CN.md) |
| Contributing / 贡献 | [Read](../CONTRIBUTING.md) | [阅读](../CONTRIBUTING.md#简体中文) |

## Validation records

Records report what was tested at their date and revision; old counts and
limitations are not current support claims. Reproduction commands use paths
relative to this standalone checkout, with a local `.venv` replacing the original
operator's venv. Historical before/after binaries and external consumer projects
are not required for the current regression suite.

验证记录只描述对应日期与版本的证据，旧测试数量和限制不代表当前支持范围。
复现命令已归一为本仓库相对路径和 `.venv`，原始使用者的个人目录不构成依赖。
当前回归不需要历史对照二进制或外部消费项目。

| Record / 记录 | Scope / 范围 |
| --- | --- |
| [Source build](validation/source-build.md) | Historical native build and manual window inspection / 历史构建与窗口检查 |
| [Live snapshot](validation/live-snapshot.md) | Historical live protocol and process lifecycle / 历史快照与生命周期 |
| [Seeded reset](validation/seeded-reset.md) | Same-seed trajectories and resource checks / 种子轨迹和资源 |
| [Powerup snapshots](validation/powerup-snapshot.md) | Native pickup identity and movement / 道具标识与移动 |
| [Headless runtime](validation/headless-throughput.md) | No-display behavior and trajectory comparison / 无显示与轨迹对照 |
| [Episode events](validation/episode-events.md) | Real native instrumentation / 原生事件测量 |
| [Public project validation](validation/public-project.md) | Packaging, public API and current native checks / 打包、公开 API 与当前原生检查 |

## Historical design notes

These explain implementation decisions and retain stage-specific limitations.
Use the current guides above for installation and API usage.
以下保留当时的设计判断与限制，安装及 API 使用以上面的当前指南为准。

- [Original design](design.md)
- [Synchronous control v1](synchronous-step.md)
- [Render separation v2](render-free-stepping.md)
- [Rendering side-effect audit](render-separation-audit.md)

[Upstream provenance](../game/UPSTREAM.md) · [Local changes](../game/LOCAL_CHANGES.md) ·
[License scope](../LICENSE.md) · [Changelog](../CHANGELOG.md)
