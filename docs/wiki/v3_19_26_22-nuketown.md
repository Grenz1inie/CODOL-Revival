# 3.19 核弹小镇 9V9

目标：保留原菜单的赛单110；进入等待厅即有一名真人和17个人机，双方各9人。
房间名单、队伍与实际对局共享身份；Rust对局服放在本版本的
`server/native/match-server/`。本轮不修改3.3的DM实现。

## 当前状态

- Rust房间规则与名单：5项定向测试先失败后通过；人数、分队、唯一身份、重入稳定性、错误身份已覆盖。
- 等待厅网络接入：尚未完成。不能将Rust名单生成等同于客户端已经显示人机。
- Nuketown资源挂载、Rust UDP、AI互射、队伍计分与实机可玩：尚未验证。
- 用户本次观察：只有一个人时进入房间即自动倒计时；不要求用户停留在一个无法保持的“Ready前”状态。

## 证据身份

所有地址为3.19.26.22原生x86静态VA。目标EXE SHA-256：
`36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537`。
只读检查的隔离实例PID81072，模块基址为`0x400000`；对象地址为运行时指针，不能再次重定位。

原始捕获的`.text` SHA-256：
`2894b36077fc6fe07e7235bb532c75895928ce69ac0b46bec15184e077199e0c`；
`.rdata` SHA-256：
`0e24e7a86acb4a13d851bad92935cef4169865082a3aca3153970b7687f309b2`。
静态重建镜像`work/codol319-console/analysis-client319.exe` SHA-256：
`4fa4db2b90a3590aea271904096021dcbed28f81dc84b42607e7c9285469cdd3`；不可运行。

| 结论 / 地址 | 来源与覆盖范围 | 未验证项 |
| --- | --- | --- |
| 赛单110为`mp_nuked,cha,1`；18人、150击杀、20分钟 | 当前实例`server/publisher-files/mp_playlists_shipRetail_release.info`解压后的赛单110；资源地址不适用 | 实际对局规则消费与固定队伍出生 |
| `0x7cad60 → 0x7c72b0 → cppSetRoomMembers` | 新REA/Ghidra分析`ev_76308237b63e547234f85696fd1f553f4f55e2bd763a1a9bce3f192f3b2a4fb0`；成员步长`0x1D0`，UID `+0`、名字`+8`、队伍`+0x88` | 服务端名单到此数组的完整消费 |
| `0x82e13fc`房间接口虚函数`+0x78 → 0x62feb0`，数组位于对象`+0xE368`，人数`+0x105D8` | 新REA分析`ev_a5840450ad897403612c2a0c228af370af0e231ef2b6a25be60b59d90a520ebb`；限定ReadProcessMemory交叉核对，当前1人、UID1000001、队伍1 | 新增17个人机后的实际UI与对局 |
| `0x634870`消息分发的`0x0E`分支接收完整成员列表 | 新REA分析`ev_f9fecbe6f72ab854b6bc9a2a1857532bd60866ddcb35a4bab129d6610a1f5ca9`；仅非房主且发送者为房主时消费，之后通知界面；不能直接向当前自建房主推送此包 | 合法远端房间建立、消息封装、原生重放 |

REA新分析产物位于`work/codol319-nuketown/`：
`room-rea.evidence.json` / `room-rea.snapshot.json`、
`room-manager-rea.evidence.json` / `room-manager-rea.snapshot.json`、
`room-wire-rea.evidence.json`。小型分析镜像保留原VA与选定代码页，缺失页不作为已分析结论。
既有登录传输快照已复用；上述房间路径属于新分析，不混称缓存命中。

## 真实回环流量

`room-baseline.pcapng`：2026-10-16 22:49:35至22:56:36，共104包。
SHA-256：`39090eebdd785bf0511168a24230f1845f00c1f2a69bc878a01d34d38880290c`。
过滤范围为TCP31901和UDP28970。

- 帧65：21/5查找赛单110；帧69：11/13；帧73：28/1；帧77、89、93：11/4房间消息。
- 对应服务器返回空成功；捕获区间没有对局UDP流量。控制器对局状态仍为waiting。
- 捕获开始于现有TCP会话中段。密钥由同一端口20029会话的既有握手十六进制日志重建；抓到的双向完整帧均通过HMAC校验。不能声称本次PCAP包含握手。
- `decode_room_capture.py`按TCP序号重组并核对重传重叠、长度及HMAC；未用日志包长度推断帧结构。
- 分帧与加密包校验已核对；房间状态机和原生重放未完成，协议恢复尚未完成。

## 定向测试

```powershell
powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 test --offline --manifest-path "$PWD/games/codol/versions/v3_19_26_22/server/native/match-server/Cargo.toml" --target-dir "$PWD/runtime/builds/codol/v3_19_26_22/rust-match" --test room
```

当前测试只证明Rust规则与成员状态，不证明网络接入或游戏画面。
