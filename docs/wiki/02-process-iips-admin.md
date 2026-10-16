# 02 进程、IIPS 与管理员启动

[总览](README.md) · [上一阶段](01-baseline-toolchain.md) · [下一阶段](03-redirection-tls-auth.md)

## 症状、原因和对照

普通权限两次启动均无正常游戏窗口，停在 IIPS 初始化。第二次受控调试在 IIPS 返回后得到 `EAX=0xE0000002`；`whoami /priv` 显示普通进程令牌没有 `SeCreateGlobalPrivilege`。

**静态确认**：`IIPS/iips.dll` 的 `FUN_10012760` 尝试设置该权限，失败路径产生 `IIPSERR_PRIVILEGE_SE_CREATE_GLOBAL_NAME`。主线程随后等待的 IIPS 完成事件未建立，不能仅按高 CPU 判断为“游戏在加载”。

**运行确认**：用户明确授权仅以管理员身份启动目标游戏后，11:24:46 使用 RunAs 启动 PID 44104，出现 IIPSHostApp 子进程和游戏窗口，进入错误 100。这个对照支持“权限是本次 IIPS 阻塞原因”，但此时认证和大厅尚未实现。

## 实际最小解决办法

只通过 Windows UAC 提升指定游戏启动进程，不授予整个工具链长期管理员权限，不改系统安全策略或 EXE。现有脚本：

- [Launch-Game.ps1](../../games/codol/versions/v3_3_3_3/scripts/Launch-Game.ps1)：先启动本地服务，再以 `-Verb RunAs` 启动项目同级游戏目录中的 EXE；防止重复启动。
- [Stop-Game.ps1](../../games/codol/versions/v3_3_3_3/scripts/Stop-Game.ps1)：必要时隐藏提权辅助 PowerShell 窗口，经 UAC 后读取 `ExecutablePath`，仅当完整路径与目标一致才按 PID 结束游戏，写入 [game-control.jsonl](../../runtime/logs/game-control.jsonl)。
- [Start-Services.ps1](../../games/codol/versions/v3_3_3_3/scripts/Start-Services.ps1) / [Stop-Services.ps1](../../games/codol/versions/v3_3_3_3/scripts/Stop-Services.ps1)：服务 PID 文件还需与本项目 `games/codol/versions/v3_3_3_3/server/local_server.py` 命令行匹配，不按所有 Python 进程处理。

**当前启动脚本含 `+set 2822 1 +set 3233 1`，这是未达到菜单目标的引导实验，不是已验证的启动必需项。** 参数和结果见 [06](06-onboarding-profile.md)。

## 授权后的复现操作

以下是人工复现说明。启动/停止授权只覆盖上述具体游戏路径和本项目服务；UAC 由用户确认。

```powershell
Set-Location -LiteralPath 'E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival'
```

上面的工作目录设置后，根据目的单独使用以下命令，不需要把它们连成批处理：

| 目的 | 命令 |
|---|---|
| 按当前参数启动服务和游戏 | `./Launch-Game.ps1` |
| 仅启动服务 | `./Start-Services.ps1` |
| 精确路径停止游戏 | `./Stop-Game.ps1` |
| 停止本项目服务 | `./Stop-Services.ps1` |

如需重做不带引导参数的启动基线，应由主任务在授权范围内恢复/比较[实验前启动脚本](../../runtime/backups/20261014-before-onboarding/Launch-Game.ps1)，或明确使用原始参数 `-q 0 -src=tgp -game_id 29 -zone_id 83886082`，不能声称当前 Launch 脚本仍只含原始参数。

只读检查可以使用：

```powershell
$expectedExe = 'E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL_Experience_V3.3.3.3_FULL.7z\codoMP_client_shipRetail.exe'
Get-CimInstance Win32_Process -Filter "Name='codoMP_client_shipRetail.exe'" |
    Where-Object { $_.ExecutablePath -eq $expectedExe } |
    Select-Object ProcessId, ExecutablePath, CommandLine
```

读取不到提权进程的路径时，不要退化为按同名进程批量结束。当前进程 ID 只作当次观察，不作为后续停止目标。

## 验收与证据

验收至少看到游戏窗口越过 IIPS 初始化；进入错误 100 只算启动阶段通过。管理员进程的关闭需要使用对应权限，不能因普通权限停止失败就认定游戏无响应。

- [REPORT](../../archive/baseline-20261014-110804/REPORT.md)、[错误 100 截图](../../archive/baseline-20261014-110804/error-100.png)。
- [GDB 返回值](../../archive/baseline-20261014-110804/gdb-iips-return.txt)、[IIPS 伪代码](../../archive/baseline-20261014-110804/iips-initialize-pseudocode.c)、[REA JSON](../../archive/baseline-20261014-110804/iips-initialize-evidence.json)，ID `ev_fd034a202dc322f3b6ba776ca52f18377916b00335a9111c85463cbe9caf70b7`。
- 当时运行时地址 `0x004ffb63` 对应静态 `0x0057fb63`，映像基址 `0x00380000`；不要把历史运行时地址直接复用于新进程。
- 主任务 12:22 更新：已通过 Stop-Game 停止 PID 6188，随后启动 PID 51912。此处是历史记录，不是当前存活检查。

## 回滚与下一检查

### 窗口模式下自动点击无响应（2026-10-14 16:55）

- **症状**：游戏已切换为窗口模式，普通自动点击“仓库”后画面不变；工具仍返回“已点击”。
- **权限证据**：`GetTokenInformation(TokenIntegrityLevel)` 读取游戏 PID 51896 为 `0x3000`（High），Codex 输入进程及 Windows MCP Python 为 `0x2000`（Medium）、UIAccess 为 0。微软说明 [SendInput 受 UIPI 限制](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)，只能向相同或更低完整性级别的应用注入输入。
- **工具事实**：Windows MCP 的 `desktop/service.py::click` 调用 `uia.Click`，底层为 `SetCursorPos` 与 `mouse_event`；成功消息没有验证游戏状态。当前统一 CUA 仅开放浏览器能力，用户已明确授权改用 Windows MCP。其截图为 2560×1440，显示时缩为 1920×1080，坐标需乘 4/3。
- **普通权限对照**：任务栏点击能将游戏切到前台；在游戏前台点击仓库不生效。不能把截图可见、鼠标命令已调用当作输入成功。
- **管理员对照**：用户授权单次管理员点击。第一次因同时人工操作出现角色名单弹窗，只确认鼠标移动；随后用户明确要求重试。16:55:37 单次脚本将仓库从“配装”切换到“背包”，证明本次菜单无需额外处理 DirectInput 或修改 EXE。主武器 31 级、副武器 20 级也在结果截图可见。
- **最小办法**：[单次验证脚本](../../games/codol/versions/v3_3_3_3/reverse/tools/test-game-admin-click.py) 在管理员进程内复用已安装的 Windows MCP 输入库，核对 EXE 完整路径、PID/窗口归属和 1280×960 客户区，确认前台后点击一次。脚本随即退出，没有常驻输入服务，也没有把 Codex/MCP 配置永久提权。固定“背包”坐标只用于本次截图条件，不是通用自动操作入口。
- **证据**：[点击前](../../runtime/captures/screenshots/20261014-admin-input-before.png)、[点击后](../../runtime/captures/screenshots/20261014-admin-input-test.png)、[目标与坐标](../../research/evidence/admin-input-test.json)。第一次受弹窗干扰的截图另保留为 `20261014-admin-input-test-first-modal.png`。

后续操作必须重新观察窗口、确认权限范围并避免用户与自动化同时输入。单次授权不能扩大成永久管理员输入；未验证战斗、长按、拖动或所有游戏页面。

只提升单次游戏进程，无系统权限配置需要恢复。结束游戏不自动代表服务也停止，两者分别控制。游戏运行会写 `players/config_mp.cfg`；回滚前先保留新资料，再选用对应时间的备份，不整体覆盖游戏目录。

窗口已出现仍报错误 100 时，下一步按 [03](03-redirection-tls-auth.md) 的请求链定位，不再反复处理已通过的 IIPS。
