# 12. 独立对局服 Rust 迁移

2026-10-17：服务启动前自动准备核弹小镇地图包；首次需要匹配原游戏、Python依赖及
x86 MinGW GCC，Rust程序仍先按下面命令构建。手动入口及失败恢复见[项目说明](../../README.md)。
包缺失、损坏和Rust产物缺失会提前报告，不再等到对局端口超时才发现。

## 目标与边界

Python 保留网页控制器、认证、大厅、玩家档案与对局预订。Rust 独立进程接管
当前核弹小镇 DM 的碰撞、移动、AI、UDP 握手、输入与快照。资源包、协议、
一名真人＋一个AI＋ACR的规则保持不变；旧服只作算法来源，不运行旧服程序。

此前用户实测：枪手、动作及基本操作已恢复，逐步回拉已消失，仍有高延迟感。
迁移不能把测试通过写成实机手感通过，也不扩大到原9V9、剧情、更多装备。

## 已完成的迁移阶段

1. CodeGraph 梳理 `runtime → matchmaking → server → connection/world`；
   固定地图和输入，保留原实现状态及耗时。
2. 碰撞和导航：同一包的几何、掩码、18单位台阶、256单位局部接入，
   视线遇障即停、射击最近命中。保留未解析模型阻挡语义。
3. 移动和AI：相同输入时间、重放过滤、事件、伤害、换弹、死亡重生；
   保留已验证的手模与组合武器编号。
4. 协议和启停：Rust直接处理UDP；Python用进程管道下发预订并读取就绪/事件。
   网络线程不执行碰撞寻路；模拟线程发布快照，保留正常20Hz节奏。
   Python旧对局循环已退出生产路径，只保留离线迁移对照资料。

## 可重放基线（2026-10-16）

入口 `games/codol/versions/v3_3_3_3/reverse/tools/benchmark_match.py`，原实现基点 `e3ddc7d`。
地图 `runtime/builds/codol/v3_3_3_3/maps/nuketown`，400帧、同一份输入，覆盖移动、转向、开火、
跳跃、换弹、一次125ms慢帧及20帧菜单空输入。结果记录完整玩家状态、
快照字段和封包；浮点状态及对应字段容差1e-6，整数和事件严格比较，
封包的逐字节差异另外统计。
输出目录的 `identity.json` 固定地图文件清单及输入，已有基线不静默覆盖。
跨语言浮点须区分数值和存储字节：400帧的玩家浮点最大差异2.84e-14，
唯一不同的PS字段为13（Y速度，约1e-14的零附近数值），整数全部一致。
65帧完整封包逐字节相同；其余差异单独报告，不能写成400帧二进制相同。
字段和协议位宽由客户端原生向量及同值编码测试保护。

最终采样先停项目服务，Python与Rust串行回放，期间不并行构建或跑测试。
完整本机输出在 `research/evidence/rust-migration-20261016-final/`；
[版本化性能摘要](../reports/20261016-rust-match-performance.json)不包含地图资源或会话密钥。

| 实现 / 阶段 | P95 ms | P99 ms | 最大 ms |
|---|---:|---:|---:|
| Python 模拟（含AI） | 16.116 | 26.820 | 37.935 |
| Python 快照编码 | 67.790 | 72.796 | 77.151 |
| Python 整帧 | 83.747 | 91.605 | 95.863 |
| Rust 模拟（含AI） | 0.493 | 0.847 | 1.773 |
| Rust 快照编码 | 0.742 | 0.947 | 1.401 |
| Rust 整帧 | 1.210 | 1.617 | 2.263 |

这是同一电脑、同一地图和输入的400帧离线样本，不能当作网络RTT或长时间运行上界。
Python快照编码本身超过50ms帧预算；Rust本轮所有整帧均低于该预算。
游戏中的输入手感、瞬移及对战效果仍需人工验收。

```powershell
powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 build --offline --release
powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 test --offline --release
python -B games/codol/versions/v3_3_3_3/reverse/tools/benchmark_match.py --output research/evidence/rust-migration-next --rust runtime/builds/codol/v3_3_3_3/rust-match/release/codol-match.exe
```

## 进程与启停

- `games/codol/versions/v3_3_3_3/server/local_server.py → match_server.runtime → NativeMatchProcess` 启动
  `runtime/builds/codol/v3_3_3_3/rust-match/release/codol-match.exe serve`。Rust直接绑定回环UDP28970；
  Python继续处理认证TCP443、大厅TCP3074及STUN UDP3074。
- JSONL标准输入只承载预订和停止；标准输出返回ready、预订确认及诊断事件。
  大厅收到Rust的预订确认后才返回服务器地址，原事件21及赛单25/轮换0保持不变。
- 模拟线程持有地图和世界状态；网络线程负责握手、收包、ACK与发送。
  双方只交换输入及最新快照；慢帧保留实际经过时间，未改客户端时间倍率。
- 地图状态6仍立即收到首帧，首条有效move后才推进模拟。重连用连接代次隔离旧输入。
  Python关闭管道或退出后，Rust因stdin EOF退出并释放端口。
- `Control-Services.ps1`同时核对Python进程与其指定路径的Rust子进程；四个端口均由
  对应进程持有才返回ready。没有Python对局回退开关；缺少可执行文件时需先构建。
- 旧Python实现移到 `tools/reference_match/`，冻结为离线差分、资源导出与协议研究基线。
  后续对局行为只修改Rust；人工验收后再按导出器实际依赖收缩基线，不维护双生产实现。

## 验证状态（2026-10-16）

- 工具链：项目内Rust 1.99.1 GNU，编译/链接/执行通过；没有修改系统PATH。
- 碰撞/导航：8个定向用例通过，合成Python对照含28条碰撞和7条路线。
- 基线工具：4个用例通过；核弹小镇400帧状态对照通过，逐字节差异如上单独记录。
- Rust移动/射击/伤害/死亡重生5项测试通过，武器读取1项通过。
- 协议库10项测试通过，包括当前客户端DATA/usercmd向量、P-224密钥、可靠命令、
  ACK保留、stats及同值快照编码。UDP主循环的模拟隔离/停止释放端口1项通过。
- Python进程桥接9项、原生运行时/大厅预订5项、PowerShell服务状态6项通过。
  旧基线运行时6项、导航/世界/导出/装备31项通过；搬迁路径造成的1项失败已修正并定向重测。
- 真实Rust子进程UDP集成2项通过，使用当前客户端原生封包/读取探针，覆盖握手、stats、
  地图状态、加载首帧、移动、开火耗弹、断开重连及EOF/stop释放端口。全部使用临时端口，
  不把探针当作完整游戏实机验收。
- 前端“对局”端口文案用例先失败后通过，TypeScript检查及生产构建通过。
  迁移前完整前端回归的其余26项通过；未为单一标签变更重复跑整套。
- 已真实重载项目服务，确认`engine=rust`、父子进程路径和四个端口归属；
  现有控制器`/api/server/status`返回ready。未操作原游戏文件或正式存档。

构建产物与工具链在 `runtime/`，不提交；源码与Cargo锁文件在
`native/match-server/`。后续测试按阶段集中执行，不重复全量扫描游戏资源。

## 人工验收

完全退出旧游戏，从现有控制器重新启动，仍选“冲锋团队竞技 → 核弹小镇”。
依次检查普通移动/转向、跳跃/奔跑、开关菜单后的移动、瞄准/射击/换弹，
再检查AI互射、伤害与死亡重生。重点记录是否还有高延迟感、短距瞬移或回出生点。
测试后保持游戏运行并描述异常，可关联`server.jsonl`中的Rust状态及每5秒帧耗时。
当前状态是代码、协议探针和服务接入通过，Rust版游戏实机验收待用户完成。
