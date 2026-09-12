# Security / 安全问题

This alpha project currently maintains the latest source revision; there is no
security support commitment for older snapshots. Include the affected commit,
platform and minimal reproduction when reporting a problem.

For sensitive reports, use GitHub's **Report a vulnerability** option on the
repository Security page if available. If private reporting is unavailable,
open an issue asking for a private contact without posting exploit details,
credentials or personal data. No response-time guarantee is currently offered.

The native game is a local subprocess, not a sandbox for untrusted executables
or game assets. Applications should control the executable and asset paths they
pass to `GameClient`. Each client isolates preferences and scores and manages
only its own child process.

---

本 Alpha 项目当前维护最新源码，不承诺旧快照的安全支持。报告问题时请提供受影响提交、平台和最小复现。

敏感问题请优先使用仓库 Security 页面上的 **Report a vulnerability**（如可用）。
若未启用私密报告，可发 Issue 请求私下联系方式，不公开利用细节、凭据或个人信息。
目前不承诺响应时限。

原生游戏是本地子进程，不是用于执行不可信程序或资源的沙箱。
应用应控制传给 `GameClient` 的程序与资源路径。客户端隔离配置和高分，只管理自己创建的进程。
