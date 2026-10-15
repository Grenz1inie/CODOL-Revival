# CODOL 3.3.3.3 本地复活技术 Wiki

本 Wiki 按游戏生命周期维护问题、证据和最小修复。适用对象是本项目的 2016 年 3.3.3.3 客户端；公开 Demonware 实现仅作对照，不能按 SDK 名称推定兼容性。

**截至 2026-10-14 13:03（北京时间）**：已走通本地认证、加密大厅、发布文件、公开档案读取，并实际进入游戏大厅，显示第二角色马库斯。直接传`+set 2822 1 +set 3233 1`失败；改为单个白名单命令段内的分号列表，结合真实选角档案读取后成功。13:03在目录迁移后重新启动游戏和服务，仍加载同一角色并进入大厅。训练、匹配、对局服务器仍未实现。公开档案保存/读取的自动化测试通过，真实客户端的新修改写回尚待另测。

[成功截图](../../runtime/captures/screenshots/20261014-main-menu-profile-restore.png) · [本次修复与验收](06-onboarding-profile.md) · [文档入口与协作约定](../README.md)

**最新进展**：3 转生、70 级及商城等级解锁生效；游戏币购买及重登保持通过，点券显示和购买扣款入库已确认。全物品发放、武器满级经验及续期已实现，浏览器操作通过；用户确认重登后永久物品、武器满级、配件及皮肤装备正常。协议与边界见 [08](08-player-progression-marketplace.md)、[09](09-inventory-completion.md)。分辨率任务已按用户要求取消。

## 按阶段定位

剧情关卡解锁已实测：后续关卡锁消失，最后一关可选。2026-10-15真实玩家档案的隔离加密连接已通过出生快照、移动和弹药减少，实际大厅查询/预订/开始确认通过。新服务已启动，可进行首关完整游戏的人工验收；地图加载、画面与实际操作仍待用户确认。全部PVE入口和原版剧情后置。见 [07 连接链路](07-session-game-server.md)、[10 PVE 与剧情](10-pve-story.md)。

| 阶段 | 遇到什么问题时阅读 | 当前结论 |
|---|---|---|
| [01 安装包、工具链与基线](01-baseline-toolchain.md) | 外层 EXE 是什么、缺注册项、分析超时、文件身份不明 | 基线建立；未运行外层安装器；主程序分析已完成并留存 |
| [02 进程、IIPS 与管理员启动](02-process-iips-admin.md) | 无窗口、IIPS 初始化失败、普通权限不能结束游戏 | 管理员启动解决本次 IIPS 权限阻塞；精确路径停止已验证 |
| [03 地址重定向、TLS 与认证](03-redirection-tls-auth.md) | 错误 100、TLS 失败、HTTP 200 后仍不进大厅 | task10 → task11 明文票据路径获真实客户端接受 |
| [04 加密大厅与 STUN](04-lobby-stun.md) | 28 字节 hello 后断开、握手或 MAC 失败 | 协议 210 收发已运行验证；UDP 0x0e 尚未解释 |
| [05 发布文件与角色选择](05-publisher-character-selection.md) | 初始化卡住、文件空结果、角色页不出现 | CODOL 实际使用 10/21；一个空文件对象已支持到达选角 |
| [06 新手引导与角色资料](06-onboarding-profile.md) | 选角后训练页、跳过参数无效、资料是否保存 | 白名单命令段＋真实公开档案读取已进入大厅；保存链测试通过，客户端新修改写回待测 |
| [07 会话与游戏服务器](07-session-game-server.md) | 训练/匹配繁忙、预订与对局握手 | 真实档案的回环与实际大厅联调通过；首关已准备人工验收 |
| [08 玩家等级、余额与商城](08-player-progression-marketplace.md) | 最高等级、转生、货币和物品所有权 | 实测 3 转生、70 级；商城等级解锁、游戏币购买扣款入库和重登保持通过 |
| [09 点券、全物品与武器成长](09-inventory-completion.md) | 点券不显示、完整物品目录、武器等级和限时续期 | 点券购买、全物品永久发放、满级和配件/皮肤装备已人工验收；续期浏览器及数据检查通过 |
| [10 PVE 菜单、剧情解锁与地图启动](10-pve-story.md) | 剧情锁、PVE 模式缺失、战斗开始后等待 | 剧情锁已解除；出生/移动/射击协议通过，完整游戏待人工验收 |

阅读顺序是阶段依赖，不是“前一步端口通了，后一步一定成功”。错误 100 曾同时覆盖“认证未完成”和“认证已通过、大厅未实现”两种状态。

## 证据与状态约定

- **运行确认**：真实客户端后续行为、抓包或界面已证实；写明时间、连接和验收点。
- **静态确认**：目标 EXE 的反编译、字节或当前源码明确支持；不能替代运行验收。
- **推断**：可解释观察的候选原因，必须写出还缺哪条调用链或对照实验。
- **未验证 / 实验失败**：未做验收，或实验未达到预定目标。失败结果不等于机制已被完全否定。

记录正文时间统一用北京时间；`runtime/captures/20261014T03…` 文件名及日志 `+00:00` 为 UTC，加 8 小时对应本地时间。请求序号、事务号会在重连后重复，关联证据时同时保留时间与 `peer`，不要只检索 `seq=51`。

## 操作入口

项目根目录是 `E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival`。下列入口用于本机复现；管理员游戏启停会显示UAC。

| 操作 | 入口与使用边界 |
|---|---|
| 一键启动 / 环境检查 | [Start.ps1](../../Start.ps1)；默认启动服务、控制器、浏览器和游戏，`-CheckOnly` 只读检查，`-NoGame` 暂不启动游戏；[参数与排错](../controller.md#启动与使用) |
| 启动 / 停止游戏 | [Launch-Game.ps1](../../scripts/Launch-Game.ps1)、[Stop-Game.ps1](../../scripts/Stop-Game.ps1)；人工确认 UAC，详见 [02](02-process-iips-admin.md)。当前启动脚本包含已进入大厅的组合命令 |
| 启动 / 停止服务 | [Start-Services.ps1](../../scripts/Start-Services.ps1)、[Stop-Services.ps1](../../scripts/Stop-Services.ps1)；服务改源码后需重启才生效，不能把文件修改当作运行采用 |
| 检查服务链 | [server.jsonl](../../runtime/logs/server.jsonl) 中依次找 `auth_request`、`auth_reply`、`lobby_authenticated`、`lobby_task`，结合对应抓包和界面 |
| 运行协议测试 | 在项目根执行 `& 'A:\Coding\Python3.13.7\python.exe' -B -m unittest discover -s tests -v`；内存测试不代表游戏界面或对局通过 |
| 查已有静态证据 | 阅读保存的 JSON / C 文件；本次REA分析已导出快照并关闭。静态地址不是运行时地址 |

## 证据总索引

| 范围 | 入口 |
|---|---|
| 项目说明、原始验收记录 | [项目 README](../../README.md)、[认证验证](../reports/20261014-auth-verification.md)、[选角后报错](../reports/20261014-character-selection.md) |
| 最早启动与 IIPS 基线 | [归档 REPORT](../../archive/baseline-20261014-110804/REPORT.md)、[初始清单](../../archive/baseline-20261014-110804/before-files.json)、[运行文件变化](../../archive/baseline-20261014-110804/runtime-file-changes.json) |
| 认证与大厅静态证据 | [认证解析](../../research/evidence/auth-parser-decompiled.json)、[210/KDF 与配置读取](../../research/evidence/lobby-keys-stun-decompiled.json)；Evidence ID 见各阶段 |
| 发布文件与界面 | [服务日志](../../runtime/logs/server.jsonl)、[角色界面截图](../../runtime/captures/screenshots/20261014-character-selection.png)、[训练页警告截图](../../runtime/captures/screenshots/20261014-after-character-selection-error.png) |
| 选角后请求与响应 | [观察区间事件](../../runtime/captures/character-selection-events.jsonl)、[请求 51 独立解析](../../research/evidence/character-selection-request-51.json) |
| 引导条件与参数 | [完成判断](../../research/evidence/onboarding-completion-checks.json)、[参数注册](../../research/evidence/onboarding-override-registration.json)、[名称原始字节](../../research/evidence/onboarding-override-names.json) |
| profile 数据校验 | [seq44解压数据](../../research/evidence/profile-seq44-raw.bin)、[seq45解压数据](../../research/evidence/profile-seq45-raw.bin)；压缩包、CRC值和复核边界见 [06](06-onboarding-profile.md) |
| 保存的 REA 分析包 | [认证阶段包](../../research/evidence/rea-main-evidence-20261014.json)、[引导后导出包](../../research/evidence/main-analysis-after-onboarding.rea.json)、[导出记录](../../research/evidence/main-analysis-close.json)；[大厅修复后快照](../../research/evidence/main-analysis-after-main-menu.rea.json)含32条证据记录 |
| 原生移植阶段的REA快照 | [客户端快照](../../research/evidence/client423-native-stage.rea.json)含89项工作流缓存和180条证据；[恢复说明与限制](../reports/20261015-server-port.md#rea快照与索引恢复) |
| 公开协议实现 | [协议研究笔记](../../research/reference-protocol/protocol-notes.md)、[仓库提交与逐文件 SHA256](../../research/reference-protocol/source-manifest.json) |

研究笔记保留了早期“10/7 尚待真实验证”的历史边界；本 Wiki 的 [05](05-publisher-character-selection.md) 补充后续 CODOL 10/21 的实际运行证据，不回写旧报告。公开参考源涉及 GPL-3.0、AGPL-3.0 和 PolyForm Shield 1.0.0，具体归属见笔记与各仓库许可证。协议事实、项目实现与原始源码分别注明来源。

## 后续维护程序

每个新问题归入最近的生命周期阶段，不按一次聊天另建总报告。主任务得到新结果后按以下顺序更新：

1. 在对应阶段追加一条带时间的实验记录，保留旧失败结果；填写“症状 → 证据 → 原因状态 → 最小变更 → 验收 → 限制”。
2. 链接精确抓包、截图、源码和保存的 REA JSON，补 Evidence ID、函数地址和目标哈希；无证据文件的用户反馈明确标成反馈，不虚构文件名。
3. 运行结果注明启动参数、进程/连接、服务是否重启、复现动作与界面。资料持久化必须包含退出再进验证。
4. 只在阶段验收真的通过后更新本页状态表和“截至”时间；修复一个 UI 分支不能顺带宣布匹配/训练成功。
5. 为未解决问题保留下一项最小检查和回滚点；引导和档案的后续结果写入 [06 的实际验收](06-onboarding-profile.md#实际验收)。

可复用条目格式：

```text
时间 / 目标哈希 / 阶段：
症状与复现动作：
确认的事实（运行 / 静态）及证据路径、ID：
候选原因与缺口：
实际最小变更（涉及文件、参数、服务重启）：
验收结果（成功 / 失败 / 未做）：
回滚点 / 下一检查：
```

目录规则、环境和提交前检查见 [CONTRIBUTING](../../CONTRIBUTING.md)。历史报告保留当时结论，当前状态以本总览及对应分章的最新验收为准。
