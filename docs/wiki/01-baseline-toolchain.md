# 01 安装包、工具链与基线

[总览](README.md) · 下一阶段：[进程与 IIPS](02-process-iips-admin.md)

## 症状与原因

| 问题 | 已确认事实 | 仍不能推出的结论 |
|---|---|---|
| 把外层 EXE 当作离线启动器 | 归档检查认定 `CODOL_Experience_V3.3.3.3_FULL.exe` 是 1,528,836 字节 NSIS 安装器，含六个 7z 分卷的 `SpannedFileList.txt` | 不是原帖所称 `CODO_OfflineLauncher`，不能靠运行它获得 DW 服务端 |
| 找不到安装路径注册项 | 当时查过 HKCU/HKLM/WOW6432Node 的 `Software\Tencent\codoltyf / InstallPath`，未找到 | 缺注册项是否影响其他路径尚未证明；没有为此手工写注册表 |
| 主 EXE Ghidra 分析超时 | 早期 300 秒调用超时；后续完成一次默认分析，耗时 642.66 秒 | 超时不等于文件损坏、引擎不支持，也不等于反编译已成功 |

上述安装包/注册项结论来自[基线 REPORT](../../archive/baseline-20261014-110804/REPORT.md)，本轮未重跑安装器或安装依赖。

## 实际最小处理

直接以已解出的客户端建立基线，不运行外层安装器。游戏目录是项目根的同级目录：

```text
E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL_Experience_V3.3.3.3_FULL.7z
```

目标 `codoMP_client_shipRetail.exe` 的基线 SHA256：

```text
e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
```

保留[初始文件清单](../../archive/baseline-20261014-110804/before-files.json)、[基线二进制哈希](../../archive/baseline-20261014-110804/final-binary-hashes.json)、[运行变化清单](../../archive/baseline-20261014-110804/runtime-file-changes.json)与[配置备份](../../runtime/backups)。游戏会自行写入配置、IIPS/Tenproxy 等日志，不能把所有文件变化都算作人工补丁。

REA 分析由[rea-session.mjs](../../tools/rea-session.mjs)隔离启动：REA 6.4.0、Ghidra 12.1.4，子进程设置 `REA_GHIDRA_STARTUP_TIMEOUT_MS=1200000`；整理后的工具默认从 LOCALAPPDATA 定位 REA，也支持 `REA_HOME`、`GHIDRA_INSTALL_DIR`，Java使用当前环境的 `JAVA_HOME`。本机已配置为 `A:/Coding/Java/jdk-21.0.11.10-hotspot`；本轮未修改全局环境。脚本会启动分析进程；本次分析结束已保存快照并关闭会话。

本地服务使用现有 `A:\Coding\Python3.13.7\python.exe` 与 `cryptography`。Python、REA、JDK 的用途不同：服务协议测试无需启动 Ghidra，阅读已保存证据也无需重建会话。

## 验收和可复现检查

本阶段验收是“目标身份、备份、分析证据可追溯”，不是进入角色页。后续重用地址前先在有文件读取权限的 PowerShell 中比较哈希：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL_Experience_V3.3.3.3_FULL.7z\codoMP_client_shipRetail.exe'
```

一次相同哈希只证明该文件相同，不证明配置、服务版本或当前运行进程相同。不要对仍在运行的游戏作“源码已生效”推断。

## 证据入口

- [认证验证中的工具链记录](../reports/20261014-auth-verification.md)：642.66 秒分析和隔离环境。
- [main-open.json](../../research/evidence/main-open.json)、[分析包](../../research/evidence/rea-main-evidence-20261014.json)、[引导阶段包](../../research/evidence/main-analysis-after-onboarding.rea.json)：重用已保存结果。
- [IIPS 反编译](../../archive/baseline-20261014-110804/iips-initialize-evidence.json)：`ev_fd034a202dc322f3b6ba776ca52f18377916b00335a9111c85463cbe9caf70b7`。
- [公开协议来源清单](../../research/reference-protocol/source-manifest.json)：仓库、提交、URL、SHA256，供区分“参考项目行为”和“本客户端行为”。

## 限制、回滚与下一检查

没有通过运行安装器验证注册表/运行库安装路径，不能将其写为已修复。本阶段没有安装变更可回滚；恢复配置时使用对应阶段备份，不能用旧目录整体覆盖后来的资料。

若哈希不同，先建立新的版本证据，不沿用旧静态地址；若哈希一致且启动无窗口，进入 [02](02-process-iips-admin.md) 检查 IIPS 权限链。
