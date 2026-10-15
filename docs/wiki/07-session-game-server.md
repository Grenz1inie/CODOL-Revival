# 07 会话与游戏服务器

[总览](README.md) · 上一阶段：[新手引导与角色资料](06-onboarding-profile.md)

**最新状态（2026-10-15）**：真实玩家档案的加密回环已通过出生快照、移动和射击后的弹药减少，均由当前客户端机器码读取。实际大厅服务的查询、预订及开始确认也已通过，新原生实例已启动，可进行首关完整游戏的人工验收；画面、地图加载与实际操作尚未确认。以下训练9/16调查保留为历史记录；本次实现详见文末。

## 症状及当前能确认的事实

用户选第二个角色后停在训练页并报服务器繁忙。12:06 观察时游戏 PID6188、服务 PID13100 均存活且 Responding=True；至12:08:09有大厅心跳，该观察区间无 auth_error/lobby_error。这些是当时的记录，不是现在仍在运行的断言。

最直接的新入口是同一连接 seq51 的 **service9/task16**，参数143字节。真实响应已经独立校验 HMAC 并解密：

```text
transaction=51，error_code=0，task_id=16，result_count=0
payload=0a3300000000000000080000000003100800000000
```

**确认**：服务器返回的是成功码、空结果；UI 仍报繁忙。**推断**：结合训练页，训练会话或游戏服务器查找是候选方向。**未证实**：9/16 的准确操作名称、结果对象布局，以及这个空结果是否直接触发该警告。

## 已做的最小处理与为何还未解决

[dw_lobby.py](../../src/dw_lobby.py)让未知服务返回有正确 TASK_REPLY 包装的 N=0，维持协议推进与证据采集；这并没有创建训练会话，也没有启动实际游戏服务器。

本阶段尚无已验证的修复。不要只向9/16塞一个凭空拼装的 N=1 结果来宣布完成；必须知道客户端如何反序列化和消费结果、是否随后连接另一个端点。

公开 IW6 的 task16 可名为 `find_sessions_two_pass`，但其服务编号为21，而本次是9。**taskID 相同不足以移植操作名和 schema。** 大厅 TCP3074、STUN UDP3074 已应答也不说明对局数据协议已实现。

## 保存的静态调查

原始 EXE 中找到 `MatchMaking_FIND_SERVERS_Query` RTTI。保存的反编译包含 `0x6df690`、`0x702200`，能作为查找对象构造与调用的入口；尚未将它们与本次9/16及 UI 错误分支连接起来。

在当次 REA 已定义字符串范围内搜索 getSessions/findSessions/SERVER_BUSY 返回空，只能描述这次有边界的搜索结果。不能把“没有已定义字符串命中”写成“二进制没有该功能”。

## 证据入口与复核方法

- [实际响应](../../runtime/captures/20261014T040459976482-lobby-response.bin)、[请求51解析](../../research/evidence/character-selection-request-51.json)：`response_mac_valid=true`、事务51、错误码0、N=0。
- [事件摘录](../../runtime/captures/character-selection-events.jsonl)、[完整日志](../../runtime/logs/server.jsonl)、[首次界面警告](../../runtime/captures/screenshots/20261014-after-character-selection-error.png)、[选角记录](../reports/20261014-character-selection.md)。
- [FIND_SERVERS RTTI 引用](../../research/evidence/find-servers-rtti-xrefs.json)：`ev_8b569278cab0af3c80a32c893f7ab67786786693686cf54d4c28412209733af4`。
- [查询相关反编译](../../research/evidence/find-servers-query-decompiled.json)：`ev_f6c40ede7ab6ebdfed42a0e45705fe396e3b37f340b010da4944d764fcbe01fa`；这是候选调用链，不是9/16命名的完成证明。
- [字符串负结果](../../research/evidence/post-selection-session-strings.json)：`ev_a1f1a3456dfa09d23e61b84ccedc86d48a33456ab3a2f8255bc12096d123de5b`。

已有事件可在项目根只读筛选，不需要向正在运行的服务发请求：

```powershell
Get-Content -LiteralPath '.\captures\character-selection-events.jsonl' |
    ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object { $_.event -eq 'lobby_task' -and $_.service_id -eq 9 -and $_.task_id -eq 16 }
```

当前参数日志只截取前128字节，而总参数143字节；完整解析必须从对应原始加密请求及该连接握手重新验证，不把截断的 `parameters_hex` 当完整请求。

## 下一项最小调查与验收

1. 将9/16发送点、参数序列化和结果消费连到同一客户端路径，确认它到底请求什么；保留当前连接时间与 peer，防止重连后的序号误配。
2. 找到返回0个结果时的 UI 分支，与“服务器繁忙”显示建立直接证据；否则仅记为时间相关。
3. 确认所需会话/地址结构后再实现最小对象，观察客户端下一步真实连接，确定游戏服务器协议边界。
4. 以“加载目标地图并进入可交互训练”为本阶段验收；仅去掉弹窗、显示菜单或收到 UDP 均不足。资料写回和重进持久化另验。

12:24 的两参数实验仍停在原界面，详见 [06](06-onboarding-profile.md)；它没有替本阶段提供会话成功证据。本阶段尚未实现游戏服务器。

## 回滚与限制

目前没有真实游戏服务器实现可回滚。后续新增服务/会话响应前保留现有源码和抓包基线；若实验失败，恢复对应服务版本并按授权重启，不改 EXE、系统 CA 或外部网络配置来掩盖未知协议。

当前已完成的链路仍是“本地认证 → 加密大厅 → 发布文件 → 角色选择”。训练/菜单问题、服务器会话和完整对局属于未完成阶段，需分别记录结果。

## 12:40 进入大厅后的补充证据

连接127.0.0.1:64775的seq32仍发送9/16，本地服务仍返回0个结果，但真实客户端已显示游戏大厅和第二角色，没有训练繁忙弹窗。见[大厅截图](../../runtime/captures/screenshots/20261014-main-menu-profile-restore.png)和[事件记录](../../runtime/captures/main-menu-first-events.jsonl)。

因此“任意9/16空结果都会导致当前报错”不成立。训练分支下的具体任务语义和失败条件仍需单独还原；本次通过[引导覆盖和公开档案](06-onboarding-profile.md)避开了此前阻塞，未伪造可用对局服务器。后续对局验收仍需实际会话地址、服务器握手和地图加载证据。

## 2026-10-15 大厅预订与当前连接链路

当前实现：`local_server.py` 启动一个回环原生子进程，只有首关初始化、资源发布校验通过且进程仍存活才提供21/5候选。每个实例使用独立安全ID、密钥、准入名册与档案导出目录；只接受本地玩家及首关 `mp_cargoship / coop_training_mp_cargoship`。停止服务时按记录的隔离路径和PID核验后关闭子进程。原游戏、正式档案和旧参考源码未修改。

REA确认的实际消息路径：

| 步骤 | 当前客户端消费者与实现 |
|---|---|
| 查询21/5 | `0x701db0 / 0xa55700`读取真实就绪实例的地址、安全ID/密钥与服务器UID |
| 预订6/14 | `0x6e48e0`产生`mmbook`，安全ID由`0xa36be0`编码为8字节的标准Base64，不能写十六进制字符串 |
| 接收确认 | **事件21**经`0xa3e980 → 0x6d1d80 → Room::onBook 0x6e6f60`；事件6属于好友收件箱，不是房间消息 |
| 开始 | `0x6e6bf0`构造`mmstart`，`0x6df750`转入连接；服务端仅确认首关，不执行客户端给出的控制台命令 |
| stats | `0x6d81a0`写`index:u8 + length:u16 + ≤1238字节负载`，没有旧版qport；原始数据分27片，末片580字节 |

[28项集中测试](../../research/evidence/server3333-booking-lifecycle-tests.log)通过，耗时2.554秒，覆盖加密大厅请求/应答/推送、实际候选与房间路由消费、身份及关卡限制、实例启动/停止/失败边界和当前stats写入器。原生档案独立探针仍保持跳过；本次实际引擎已成功读取同样的隔离档案导出，不恢复被拦截的临时程序。

连接探针 [probe_native_connection.py](../../tools/probe_native_connection.py)在独立28971端口测试：当前客户端Tiger函数计算会话材料，P224/AES192CTR/HMAC-SHA1握手 → challenge/connect → 当前stats写入器上传 → 当前netchan/gamestate读取器接收首关和CRC `9eaffd84` → 可靠userinfo确认 → `CS_ACTIVE`和出生坐标`(3248,296,364)`。随后实际脚本报`codol_applyProfileCharacter could not compose/publish this player's character`，属于出生后的外观构造失败，不能把已到达出生函数当作能操作。

证据：[连接结果](../../research/evidence/native-connection-latest.json)、[当前房间路由](../../research/evidence/client-room-instant-message423.json)、[事件21读取器](../../research/evidence/client-booking-push21-reader423.json)、[开始命令](../../research/evidence/client-coop-mmstart423.json)、[stats写入器](../../research/evidence/client-stats-writer423.json)、[Tiger消费者](../../research/evidence/client-tiger423.json)。目标SHA-256仍为`e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。探针混合真实引擎、当前客户端机器码及测试网络驱动，不替代完整游戏的渲染与操作验收。

## 最小外观与移动射击的协议验证

修复旧角色读取器仅接受233版旧校验值的问题：当前公开结构为233版、校验值`e32d50d6`、记录14426字节。12个角色、每个9个uint32槽位按捕获的非连续偏移读取；越界、错误结构和无效物品仍拒绝。

出生实际依赖的14份流式模型来自5个`lf_init_common_marketplace*.ifs`。工具[prepare_character_streams.py](../../tools/prepare_character_streams.py)只提取指定名称，先复制IFS、检查原始名称解码并校验前后哈希，安装到隔离`startup-assets/main/models`。原游戏资源不改；来源记录在`resources-character-streams/installed.json`。测试外观为`cha_INFbaseA + han_hands`，装备仍为`defaultweapon_mp`。

[保存的通过结果](../../research/evidence/native-minimal-input-pass.json)包含9个阶段：真实原生实例就绪 → 加密握手 → challenge/connect → stats → gamestate → userinfo确认 → 出生快照 → 移动 → 射击。当前客户端快照读取器完整消费975个实体、1个客户端及EOF；位置从约`(3248,296,360)`变为`(2849,271,336)`，收到`a 1`切枪命令后弹药从10减至0。切枪消费依据`0x57d560 → 0x562260`，没有用手写快照读取器代替。

慢速机器码探针需要完整接收约92KB首帧；增加接收缓冲与执行预算，并将导入桩移出快照栈区。16位传输计数回绕使用完整计数派生加密材料。这些是探针修复，不是游戏性能结论。[29项集中测试](../../research/evidence/server3333-character-input-tests.log)通过，3.604秒；未重复运行完整原生构建套件。

**未覆盖**：探针公开stats为明确标注的最小测试档案，私有档案来自真实只读导出。真实公开存档头部为零，与旧服按头选择结构的行为不同；正在核对当前客户端契约。完整游戏的资源加载、画面和实际输入仍待验收，`gameplay_verified=false`。

REA已保存[当前阶段快照](../../research/evidence/client423-native-connection-stage.rea.json)，含91个workflow、182份evidence。新增全程序分析遇到提供器超时，缓存仍可复用；[定点补充反编译](../../research/evidence/client-stats-focused423.json)来自同一已校验EXE的独立Ghidra `-noanalysis` 作业，不冒充REA Evidence或完整程序分析。

## 真实档案与人工验收入口

随后切换为正式公开档案的只读内容，重现旧服拒绝零头的问题。当前客户端`0x6d7740`直接按档案类型绑定`mp/playerdata.def`并处理CRC和扩展字段；`0x6d7ce0`只在初始化分支写版本头。不能把已被客户端接受的零头存档，简单视为另一版本或损坏数据。

原生读取器仅对**版本头和校验头同时为零、公开结构名、233版、e32d50d6校验值、14426字节布局**的组合使用已挂载定义；不改输入字节，不放宽显式错误版本、私有档案或网络CRC。7项测试先红后绿，最终加上私有结构隔离验证。推导依据见[定点反编译](../../research/evidence/client-public-schema-focused423.json)，与REA缓存的反序列化链交叉核对。

真实玩家当前选择`cha_zombieranger`（槽位8，包10952）。沿实际缺失模型补齐此角色族42份流式模型，仍使用IFS私有副本和原始名称解码。实际私有档案成功装入，公开stats不改头、不替换角色：[真实档案通过结果](../../research/evidence/native-real-profile-input-pass.json)完整通过相同9阶段，读取到位置变化及弹药10→0。默认探针现在读取真实公开档案；`--minimal-profile`才使用前节的明确测试档案。

2026-10-15 14:35已启动服务PID76472及其原生子进程PID72788（PID只记录本次运行）。对TCP3074执行真实加密查询/预订/开始请求，候选与事件21由当前客户端读取器消费；正式公私档案的前后SHA-256均保持一致。见[实际大厅联调](../../research/evidence/native-live-lobby-booking-pass.json)。[最终集中回归](../../research/evidence/server3333-connection-final-tests.log)48项通过，6.453秒。CodeGraph报告最新，GitNexus已按代码白名单刷新。

人工验收由用户执行：

1. 在[本地控制器](http://127.0.0.1:8765/)启动游戏并确认UAC；服务已准备。以后重新启动可用项目根`Start.ps1`。
2. 保持当前角色，进入“玩 → 闯关模式(PVE) → 剧情模式任务 → 身份不明”，点击一次“开始匹配”。
3. 确认进入地图并出现可控制角色，测试WASD、鼠标转向、开火和弹药减少。本轮服务端使用最简单的`defaultweapon_mp`。
4. 若失败，记录停留的界面或报错文字；关联`runtime/logs/server.jsonl`和`runtime/logs/native-instance.json`指向的`main/qconsole.log`，继续从实际断点修复。

这次可以开始人工验证，但尚未声称完整客户端可玩。原版剧情任务、其他地图、其他外观和全面装备兼容仍后置。
