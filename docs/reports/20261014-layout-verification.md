# 2026-10-14 目录整理与重启验收

范围仅为 `CODOL-Revival/`。没有搬动游戏目录或修改游戏 EXE；没有初始化 Git、提交、推送或安装 GUI。

## 目录变更

| 旧位置 | 新位置 |
|---|---|
| 根目录四个启动/停止脚本 | `scripts/` |
| `captures/logs/certs/data/backups` | `runtime/` 下同名子目录 |
| `docs/` 的两份日期报告 | `docs/reports/` |
| `research/` 根目录分析输出、原始档案和快照 | `research/evidence/` |

`src/`、`tests/`、`tools/`、`docs/wiki/`、`research/reference-protocol/`、`archive/` 保留职责。新增文档入口、协作说明、依赖锁定和忽略规则。测试改用 `tests/fixtures/`，不再依赖运行抓包；认证fixture已替换账号和IV为测试值。第三方来源与许可证归属保留。

完整[搬迁清单](20261014-directory-migration.json)记录994个文件的旧/新位置和搬迁时SHA256。移动后全部逐一匹配；脚本、文档随后按新路径更新。982个原始抓包、研究证据、证书、备份、玩家数据文件再次核验仍一致。日志和PID在后续启动时正常更新，不应与搬迁时哈希强行比较。

原始REA JSON、历史归档中的路径保留生成时原文，使用搬迁清单定位新位置。Markdown链接已调整。历史报告的叙述仍代表当时状态。

## 验证

- 21项Python测试通过：认证票据、加密大厅、STUN、发布文件、公开档案CRC及保存重载。
- 四个PowerShell入口语法通过；REA辅助脚本 `node --check` 通过。
- 本机文档文件链接检查通过；命令为 `python -B tools/check-doc-links.py`。
- 13:02启动新服务PID50072、游戏PID13836，连接 `127.0.0.1:54084`；`8/1`返回一个公开档案。
- 13:03真实界面直接进入大厅，显示johnClient、等级1、第二角色马库斯，没有原训练繁忙弹窗。游戏和服务都已重启，因此验证包含磁盘档案重新加载。
- 游戏EXE SHA256仍为 `e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。

[重启截图](../../runtime/captures/screenshots/20261014-main-menu-after-layout-restart.png) · [重启事件](../../runtime/captures/main-menu-layout-restart-events.jsonl) · [引导修复详情](../wiki/06-onboarding-profile.md)

真实客户端本轮没有新的8/3提交；更新写回由离线/内存协议测试覆盖，仍需一次真实客户端修改后重进验收。引导完成位没有直接改写，进入大厅依赖现有启动覆盖命令。训练、匹配及对局服务器仍未实现。
