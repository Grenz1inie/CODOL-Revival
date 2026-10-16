# 06 新手引导与角色资料

[总览](README.md) · [上一阶段](05-publisher-character-selection.md) · [下一阶段](07-session-game-server.md)

**当前状态：12:40 真实客户端已进入游戏大厅，显示第二个角色“马库斯”。** 已采用单个白名单命令段内的引导覆盖，并读取本地保存的公开档案。两项改动组合实测通过；未直接读取运行内存中的 dvar 数值。训练及对局未实现，档案保存与重新加载的各层验收见下文。

## 症状与原始观察

用户选择第二个角色后，训练页显示“很好 johnClient！接下来我们将前往核弹小镇开始训练。点击继续开始。”，并弹出“服务器繁忙中，请稍候重试”。[原始截图](../../runtime/captures/screenshots/20261014-after-character-selection-error.png)和[观察记录](../reports/20261014-character-selection.md)说明已经越过角色选择，但还没进入训练。

相关请求有 seq47/48 的 8/3 压缩数据提交、seq50 的 71/3（含 OnBoarding、LoadoutChangeEvent）以及 seq52 的 71/15（解压后含 UIPage）。它们证明对应消息发生过，不证明后端写入、角色保存或引导标志已持久化。当前大量服务仍返回 N=0。

## 静态原因线索：完成判断与两个覆盖参数

| 名称/位置 | 静态确认 | 限制 |
|---|---|---|
| `2822`：字符串0xc74088，指针DAT_0783fa70 | `0x5c3670` 检查 `un_mp_tutorial`；其结果为假时，还允许该参数 `+0xc` 值非零使函数返回1 | 只证明这一完成判断的控制条件 |
| `3233`：字符串0xc74090，指针DAT_0783fa74 | `0x5c36f0` 检查 `onboard_complete`；同样有覆盖条件 | 函数还有 DAT_0783f8c0 前置分支，不能称为无条件跳过全部引导 |
| 参数注册 | `0x605af0` 通过 `FUN_00633a00` 注册两项，传入默认0、flags0；原始字节证实数字字符串名称 | 注册存在不表示允许命令行赋值；后续发现执行前白名单过滤，见下文 |

`FUN_005c6350` 从 `mp/uiNotifications.csv` 按名称查询，`FUN_005953a0` 访问相关状态。这条链不等于完整 profile 存储格式；不要凭函数名或通知名创建未经证实的存档字段。

## 实际最小实验与失败结果

主任务在原版 EXE 不变的前提下，只向 [Launch-Game.ps1](../../games/codol/versions/v3_3_3_3/scripts/Launch-Game.ps1)追加：

```text
+set 2822 1 +set 3233 1
```

实验前脚本和 `players/config_mp.cfg` 保存于 [backups/20261014-before-onboarding](../../runtime/backups/20261014-before-onboarding)。两项参数目前是实验设置，**不是已验证可用的操作步骤或永久解决方案**。

| 时间（北京时间） | 事实与证据来源 | 结论 |
|---|---|---|
| 首次选角后 | 原始截图/记录显示训练页及繁忙；12:06游戏与服务存活，至12:08:09有大厅心跳 | 已到训练引导；不是仅因进程退出造成的报错 |
| 12:22 | 主任务运行更新：Stop-Game 精确停止 PID6188，带两参数启动 PID51912；脚本和配置已备份 | 参数已写入启动配置并进行了重启实验，不等于参数运行值已证实 |
| 12:24 | 用户重新选择第二角色；主任务实际 UI 观察和用户截图仍是相同训练页/繁忙 | **实验失败：未达到进入菜单目标；不能标记参数 operational** |

[12:24复测截图](../../runtime/captures/screenshots/20261014-onboarding-flags-error-user.png)已归档，确认直接传两项参数仍停在原报错页面。

### 已取得的失败原因：命令行白名单过滤

主任务最新 objdump 读证显示：`FUN_00598150` 对按 `+` 切分后的每个命令检查地址 `0x00cdd238` 的七项白名单：

```text
connect_lobby
set dw_username
set r_displayMode
set 2451
set 2624
set 938
set 1436
```

全部不匹配时，`0x005982b0` 执行 `movb $0,(%edi)`，把命令首字节置为 NUL，使其成为空串。`set 2822 1`、`set 3233 1` 不匹配上述白名单，因而在执行前被过滤。

**静态确认**：REA 反编译与 objdump 一致。证据见 [命令过滤与后续执行](../../research/evidence/onboarding-command-filter-and-publisher.json)，Evidence ID `ev_bd56621a7899ff6d1bb5af02f6b59001766681e7da3b964728a2aff64672d353`。`0x00598590` 把保留的命令段交给命令执行器；本地测试保留用户名设置前缀，将两个开关放在同一段的分号命令列表中。没有修改 EXE 或白名单。

## Profile：长度与 CRC32 已复核

主任务保存的 seq44、seq45 profile 压缩数据均可用 zlib 解压为32768字节。本轮 Wiki 更新只读复核了两份压缩文件与 raw 文件逐字节相同，并验证：

```text
LE32(raw[0:4]) == zlib.crc32(raw[4:]) & 0xffffffff
raw = CRC32[4] | 数据[32764]
```

| 序号 | 压缩 / 解压证据 | 压缩字节数 | 解压字节数 | 首LE32与计算CRC32 |
|---:|---|---:|---:|---|
| 44 | [压缩](../../research/evidence/profile-seq44-compressed.bin) / [raw](../../research/evidence/profile-seq44-raw.bin) | 1108 | 32768 | 两者均为 `0x4b78469c` |
| 45 | [压缩](../../research/evidence/profile-seq45-compressed.bin) / [raw](../../research/evidence/profile-seq45-raw.bin) | 1179 | 32768 | 两者均为 `0xdea7c860` |

这是两份保存样本的结构/完整性证据，不等于 profile 字段、引导标志偏移或服务端读写协议已经还原。序号需结合原连接关联，不能直接替代前述 seq47/48 的提交记录；当前没有据此宣称角色保存、重新加载或跳过引导成功。

## 证据与验收要求

- [完成检查](../../research/evidence/onboarding-completion-checks.json)：`ev_6bc47e9711bca44a0b74c03346ff294d057cc900ef70ed75f0fc0c942c4a1cd8`，含0x5c3670、0x5c6350、0x5953a0。
- [onboard_complete 消费点](../../research/evidence/onboard-complete-users-decompiled.json)：`ev_39e507d47d9f4eba714664eed69aa68c73f6c1bb854e913cb8abf929d99490fa`，含0x5c36f0。
- [覆盖参数注册](../../research/evidence/onboarding-override-registration.json)：`ev_74ffe2816ed185df5a55d97073a32d86800b74c447b44e2313cc3ec20289b74c`。
- [名称字节](../../research/evidence/onboarding-override-names.json)：`ev_3a64748db74c17ba095216aa64fe392f8267acab234445159b920f9b9d299f1c`；[bool注册](../../research/evidence/bool-dvar-registration.json)：`ev_bfa637c5d13f83563db79325218733046fc9683dbaaf4676797c2092279bcc80`。
- [观察区间事件](../../runtime/captures/character-selection-events.jsonl)、[请求51解析](../../research/evidence/character-selection-request-51.json)；后者的具体语义讨论见 [07](07-session-game-server.md)。

下次验收分别回答三个问题：参数在目标时刻实际值是多少；界面是否越过训练引导到菜单；退出重进后角色/资料是否仍一致。三者不能互相代替。跳过 UI 即便成功，也不证明训练服务器或资料存储完成。

## 已采用的最小修复

[scripts/Launch-Game.ps1](../../games/codol/versions/v3_3_3_3/scripts/Launch-Game.ps1)保留原有 TGP 参数，并传入一个完整命令段：

```text
+set dw_username johnClient;set 2822 1;set 3233 1
```

用户名 `johnClient` 与本机已有账号一致。不能把后两项重新拆成独立 `+set` 段，否则又会被过滤。这是本机客户端的实验性启动方式；完整用户名设置也包含在命令里，更换账号时需要一起复核。

同时实现 [dw_profiles.py](../../games/codol/versions/v3_3_3_3/server/dw_profiles.py) 的公开档案存储，以及 [dw_lobby.py](../../games/codol/versions/v3_3_3_3/server/dw_lobby.py) 的 `8/1` 查询、`8/3` 保存：

| 数据 | 已核对的结构 |
|---|---|
| `8/1` 请求 | typed uint64 用户ID，末尾00；本地首个单用户查询识别当前档案所有者 |
| `8/3` 请求 | 三个typed uint32（实测1、1、CRC32），typed blob压缩体，DDL扩展字段，末尾00 |
| `8/1` 返回对象 | typed uint64 用户ID + 保存的8/3参数，去掉请求末尾00 |
| 压缩体 | zlib解压32768字节，头4字节是后32764字节的CRC32；同时与请求CRC字段相等 |
| DDL扩展字段 | 实测样本含125个typed int32；必须原样保留，客户端还会读取它们覆盖字段，不能仅返回压缩体 |

第二个uint32的完整业务命名未还原，代码称 `format_marker`，只接受本次验证的值1；不把它擅自定义为某版SDK通用版本号。私有档案 `8/2`、多账号认证绑定和任意DDL字段编辑尚未实现。

读取函数 `0x006d7740`、基类读取 `0x00a5a370`、解压 `0x006d7430`、CRC `0x006d7d80` 均已留存：

- [dwProfile反序列化](../../research/evidence/dwprofile-deserialize.json)：`ev_e93e1bd25a0486aa4a4f3110b3c08d06673cb7d5d565358f6f7ff8008ef08837`。
- [基类、解压和CRC](../../research/evidence/dwprofile-base-and-checksum.json)：`ev_a3131473317ad398d2c0eb4a89ded857ea94566263fbf96869bb6606da42b19c`。
- [完整提交来源](../../research/evidence/profile-seq45-origin.json)、[原始参数](../../research/evidence/profile-seq45-parameters.bin)。首份档案从该次真实选角提交初始化，没有伪造角色字段。

## 实际验收

| 时间 | 操作和结果 |
|---|---|
| 12:24 | 直接两个`+set`实验失败；截图见上文 |
| 12:39–12:40 | 新服务PID26704、游戏PID38020，连接127.0.0.1:64775；`8/1`返回1个档案对象 |
| 12:40 | 自动越过角色选择和训练引导，出现游戏大厅、johnClient、等级1、第二角色马库斯，没有繁忙弹窗 |
| 13:02–13:03 | 整理目录后重新启动服务PID50072和游戏PID13836，连接127.0.0.1:54084；`8/1`再次返回1个档案，仍直接进入大厅并显示马库斯 |

[重启后大厅截图](../../runtime/captures/screenshots/20261014-main-menu-after-layout-restart.png) · [重启事件](../../runtime/captures/main-menu-layout-restart-events.jsonl)

[首次大厅截图](../../runtime/captures/screenshots/20261014-main-menu-profile-restore.png) · [首次大厅事件](../../runtime/captures/main-menu-first-events.jsonl)

21项测试通过，新增测试覆盖真实档案CRC、磁盘保存后重载、坏CRC不覆盖已存档案、截断输入拒绝、加密会话保存后新连接读取。首次大厅运行证明客户端接受读取结果；它没有产生新的`8/3`保存，所以不能据此宣称真实客户端更新写回已完成全流程验收。当前保存实现通过离线/加密内存链测试，真实新修改写回仍需另测。引导完成位未被直接改写，当前依赖启动时的覆盖命令。

## 回滚与后续

原始启动脚本及直接参数实验脚本见 [备份目录](../../runtime/backups/20261014-before-onboarding)。回滚应只移除本次引导命令，保留原TGP参数和已保存角色。公开档案在 `runtime/data/public-profiles/`，原始初始化样本保留在研究证据和测试fixtures；不要用全目录覆盖方式回滚玩家数据。

后续先观察真实客户端的`8/3`变更与重载，再还原需要编辑的DDL字段。`9/16`仍返回空结果，但当前大厅能正常显示，不能仅凭该请求为空就认定它会触发繁忙；训练/游戏服务器见 [07](07-session-game-server.md)。
