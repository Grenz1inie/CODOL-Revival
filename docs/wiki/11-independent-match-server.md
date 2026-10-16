# 11 独立模拟对局服务器

## 决定与范围

2026-10-15，用户明确停止以旧服务器持续打补丁的路线，改做面向 **3.3.3.3** 的独立模拟对局服。此前“优先复用旧版代码”的要求继续适用于选择性源码移植；不依赖旧服进程或旧安装目录。原游戏 EXE、正式存档和现有认证/商城功能保持原状。

用户随后确认首版改为 **核弹小镇 `mp_nuked`、一名真人、一个服务端AI、一把ACR、自由混战 `dm`**，完成出生、移动、互射、伤害、死亡及重生。Killhouse保留为此前的资源/协议基线；剧情脚本、连杀奖励、全面装备与公网多人不属于这个阶段。

“模拟”指由新服接收输入、维护权威状态并产生当前客户端可消费的快照。预录快照、固定坐标、按请求返回成功或客户端自行减血都不能代替对局实现。

## 核弹小镇参考评估（2026-10-15）

用户提出并批准实施“进入核弹小镇，一名真人与一个AI移动、互射、伤害及死亡重生”，复杂地图效果后置，并指定充分参考相邻 `sh1x_dedicated/`。以下评估保留为实现依据；实际进度见下一节。

- 初始参考菜单的核弹小镇是赛单110、地图 `mp_nuked`、玩法 `cha`（原9V9）。恢复赛单目录不会自动切换服务端地图；后续已按用户纠正复用此入口接入本图最小DM规则，见下一节。
- 3.3.3.3客户端目录已有 `ff_init_mp_nuked_V32.ifs`、`lf_init_mp_nuked_const_V37.ifs` 及对应流式包。这里只确认文件存在，未声称本图碰撞、出生点、基线和资源注册表已成功导出或完整匹配。
- 参考包 `bin/home/main/waypoints/mp_nuked_wp.csv` 实际有235个点，与首行数量一致。含站立、蹲伏、卧倒及攀爬标记；当前独立服只走站立可达路径，须将路径与新版碰撞核对，不能保证所有235点都可直接使用。
- `bin/home/codol_rawfiles/maps/mp/mp_nuked.gsc` 是薄初始化层：调用特效、通用多人加载、小地图设置和阵营设置。最小人机对战可先后置其环境特效；墙体、地面、出生点、射线遮挡和客户端必需资源不能一并略去。
- 参考源码README明确目标为1.1.1.13。算法、地图数据格式和调用顺序可参考；旧版内存布局、资源编号、网络字段仍以当前3.3.3.3的REA证据为准。

已通过CodeGraph与GitNexus定位的复用点：

| 参考位置 | 可复用内容 | 当前独立服对应位置 |
|---|---|---|
| `src/sv_main.c` 的 `SV_SpawnServer` → `CODOL_BotNavLoadForMap` | 每张地图加载其独立寻路数据 | `runtime.py`、`navigation.py` |
| `src/codol/player/codol_bot_nav.c` | CSV解析、节点连接及寻路 | `navigation.py`、地图资源包 |
| `SV_BotUserMove` → `CODOL_BotBuildCommand` | 目标选择、瞄准、移动、开火/换弹指令；AI同样通过输入驱动角色 | `world.py` 的AI、移动与武器路径 |
| `src/codol/snapshot/codol_sv_state.c` | 地图身份、serverinfo、注册表与初始状态保持一致 | `connection.py`、`runtime.py`、`mapdata.py` |

核弹小镇隔离资源包及地图身份接入已经完成。2026-10-16修正握手、stats、初始地图编号、首帧时序和基线标记后，完整游戏已显示核弹小镇场景及HUD。慢动作配置补齐后，用户确认主动抬头、移动和转向基本正常；发布组合ACR后，用户确认枪体出现、动作能播放，但枪和手仍错位。当前继续定位模型与动作绑定；实际耗弹、互射伤害和重生效果尚待人工验证，不能宣称完整对战已通过。

保留完整原菜单，复用“冲锋团队竞技 → 核弹小镇”入口，使用最小自由混战规则，说明标明1真人＋1AI；不把这个入口标成原9V9玩法已恢复。核弹爆炸、环境事件、破坏物、连杀奖励及高级AI动作均可后置；静态碰撞与射击遮挡先保持一致。核弹小镇可作为首个样板，不必将Killhouse实机验收作为额外前置，但共同握手/出生链路仍必须完成。

参考目录已建立局部索引：CodeGraph为1431文件、27510节点；GitNexus别名 `sh1x-dedicated-reference`，44534节点。范围为 `src/` 与 `tests/`，配置是参考目录的 `codegraph.json` 与 `.gitnexusignore`；GSC、寻路CSV及地图包仍直接按路径读取，不伪称已形成GSC调用图。少量旧头文件无法解析、部分跨语言/函数指针调用不完整，缺边不能推成无调用。未编译或运行旧服，未改动其原有源码。

## 等待连接定位（2026-10-16）

本轮来自用户00:04（Asia/Shanghai）的真实重试，捕获限定32条，保存在 `runtime/captures/match-connection-trace.json`。该文件含临时会话材料，保持Git排除。只读CDB模块/线程栈在 `runtime/logs/match-debug.txt`；没有设置断点、修改进程或游戏EXE。

已完成的两处修复：

1. **房间开始命令**：实际文本为 `playlist 25; start_map_rotate_once 0`。不是选错地图：原生 `0x613330` 将目录ID110转换为当前有效赛单中的紧凑索引25，`0x6132e0`反向得到110。此前服务端比较110并要求轮换值大于0，两项均拒绝合法请求。现在只接受对应25及非负轮换参数，仍拒绝其他赛单、地图和玩法；不执行任意控制台文本。
2. **challenge请求**：真实客户端使用 `getchallenge 0 "玩家ID"`，格式字符串在 `0xc6119c`、调用在 `0x465d32`。服务端补齐该格式并保留旧探针格式，两者都绑定已预订账号；畸形参数不能进入connected。

两处均先复现失败再修复：连接边界11项通过，赛单/菜单边界5项通过。菜单测试保留中文、分类、顺序、UI类型和地图；新测试执行原生双向索引转换，不以Python映射自测代替客户端证据。尚未将这些结果表述为实机出生成功。

加密修复已应用：参考服的Tiger192/AES-192组合不适用于本次客户端。当前 `0xa7af90` 将28字节P-224共享X与16字节预订密钥拼接后做SHA-1；AES使用前16字节。`0xa7f960` 的IV来自32位完整序号与16位目标tag的SHA-1前16字节，CTR按小端递增；HMAC覆盖头6字节及长度2字节和密文，结果截取8字节。

验证使用 `tests/client_transport423.py` 执行当前EXE的DATA封包、SHA-1、HMAC和AES-CTR机器码，仅隔离CRT内存分配。服务端输出与原生输出逐字节相同；覆盖完整32位序号跨65535、方向tag、分块载荷、错误认证、长度和重放。4项传输测试加6项UDP/探针测试通过，UDP路径继续到stats、gamestate、active及移动射击输入。旧参考服探针保留默认旧协议，独立服用例显式指定 `current=True`，避免把旧版自我往返误当新版握手证据。

另用已捕获的临时服务端密钥重建COOKIE_ACK，与实抓响应完全相同；新的生产 `Association` 成功认证并解密全部30条DATA，首个真实getchallenge已由生产 `Connection` 生成challengeResponse。秘密材料仍仅在忽略目录中。01:18（Asia/Shanghai）完整游戏重试已到 `match_phase=connected`，随后反复被 `invalid stats size or CRC` 拒收；不再把后续等待归因于握手加密。

### 对局stats与存档CRC的区别

使用缓存REA `client-stats-writer423.json` 与当前EXE反汇编定位：`0x6d81bf` 调用 `0x6d7d80` 计算CRC，接着 `0x6d81c5` 调用 `0x6d8a70` 整理档案，之后 `0x6d80d0` 压缩发送。该路径没有重新计算CRC。原生CRC函数在Unicorn中算出的值与标准CRC32一致，排除了多项式和范围差异。

01:50的限定CDB硬件执行断点捕获了同一次调用的三个32KiB缓冲区（状态指针 `EDI+0x7c`）：

| 时点 | 头4字节 | 当前正文CRC32 |
|---|---|---|
| CRC调用前 | `da6e92b5` | `aca96c21` |
| CRC调用后、整理前 | `aca96c21` | `aca96c21` |
| 整理后、压缩前 | `aca96c21` | `da6e92b5` |

值按uint32表示。整理步骤改变7452个正文中字节，头部保持旧值。此前实抓的stats同样仅头4字节与大厅保存的公开档案不同；密文HMAC认证与zlib解压均通过。参考 `sh1x_dedicated/src/codol/stats/codol_stats.c` 的对局接收器也没有套用大厅存档的整块CRC契约。

因此 `StatsTransfer` 保留已认证DATA、连接身份、分片顺序/长度/重复内容检查、zlib完整性及精确32768字节边界，按原样接收对局stats，不拿其旧CRC检查整理后的正文。大厅公开/私有档案保存的CRC规则不变，也不将上传缓冲区写回正式存档。回归通过原生stats封包器覆盖压缩/未压缩及旧CRC上传；损坏zlib、尾随数据、错误尺寸仍拒绝。连接与UDP共15项通过，大厅存档5项通过。

复现工具为 `tools/Read-MatchDebug.ps1 -Stats`，使用三个硬件断点，不改EXE代码字节；第三次命中后脱离。需在新启动、首次匹配前附加，后续重试会复用压缩缓存。原始缓冲区位于忽略目录 `runtime/captures/stats-20261016-014425-*.bin`，包含玩家数据，不提交。调试后客户端上报异常并退出，此次只用于取证；可玩性验证须使用不附加调试器的独立重试。

### 首个netchan的地图编号

01:59未附加调试器的完整游戏已完成stats，界面由“等待连接”推进到“设置游戏”，但服务端拒收首个netchan，原因是 `invalid client sequence or server id`。02:05的限定抓包记录在 `runtime/captures/match-connection-trace-20261016-020046.json`：首包明文为 `0100000000000000000000000036`，序号1、server ID 0、两项ack 0；本次challenge为535873589，末字节解码为EOF 3。该14字节包不含玩家数据。

REA缓存 `client-send-command423.json` 的 `0x4602a0` 读取当前地图状态的首字节作为server ID；首次尚未收到gamestate时为0。此前测试构造255掩盖了这个边界。现在只在connected/primed、ack均为0时接受初始ID 0；收到地图确认后仍拒绝0。新增用例直接回放上述真实首包，覆盖重复首包及后续编号检查；连接与UDP共16项通过。完整游戏是否消费gamestate另行记录，不用此测试声称出生成功。

### 加载完成后等待首帧

02:26（Asia/Shanghai）完整游戏依次发出 `gamestateupdate 1..6`，只读CDB确认 `0x1a2e7ec=9`、已接收序号1、NCS值 `0x2df7d90=0x69355ea4`（1765105316）。客户端正常CRC比较已通过；这比离线读取器证据更强，但不表示全部模型、武器及渲染路径兼容。原始材料在 `runtime/captures/match-connection-trace-20261016-022157.json` 和 `match-client-state9-20261016-022630.txt`，均不提交。

本次实抓先发送14字节初始netchan，完成加载回报后不发送move，等待服务器首帧；原独立服却要收到move才发首帧，形成互等。`server.py` 改为在primed且首次收到阶段6时发送两名玩家的初始状态和武器选择，仍须真实move才能进入active并推进模拟。阶段1..5及重复阶段6不启动AI、不重置世界。新UDP回归先复现首帧等待超时，再由当前客户端快照读取器验证初始玩家数据，并继续检查输入、移动、扣弹和伤害；连接/UDP共16项通过。

`Read-MatchDebug.ps1 -Connection` 仅只读提取当前状态、NCS及netchan计数；`trace_match_connection.py` 当前限定128条双向加密/解密记录，含临时密钥，仍仅写入忽略目录。两字节 `<3` 是已认证的底层保活，不是玩家move；它在首帧等待期出现，不能单凭这条消息声称输入解析失败。

### active后黑屏：基线帧不参与绘制

02:34完整客户端接收首帧并发回第一条move，服务端进入active。只读CDB确认客户端 `0x1a2e7ec=10`，快照序号持续增加，CG已持有快照，主线程仍在正常帧循环；截图却全黑。原始状态保存在忽略目录 `runtime/captures/match-black-draw-gate-20261016.txt`。

沿当前EXE `0x46f170 → 0x524890` 追踪：`0x5263c6` 检查CG快照标记 `flags & 0x0a`，非零时直接跳过绘制。原编码器一直设置8；它能被网络读取器消费，也能令连接变为active，却不能显示场景。参考 `sh1x_dedicated/src/codol/snapshot/codol_sv_snapshot.c` 同样区分基线和正常帧；当前解析器 `0x46d170` 要求无delta的正常帧已有固定基线，因此不能只清除标记。

最小修正：每个独立连接先发送一次空基线（flag8），随后世界帧用flag0、delta0并相对这份固定空基线编码。保留完整玩家、库存和地图实体；不增加增量压缩或修改客户端。回归扩展到原生 `CL_GetSnapshot 0x4f8fa0` 和 `CG_DrawActiveFrame 0x52639e..0x5263df` 的早退判定：旧行为在UDP测试等待可绘制帧超时；修复后基线仍被跳过，正常帧通过，后续移动、扣弹和伤害继续成立。快照、世界、连接、UDP共31项通过；该判定仍不等于实际渲染或人工操作验收。

02:59完整游戏首次显示场景与HUD，截图 `runtime/captures/screenshots/20261016-030439-admin-move-fire.png`。03:04管理员脚本按W半秒并单击一次，服务端玩家坐标、弹药没有变化，武器与手部仍未显示。只读调试工具补充快照、CG持有快照、帧时间与最新输入命令；未写进程内存。

### AI缓坡卡死与寻路阻塞

实际AI在 `[798.385,878.814,-64]` 陷入地形三角面4834，随后每500毫秒模拟时间重算无法到达的路径，约耗26秒真实时间。最小复现保留一片斜面和进入/离开接触点：SAT将前次接触点的舍入误差算成极小负进入时间，丢失法线，下一步穿入地面。

`collision.py` 保留真实进入时间和法线，仅把现有接触容差内的负时间夹到0。新用例先失败后通过，原移动、射击及寻路共13项通过；没有扩大导航可达范围或忽略碰撞。实际地图离线模拟469步后AI扣弹并将真人生命从100降到70，用时42.25秒、最慢单步2.16秒；已越过原卡点，但尚未达到稳定20Hz，不以此替代实机对战验收。

## 当前方案与参考源码

### 核弹小镇接入（2026-10-15）

- 赛单版本801按用户纠正移除新增分类6和赛单240，复用“冲锋团队竞技 → 核弹小镇”（分类1、赛单110），保留名称和位置。此入口使用 `mp_nuked,ffa,1`，客户端已有 `ffa → dm` 映射；规则与说明为1真人＋1AI、ACR、自由混战，其余赛单不变。
- 版本802修复801误删 `ranked` 的回归。原客户端 `GetPlayList`（`0x6ab670`）调用 `0x613ed0`，在 `0x6ac42b` 将结果发布为UI字段 `type`。801中110仍存在于分类和地图表，但类型从1变成0；只补回 `ranked` 即恢复1，地图及1V1规则无需回退。`tests/test_client_playlist.py` 已保护冲锋分类七个赛单的名称、顺序与真实客户端UI类型，以及110的地图/规则说明、无新增入口；修复前定向用例报 `0 != 1`，修复后通过。该测试执行当前EXE机器码，未执行Flash渲染，最终显示仍由用户复审。
- 本次对照证据为 `research/evidence/nuketown-menu-type423.json`；REA新反编译请求再次300秒超时，结论来自原EXE汇编与机器码执行，未冒称新反编译成功。23:15:33（Asia/Shanghai）服务PID52332已就绪，重登后发布802。
- `runtime → matchmaking → MatchServer → Connection` 传递包内地图身份，连接响应、serverinfo及gamestate使用同一地图名；当前客户端机器码读取器已消费Nuketown的状态。
- REA已保存的 `client-coop-mmstart423.json` 中 `0x6e6bf0` 证明PVP有 `playlist …; start_map_rotate_once …` 分支，不能只识别 `map`。核弹小镇目录ID为110、实际网络索引为25（见上节纠正），也接受明确的 `map mp_nuked` / `g_gametype dm`；不执行客户端任意控制台文本。
- 参考源码 `src/codol/net/codol_network.c:359–371` 的明文bdNAT INTRO发生在加密INIT前：29字节 `0d 02 00` 请求原样回显，仅类型改成 `0c`。已补入独立UDP入口，保留客户端MAC与地址，不提前占用预订。定向测试先复现超时，再验证回应和后续INIT_ACK。
- 此前实机日志只记录29字节及 `DATA before handshake`，没有包头，不能仅凭长度认定所有失败包都是INTRO。新日志记录前6字节，供下一次人工测试区分NAT与真正的加密DATA；游戏出生仍未实测。
- REA恢复现有快照成功；新字符串查询在300秒超时，本轮使用已有REA命令链证据与参考源码，没有把缓存恢复表述为新完成的全量分析。

核弹小镇资源已导出到 `research/experiments/independent-match/nuketown-loadout-v2/`，34个文件，原游戏与正式档案未写入：

- 当前签名FF423中提取本图碰撞、302个出生点记录（其中30个DM点）、98个基线实体；盒体落地检查接受27个DM点。
- 冻结DM碰撞包含5395个世界brush、1142个地形分区、158种静态XModel、72834条模型三角形及32个真实初始姿态的内联模型。保留材质/碰撞掩码，不用包围盒冒充真实模型；55个其他模式、工具、玻璃或渲染对象明确排除，1个基线模型无碰撞几何。
- 快照保留94个type6实体；另外4个为 `ET_FX=8` 环境特效（实体668–671，参考 `sh1x_dedicated/src/entity.h`）。本轮不发送这4个特效，原始基线仍完整保存；其他未知类型仍报错。客户端读取器消费94个地图实体及2名玩家，共96个实体。
- CS16中心 `[1090,5791,1933]` 由实际网络实体、DM出生点、路点及零差分基准确定。远景BSP范围不参与网络位置窗口，原始碰撞仍完整保留；后续越界实体仍由编码器拒绝。
- 本图NCS候选CRC为 **1765105316**，角色/手部/ACR编号为109/53/5。`mounted_set_verified=false`：当前客户端读取器通过不表示实际游戏的挂载集合已匹配，保留正常CRC比较。

一次真实UDP加密握手、stats、gamestate及snapshot读取已通过，记录在 `research/evidence/nuketown-independent-smoke.json`。其范围是当前客户端机器码消费，未执行完整游戏渲染；不能据此声称已进图或可操作。

REA快照另存为 `research/evidence/client423-nuketown-entry.rea.json`，93项工作流、184条证据，绑定同一下述客户端SHA-256。继续恢复该快照，不重复已超时的字符串扫描。

### 核弹小镇资源重建

以下命令在项目根执行；输出目录必须不存在。已有中间包保留，重新导出时统一换新目录名。只把最终34文件包部署到运行目录，不提交游戏资源。所有注册表输入先校验签名FF及客户端哈希。

```powershell
$env:PYTHONPATH='src;tests;tools'
python -B tools/extract_story_resources.py --map-name mp_nuked --output research/experiments/independent-match/nuketown-inputs-v1
python -B tools/build_match_registration.py --map-name mp_nuked --ff-directory research/experiments/independent-match/nuketown-inputs-v1/chinese --output research/experiments/independent-match/nuketown-registration-v1
```

首次地图导出使用 `export_zones` 的地图参数：

```powershell
@'
import json
from pathlib import Path
from decode_story_fastfile import decode
from export_match_map import export_zones
base=Path('research/experiments/independent-match')
reg=base/'nuketown-registration-v1'
sources=json.loads((reg/'sources.json').read_text())
ncs=json.loads((reg/'ncs.json').read_text())
client=Path('../CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe').read_bytes()
records={r['name']:r for r in sources['fastfiles']}
zones={name:decode(client,Path(records[name]['path']).read_bytes(),name)
       for name in ncs['selected_zones']}
export_zones(zones,base/'nuketown-dm-v1',map_name='mp_nuked',gametype='dm',
             source_records=records,registration=ncs['registration_evidence'])
'@ | python -B -
python -B tools/export_match_map.py --from-package research/experiments/independent-match/nuketown-dm-v1 --model-zone research/experiments/story-native/zone-assets/common_mp/zone.bin --output research/experiments/independent-match/nuketown-dm-v2
python -B tools/export_match_loadout.py --source research/experiments/independent-match/nuketown-dm-v2 --output research/experiments/independent-match/nuketown-loadout-v1 --common-zone research/experiments/story-native/zone-assets/common_mp/zone.bin --waypoints ../sh1x_dedicated/bin/home/main/waypoints/mp_nuked_wp.csv --registration research/experiments/independent-match/nuketown-registration-v1
python -B tools/export_match_map.py --from-package research/experiments/independent-match/nuketown-loadout-v1 --model-zone research/experiments/story-native/zone-assets/common_mp/zone.bin --output research/experiments/independent-match/nuketown-loadout-v2
```

最后一步将包内路点纳入坐标窗口并重新生成哈希。旧路点只作为图结构输入，运行时仍须以当前地图碰撞确认可达性。动态尾部1413777字节原样保存；玻璃破坏、脚本驱动物体与复杂环境效果不属于 `dm_frozen_initial_static` 就绪范围。

独立服源码位于 `src/match_server/`，已接入现有认证/大厅，当前资源独立保存在 `runtime/match/nuketown/`；旧Killhouse包保留。`local_server.py` 已替换 `NativeServer`，启动时读取地图、碰撞、武器与寻路数据；查询时为当前账号建立回环UDP实例。**自动验证覆盖协议消费和服务端模拟；完整客户端开图、画面、操作及对战仍待用户验收。**

| 对象 | 实际作用及状态 |
|---|---|
| `sh1x_dedicated/` | 源码/算法参考；用户已允许必要修改，相邻 `.7z` 为保留归档。本阶段未修改它，也未启动其中的服务器 |
| `reference-source/` | 从用户提供的 `native-source.zip` 提取的另一份同源参考，保持不可变 |
| 用户更正后的相邻 `Server/` | 12份发布配置，没有对局程序或源码；播放列表提供分类、FFA→dm和地图入口语法参考 |
| `server3333/` + `server3333.patch` | 旧引擎源码加新版适配后重新编译的实验；尚未完成完整客户端对局验收，停止扩展 |
| 当前客户端读取器与REA证据 | 新服可继续采用的协议验证依据；必须绑定当前EXE哈希 |

本次逐文件对照：两份参考的 `codol_bot_nav.c` 完全相同，SHA-256为 `9e928b94b009f5de45b696b356850881ed6712da39a970948d5f9042a2681518`；`codol_bot.c`、`codol_sv_state.c` 分别有53、93行增删，新增参考缺少现有参考的一部分目标版本资源适配。两者不能视为可直接替换的3.3.3.3实现。

REA会话已保存为[独立服参考基线](../../research/evidence/client423-independent-server-baseline.rea.json)，保留92项工作流及183条证据，本轮恢复后继续复用。绑定客户端SHA-256 `e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`；持久化证据不代表新服实现通过。已超时的整段反编译/xref不再重复扫描，缺失调用参数使用对应地址的汇编核对。

旧PVP实验在方向切换前已挂载Killhouse资源、读取181个寻路点，随后因 `projectile_cbu97_clusterbomb_lod010` 缺失失败。新版MP/地图包另提取43份模型流，哈希无冲突；没有继续开图验证。保留[失败日志](../../research/evidence/pvp-startup-icons.log)和[资源记录](../../research/evidence/server3333-pvp-model-streams.json)，不再沿旧服的完整脚本预加载逐项补模型。

## 新实现的边界

```text
现有认证/大厅 → 查询与预订 → 独立对局服
                              ↓
             3.3.3.3握手、可靠消息、输入解码
                              ↓
          当前地图碰撞 + 玩家/武器状态 + AI
                              ↓
                3.3.3.3资源编号及快照编码
                              ↓
                          原版客户端
```

| 层 | 复用依据 | 新服必须拥有的责任 |
|---|---|---|
| 大厅接入 | `dw_matchmaking.py` 的查询、事件21预订与准入验证 | 只发布真正完成地图准备的实例，开始请求绑定所选地图 |
| 连接与传输 | 当前客户端消费过的加密握手、stats、netchan、可靠消息证据 | 独立连接生命周期、分片、序列与确认；不启动旧服务器 |
| 初始地图状态 | 当前资源注册表、CRC与gamestate读取器 | 从本版本资源生成初始状态，不把旧服捕获回放当生产实现 |
| 移动与命中 | 当前地图碰撞数据；旧源码中的可分离算法 | 碰撞、遮挡、输入时间及武器状态；直接使用新服状态，不经旧引擎布局中转 |
| AI与重生 | 旧服寻路、目标选择和玩法流程 | 由与真人相同的移动、武器、伤害接口驱动AI；死亡后按实际状态重生 |
| 输出 | 当前客户端机器码读取器、已有字段差异证据 | 直接编码3.3.3.3玩家、实体、资源编号和事件，验证客户端消费结果 |

源码复用以可分离模块为单位，保留原始来源与许可证。不能把旧EXE换名，或再包一层Python启动器后称为独立服。也不需要为了服务器启动而恢复客户端纯渲染材质或无关连杀奖励；模型中参与碰撞、命中或协议引用的数据仍须准确处理。

## 开发次序与验收

沿用已确认的测试边界，每个阶段先建立失败用例，再实现最小通过路径，不一次写完假设中的整套测试。

1. **独立连接与出生**：隔离端口完成预订、加密握手、stats、地图状态和两名玩家的初始快照；由当前客户端读取器验证。启动依赖中不得出现旧服EXE或旧安装目录。
2. **权威移动和射击**：同一地图上的输入导致合法位置和弹药变化，墙体阻挡移动及射线；客户端消费结果与新服状态相符。
3. **一名AI完整对战**：AI通过同一输入路径移动/开火，双方伤害、死亡、重生均进入快照；避免直接扣血或传送冒充交互。
4. **用户集中验收**：完整游戏加载核弹小镇、双方可见、真人与AI互射、伤害及重生。此前只报告自动验证阶段，不提前通知“已可玩”。

新源码放在 `src/match_server/`，协议测试及真实客户端消费探针放在现有 `tests/`、`tools/`；资源与运行产物继续分别放在 `research/`、`runtime/`。接线时才替换 `local_server.py` 中旧后端，并同步服务启停与控制器状态。

## 独立连接阶段（2026-10-15）

- 初版 `crypto.py`、`transport.py` 沿用参考的Tiger192、P-224、AES-192 CTR与DATA HMAC。2026-10-16真实抓包证实其中密钥派生、AES位数、IV和认证范围与当前客户端不匹配；早期回环测试不能作为3.3.3.3加密兼容性证明，纠正见上节。
- `connection.py`：单一预订账号校验、challenge/connect、stats分片与压缩边界、可靠userinfo确认、当前版本gamestate；不写正式玩家档案。
- `server.py`：只绑定 `127.0.0.1` 的独立 UDP 收发。`tests/test_match_server.py` 经真实 socket 和加密层，把地图状态交给当前客户端读取器；确认解析出 `mp_killhouse_sh / dm`。
- stats的uint16是**压缩后总长度**，不是本分片长度；每片最多1238字节，未压缩长度32768。首4字节是整理前的CRC，不能用于校验上传正文（2026-10-16动态证据见上节）。只有全部合法数据齐备才允许地图状态发送。

测试分别使用客户端 `0xa87020/0xa87060/0xa87110`（Tiger）、`0x6d81a0`（stats writer）、`0x5a5960/0x46bf80`（netchan/XOR）和 `0x46dea0`（gamestate）。最后一项在 `0x4651b0` 加载入口停止，**未执行渲染、资源加载或出生**；测试中的 NCS CRC 是协议夹具，不是已经核实的 Killhouse 实际注册表。

REA 已恢复原快照；本轮重复反编译请求300秒超时，未取得新结果。继续使用绑定相同客户端哈希的 `client-tiger423.json`、`client-stats-writer423.json`、`client-connectionless-current423.json` 及机器码验证，不把快照恢复称为新分析完成。

定向验证：

```powershell
$env:PYTHONPATH='src;tests;tools'
python -m unittest test_match_transport test_match_connection test_match_server test_story_wire423 -q
```

## 输入与玩家快照（2026-10-15）

### ACR只显示手部：基础定义不是完整枪体（2026-10-16）

用户澄清截图是主动抬头，移动和转向基本正常；不能从天空画面推断角色掉出地图。非暂停读取 `viewweapon-model-binding-20261016.txt` 发现DObj的手模型为 `viewhands_player_tf141`，第二模型实际为 `tag_origin`（3骨骼、1表面）。DObj隐藏位全零，父骨骼12对应真实 `tag_weapon`；因此已有DObj、资源就绪及绘制开关不等于已绑定正确枪体。无需猜动画0、PS开关或换用旧DObj布局。

参考 `sh1x_dedicated/src/codol/weapon/codol_weapon_compose.c::load_composed_with_base` 的组合流程，再核对当前EXE（SHA256以 `e3823fd6` 开头）的实际消费者：

| 当前地址/数据 | 已证实的契约 |
|---|---|
| `0x46da00` | 网络recipe解码为 `** 5 0 0`：基础武器5、普通涂装0、附加字段0、无可选配件 |
| `0x42e414/0x42e49b` | 找到基础定义并复制为组合定义 |
| `0x42c3e0`、`0x445c54..0x445c79` | 在351个基础槽后注册352；客户端检查CS编号减5443等于实际注册ID |
| `0x42c05a`、`0x42c253` | 当前ACR组合继承备用弹药键5，独立弹匣键为352 |
| `0x558d57 → 0x42e800` | 使用组合记录 `+0xfac` 的viewmodel，成功后不走基础定义的 `tag_origin` 回退 |
| `live-acr-models.json` | PID55400只读提取的 `mp/coweapmodels/acr_mp.csv` 第0涂装指向 `wea_acr_acr_blk` / `wea_acr_acr_blk_vmgun` |

最小修改在 `match_server/runtime.py`：从NCS实际数量分配下一个槽，发布CS5795的recipe，同时使玩家选枪、库存、世界武器和弹匣使用352，备用弹药仍为5。不覆盖基础CS5448，不改变地图NCS校验和，也不写客户端文件。原有隔离资源包已经包含基础ACR参数与NCS，本轮无需重新导出地图或复制模型到服务端。

测试先复现原先返回 `(weapon, ammo, clip)=(5,5,5)` 及注册表满时仍允许发布，修改后6项runtime用例通过。新增原生回归覆盖组合注册键、viewmodel选择；runtime测试让实际客户端读取gamestate与快照，确认选中/持有/弹匣352及一次开火扣弹、伤害状态。模型选择测试提供已解析的资源夹具，在骨骼处理前停止；它不证明实际网格已加载或渲染正确。

空配件列表不会自动补 `mp/coweapitemswea.csv` 的默认部件；`0x42dd65..0x42dd74` 仍保留一个基础枪体模型。因此当前先恢复基础枪体，完整网格、默认部件和动画以实机结果为准，不把配件影响一概视为纯外观。REA新反编译本轮再次超时，未重复扫描；本节新增结论来自已保存的当前EXE汇编、原生执行测试及限定只读采集。

09:11项目服务重载为PID61972，日志确认 `mp_nuked / dm`、NCS校验和1765105316。用户需完全退出旧客户端，从控制器重启，再经原有“冲锋团队竞技 → 核弹小镇”入口检查基础枪体、左键耗弹、R换弹及AI受击；端口监听不作为这些画面行为的验收。

### 枪手错位：区分第一/第三人称与缺少默认部件（2026-10-16）

用户确认动作能播放但枪手错位，随后转述“枪的模型调用错误、可能混用第一/第三人称，动作不通用”。按此线索核对实际消费者，不能仅按资源名或view列判定整套姿态正确：

| 核对项 | 当前证据 |
|---|---|
| 模型选择 | `0x707b17/0x707b40` 分别取表中world/view列，写入组合记录 `+f68/+fac`；第一人称 `0x558d85 → 0x42e800` 固定读 `+fac` |
| 实机模型 | DObj为 `viewhands_player_tf141`（66骨）和 `wea_acr_acr_blk_vmgun`（25骨）；world版本 `wea_acr_acr_blk` 为18骨，并非当前选中的模型 |
| 主枪挂接 | DObj父骨骼12为手部 `tag_weapon/032d`；idle映射 `0330` 到枪根骨66，尚无证据要求移除这个挂接 |
| 动作来源 | 原始ACR与组合Def的idle都是 `viewmodel_m4a1tech_idle`，不是本项目写入；开火/换弹另有ACR动作，不能按M4A1名字直接判成第三人称动作 |
| ADS状态 | `0x556b10` 由 `PS+34c` 驱动节点36/37的采样时间；未瞄准时节点37时间1、速率0是正常端点，不是异常满ADS |

确定遗漏的是默认枪口、枪托、握把、弹匣和机械瞄具。`mp/coweapitemswea.csv` 将它们标为默认，`mp/coWeaponAttachmentTable.csv` 对应 `nop`，不会替换原始动画。当前 `0x42c6a0` 按名称注册14位槽，`0x42e44d` 直接读取槽内字符串；不是旧服的marketplace序号或item/variant对。PID52008只读确认五槽分别为 `1690=muz_default`、`2683=sto_default`、`2385=gri_default`、`9641=mag_default`、`13370=iro_default`，已排除这五项的哈希碰撞。CS5795现在发布：

```text
** 5 0 0 1690 2683 2385 9641 13370
```

runtime原生gamestate回归先复现空部件配方，再验证完整配方、武器/弹匣352和备用弹药5。原生模型选择回归提供不同world/view资源夹具，检查主枪及五部件只取view，保留各自tag和主枪的 `tag_weapon`；只隔离资源流式加载调用，不把该测试当作渲染或动画配套验收。相关server/runtime/composed共13项通过。

证据：`research/evidence/acr-model-pairing-20261016.json`、`acr-model-pose-20261016.txt`、`acr-animation-pose-20261016.txt`、`acr-animation-source-20261016.txt`。`Read-PlayerSchema.ps1 -WeaponModels` 复用限定只读采集；`tools/Read-MatchDebug.ps1 -ViewAnimation` 读取当前枪模动作树，最多64节点。REA已存证据继续复用；本次新指令查询返回 `Ghidra client is already started`，没有反复重扫，新增地址结论以本版本缓存汇编和实机读取交叉核对。

10:28服务重载为PID61288，同时带入输入排队及UDP退出修复，确认 `mp_nuked / dm`、NCS校验和1765105316。默认部件完整性和枪手姿态交由人工检查；目前没有证据宣称错位已修复，也未替换原始客户端的模型、骨骼或动作文件。

### 保留已确认的输入基准帧（2026-10-16）

时钟修复后的08:36会话已经进入active，随后日志大量记录 `client acknowledged an unsent message`。原检查把“确认了尚未发送的序号”和“确认帧已被64帧缓存淘汰”合并，单凭旧日志不能判定每个失败属于哪一类。

定向复现使用当前客户端的原生usercmd writer：先确认一帧武器5，再发送80帧武器7；客户端仍以已确认的武器5为差分基准。原实现删除该基准并拒收，修复后解出武器5、前进及开火。缓存只额外保留最后确认帧，确认推进后正常淘汰；未来序号、已过期基准和重复包的边界分别受测试保护。失败日志现在区分未来确认和过期基准，方便核对实机后续结果。

`test_match_connection`、`test_match_server` 共20项通过。该回归证明缓存缺陷及修复，不将旧日志所有拒收都归因于它；真实会话是否还会拒收须重载后观察。

### 模拟耗时后输入积压（2026-10-16）

09:23会话仍出现 `expired input base`：09:26首个记录为ack30/sent94，随后确认序号推进但长期落后约146帧。额外保留最后确认帧不能保护已被淘汰的中间帧。只读状态归档为 `research/evidence/acr-connection-lag-20261016.txt`。

收包循环原先每读一个UDP包都先调用模拟tick。路径计算超过50ms时，积压输入只能穿插在后续tick之间消费。当前核弹小镇离线12步中，常规步约10–12ms，重新寻路的一步1045ms；它确实能触发该条件。现在先排空已就绪的UDP包，再执行下一次模拟，不增大输入缓存、不更换差分基准。

回归使用真实加密UDP和原生usercmd writer，在受控的慢tick期间排入三条操作。旧代码首批只处理 `[1150]`，修改后首批处理 `[1150,1200,1250]`，后续位置、扣弹和伤害断言仍通过；当时 `test_match_server` 3项通过。10:28已随默认部件修复重载，实机效果待观察，不能据此声称所有延迟或枪手错位已经消失。

### 退出后再匹配提示服务器繁忙（2026-10-16）

10:18用户重试时，大厅仍运行，但对局线程已因 `recvfrom` 的 `ConnectionResetError: WinError 10054` 退出；同一日志的服务器查询21/5返回0个候选。Windows会把发往已关闭客户端UDP端口的ICMP错误交给下一次接收，不能据大厅端口仍在监听判断对局可用。

接收循环现仅处理这个连接重置：清除旧association、输入队列和tick时钟，重建连接状态，保留本地UDP端点供重新握手；其他未处理的系统错误仍上报。Windows回归实际关闭已握手的回环客户端并触发ICMP，旧代码使线程退出；修复后第二个端口重新完成加密握手及getchallenge。证据保存在 `research/evidence/match-udp-reset-20261016.txt`。

### 客户端帧时钟与稀疏输入（2026-10-16）

用户人工按住W和开火后，两次非暂停CDB读取相隔约47秒，本地帧时钟 `0x078b0a58` 只从180301增至180347，usercmd序号41→87，发送序号4→5。限频dvar969仍为30；正常倍率dvar1866/1867均为1、固定步长1868为0、帧率1848为85。异常来自慢动作全局 `0x02e8a974`：值为 `0x01d2447c`（极小浮点数），不是正常1.0。只读证据为 `research/evidence/match-input-clock-20261016-a.txt`、`-b.txt` 和 `match-clock-scales-20261016.txt`。

当前EXE `0x579f30` 无条件读取配置串6415（0x190f），按 `%i %i %g %g` 解析时间戳、持续毫秒、起始倍率和结束倍率，未检查sscanf返回值。独立服未发布该串，空值使栈残留进入 `0x59d2f0`；`0x59d500` 将极小倍率后的时长钳到1ms，`0x59d902..0x59d940` 同时把帧率限制到1。`0x460210` 的33ms发送门槛因此约33秒才满足。参考 `sh1x_dedicated/src/codol/script/codol_script_slowmotion.c` 仅用于核对四字段含义；新版编号由当前客户端指令和已有版本映射确认。

最小修复：`Connection` 初始gamestate明确发送6415=`0 0 1 1`，保持正常时间，不改EXE、启动参数或发送限频。新增回归执行实际gamestate读取、配置查找、慢动作消费和帧时长换算，仅隔离依赖Windows TLS的CRT sscanf；缺值时16/50/1000ms均错误变1ms，修复后两张受支持地图都保留原时长。连接及加密UDP相关19项一次集中回归通过。REA新xref请求本轮超时，未重复扫描；新增调用链使用当前EXE限定地址反汇编，已保存 `research/evidence/client-frame-clock423.asm`，不冒充REA新反编译结果。

服务重载后须完全退出并重启客户端，清除旧会话的异常倍率。人工检查WASD/视角响应、手枪模、射击耗弹及AI伤害；原生回归不等于游戏实测通过。最新用户要求恢复人工验收，代理不再自动操作菜单或移动射击。

### 出生缩放、计数和选枪（2026-10-16）

实机原始快照有武器5和视角高度60，但CG预测后两者变0，`pm_flags=2`。当前 `0x4124d0` 从 `PS+0x98` 计算 `scale*60`，`0x419bdd` 覆盖目标高度；缩放缺省0还会在 `0x415cd0/0x419d11` 被判作蹲姿。`0x412560` 使用同一缩放生成碰撞盒。修复为发出field217=1.0，而不是反复强写视角或虚构额外碰撞字段。原生高度/碰撞函数回归修复前返回0，修复后为60及center `(0,0,35)`、halfsize `(15,15,35)`。

玩家生命期同时补齐：stats mask bit3发送单字节出生计数，原生 `0x5a4967` 写入 `PS+0x19c`；新旧计数变化经 `0x525a3c → 0x525c1f → 0x44ee10` 触发出生选枪。field85发送固定出生时间到 `PS+0x3350`，供 `0x425124` 的200ms初生切枪保护使用。两项仅在真实出生/重生时变化，计数按8位回绕，不能每帧刷新保护时间。原生快照回归覆盖首生、存活、死亡等待、连续重生及255回绕；世界、快照和UDP共20项通过。完整客户端是否恢复枪模和输入仍须本轮重启验证。

03:58完整客户端只读CDB确认：预测后的scale=1、视角高度60、PS武器=5、CG选择武器=5、最新usercmd武器=5，出生计数已随AI击杀后的重生变为2。证明出生选枪链已恢复，但画面仍不见枪，半秒自动前进/点击未观察到服务端位移或耗弹，不作为可玩性通过。

库存的五个字节不是五个“拥有”开关。旧源码 `codol_weapon_give.c::grant` 将Old/Rechamber清零；当前 `0x423c87..0x423c98` 读取并设置used-before，`0x423db7` 据此选择首次或普通举枪。发布mask从31改为新授予0；收到选择ACR的有效usercmd后保留bit0=1，双持、fast-mag及两手rechamber保持0，重生重新清零。新增原生解码生命周期测试先失败后通过，相关世界/快照18项通过。

04:03按键期间只读CDB看见原生usercmd `buttons=0x02000001`、weapon=5，开火已进入客户端。原实现直接丢弃超过世界时间200ms的整条输入；参考 `_g_active_mp.asm::ClientThink_real` 与 `codol_pmove_c1.c` 则将模拟时间限到世界时间+200ms。独立服跟随该上限，并单独记录原始输入时间防重放；超过20000ms仍按参考网络层拒绝。新增用例覆盖超前输入的移动/耗弹、重复原始时间无副作用、后续新输入继续执行，世界/UDP共14项通过。状态日志补充最近输入与接收时世界时间、玩家已执行时间，方便实机区分传输、时钟拒收和碰撞。

自动操作脚本的W改用扫描码0x11且不带扩展键标记，按住和开火各2秒并在finally中释放；旧UI库的通用PressKey使用扫描码0且标记扩展键。此工具差异与服务器输入修复分开判断，脚本返回成功不等于实际位移成功。

04:20原生 `0x55c9fc → 0x55bf90` 的一次硬件断点捕获EBX=1，即画枪开关开启。此前非暂停读取确认weapon5模型、手模型及DObj存在，两个模型 `+0x15d` 分别为0x0d/0x08（均已就绪），DObj scale=1。故不能继续靠猜PS enable位修复无枪。尚未确认 `0x55c4c6 → 0x4f5990` 完成场景登记。断点脱离后客户端上报ClientException并退出，原因未定位；停止重复侵入式调试，保留 `-pv` 读取。证据归档 `research/evidence/viewweapon-draw-gate-20261016.txt`。

同轮输入日志表明最近有效move常隔20–30秒才更新，多数包实际为已认证的两字节`<3`；时间上限修复未消除此发送稀疏问题。需要继续对照 `0x4602a0` 调用者的发送门槛，不能把服务器能解码单包或AI能击杀重生当作真人输入已打通。

已静态收窄到 `0x52d739 → 0x4607c0 → 0x460210 → 0x4602a0`。当前CA_ACTIVE确为10；`0x460270`比较本地累计时间 `0x078b0a58` 与上次发送ring槽 `+8`，阈值 `1000/dvar969`（默认30，范围15–100）。ring由 `cl+0x867c XOR 0x96b9dc91`取得，槽为`(conn+0x80158-1)&cl[0x8668]`。不得用conn+8或ring+4的usercmd时间代替这个门槛。`Read-MatchDebug.ps1 -Connection`已补三者只读输出，尚待新一轮实际读取；没有证据支持补serverinfo字段或改人数规则。

一次实际核弹小镇资源的30步短采样还定位到长距离路径的宽矩形粗筛：沿对角线前进时，大量离线段很远的三角形仍进入SAT。增加保守的线段/扩张包围盒筛选，精确几何、接触顺序与碰撞结果保持原路径。最小回归从41次三角形展开降为1次，并覆盖静止重叠、切向接触；碰撞、导航及世界32项通过。同样启用cProfile的30步由32.595秒降至7.701秒，SAT次数487627降至34299。这是受采样开销影响的离线对比，不能作为实际20Hz稳定性的证明。

2026-10-16 03:26，完整客户端已在核弹小镇中持续收帧。只读CDB读取发送队列（连接对象 `+0x140/+0x144` 为可靠序号/确认，`+0x148+1024*(序号&255)` 为文本）发现44条未确认指令，首尾均为 `s`。参考源码 `g_cmds.c::ClientCommand` 将它识别为比分查询；原独立服只接受userinfo，因而连同包中的move一起拒收。现在准确接受无参数 `s` 并维护可靠确认与响应XOR，不放宽序号缺口、未知命令或userinfo身份校验。比分内容尚未实现，此修改只解除输入传输阻塞。

新增回归通过原生usercmd封包器构造 `s → userinfo → s → move` 同包，验证移动/射击字段、响应确认和重复包；异常序号及带参数的未知命令仍拒绝。连接与输入18项通过。当前客户端原始快照的武器5、视角高度60正确，但预测后的玩家状态把二者改为0；这仍阻塞武器显示及操作，不把可靠指令修复当成可玩性验收。

03:36重启实测，比分查询已收到确认；点击开火产生下一种可靠文本 `n 1 / n 2`。当前 `0x46a8c0` 在active状态将动作编号格式化为 `n %i`，新版指针表 `0xce1cc0` 含1..98项（1/2为开火按下/松开，31/32为前进按下/松开），不能照搬旧服85项的上界。连接现在接收该范围的通知，继续由同包usercmd模拟移动与射击，不重复执行动作。定向回归在原同包链加入动作与98边界，0、99、负数、额外参数均拒绝；先失败后通过。此处未恢复GSC事件订阅或完整比分板。

`input.py` 直接反解3.3.3.3的3位消息类型、键控usercmd和末尾标签，支持一包多条可靠命令。首条输入的省略字段来自**已确认的快照**；不能拿服务器最新位置、视角或武器作解码基准。畸形批次不更新连接状态，重发批次不重复处理。

`snapshot.py` 直接编码当前玩家字段、生命值、单武器弹药、两名玩家的entity/client记录；没有旧引擎布局中转。`data/match-fields423.json` 保存当前EXE的实体字段、客户端字段与事件参数宽度。连接中加入可靠服务端命令及其确认记录，后续可发送武器选择和对局状态。

坐标中心不是必须猜出的地图常量：REA `client-gamestate-instructions423.json` 的 `0x46e0e1..0x46e0ec` 读取配置串16并按 `%f %f %f` 写入 `0x78b0a78/7c/80`。新服可选覆盖本图坐标的中心，配置串和实体编码必须使用同一值。`test_map_center_is_server_supplied_configstring_16` 执行实际gamestate读取器，只替换CRT的sscanf，并再用实际实体读取器验证非零中心的位置。

定向测试共39项通过：

```powershell
$env:PYTHONPATH='src;tests;tools'
python -m unittest test_match_transport test_match_connection test_match_server test_match_input test_match_snapshot test_story_wire423 -q
```

验证边界仍是协议消费：真实客户端writer `0x5a1be0`、默认输入 `0x5a18e0`、snapshot reader `0x46d170`；没有执行完整渲染或开图。后续资源、模拟和大厅接线状态见下文，不能用这些读取器结果替代游戏验收。

## 独立模拟与大厅接入

`world.py` 已持有两名玩家的位置、速度、生命值、弹药、射击/换弹计时和重生状态。真人输入和AI共用移动及射击入口；射线先受地图遮挡，再按命中距离扣血，AI没有直接改对手生命值的捷径。当前只实现站立移动、跳跃、跨低台阶和单支步枪，其他姿态、技能、穿透及骨骼伤害后置。

- `navigation.py` 复用参考CSV路点与A*；CSV连线必须再经当前地图盒体扫掠验证，隐藏目标需要绕过掩体才能被射击。
- `loadout.py` 从当前423武器头直接读取参数；`export_match_loadout.py` 通过本版本NCS前缀还原名称，提取 `acr_mp`，不按旧资源编号或资产序号猜测。ACR为36发、90ms射击间隔、2000/2500ms普通/空仓换弹。最小对局初始给予一个弹匣及三个备用弹匣。
- `server.py` 在加载阶段6后先发送初始玩家快照，在有效gamestate确认后的首个move上进入模拟，随后按20Hz发送状态。回环测试使用真实加密UDP和当前客户端writer/reader，确认输入改变新服位置、弹药和对手生命值，而不仅是收到回复。
- `matchmaking.py` 复用现有查询编码和事件21预订消息，绑定一个账号、Killhouse和dm；只发布已启动的独立UDP实例。`local_server.py` 使用 `runtime.load_matchmaking`，运行时不读取参考源码目录或启动旧引擎。

当前机器码 `0x4232d0/0x4253e0` 的死亡门槛为 `pm_type >= 8`，7是倒地状态；`0x4131a0` 同时填写实体 `0xd0/0xd2` 的当前武器。事件序号按8位回绕。上述边界已加入测试，不能沿用其他版本的枚举与布局。

```powershell
$env:PYTHONPATH='src;tests;tools'
python -m unittest test_match_world test_match_navigation test_match_loadout test_independent_matchmaking test_match_server -q
```

这些测试尚未运行完整客户端渲染、实际开图和玩家操作。v5地图包确认17个DM出生点可落地；静态碰撞包括14931个brush、11610个地形三角形、1627个模型实例及78个初始世界子模型。采用空间粗筛和几何缓存后，一次真实地图20步记录中常规步为9–11ms，首次路径计算5.765s；现已把初始AI路径预热移到发布前。新路线缓存仍可能产生延迟，实际手感由用户检查，不宣称完整物理一致。

碰撞就绪只指DM初始静态世界：保留156个原始type6基线实体，不重排其资源编号；玻璃破坏、动态物体、训练/其他模式的子模型不在本轮可玩承诺中。

## 首次开图预加载与注册表

正常Room连接入口 `0x46a750` 在 `0x46a8a5` 调用 `0x46a450`，再经 `0x49fe30` 提交地图加载；这是握手前已有的预加载。stats完成的 `statResponse 0 → 0x466660` 检查DB就绪，未就绪进入state6，经 `heartbeatresponse` 再检查后进入state7。新服补齐heartbeat响应及 `gamestateupdate 0..6`，不额外发送 `loadingnewmap`。后者有先检查旧DB状态再提交加载的时序，不能作为正常首连的必要步骤。

首次gamestate仍在解析配置串前比较NCS CRC，不绕过比较。此前将 `0x448070` 的UI预览初始化误称为 `CG_Init`，现纠正；不能据此强行切换两套CRC。

`build_match_registration.py` 校验当前客户端和签名FF，按实际加载器选择重建54张地图NCS表。商城lite表在卸载UI后仍保留，原52表候选391859916不再用于启动；最终地图候选CRC为 **3852334052**，大厅候选为962763178，seed为3451066449。`probe_match_registration.py` 执行当前机器码核对算法，**所选集合仍是加载器推导，尚非实机挂载捕获**。清单保留 `mounted_set_verified=false`，最终是否一致由客户端正常CRC比较反馈。

对应角色/手部/ACR编号为109/53/5。`export_match_loadout.py` 将注册表、武器头、路点与地图文件放入独立包；不借用旧编号或旧安装目录。生成命令：

```powershell
$env:PYTHONPATH='src;tests;tools'
python tools/build_match_registration.py
python tools/export_match_loadout.py --source research/experiments/independent-match/killhouse-dm-v5 --output research/experiments/independent-match/killhouse-loadout-v2 --common-zone research/experiments/story-native/zone-assets/common_mp/zone.bin --waypoints research/experiments/story-native/source-startup-xygdjp3z/main/waypoints/mp_killhouse_sh_wp.csv --registration research/experiments/independent-match/registration/rebuilt
```

导出要求新目录，已有包不会覆盖。将完整导出目录部署到 `runtime/match/killhouse/`；生成物、游戏资源和玩家档案均不提交。重建依赖本机已提取输入，运行只依赖独立包。

## 历史部署记录（Killhouse）

此前 `data/match-playlist.info` 通过 **10/21 → mp_playlists_shipRetail_release.info** 仅发布 `Killhouse DM`。用户截图显示分类存在但子赛单为空、匹配按钮缺失，不能视为可用入口。随后已按用户要求恢复完整菜单，实施与步骤见 [05](05-publisher-character-selection.md#赛单恢复与界面复审2026-10-15)。以下保留当时的Killhouse计划和部署证据；当前人工入口见下一节。

1. 界面复审通过后再接回明确的Killhouse/dm测试入口。
2. 一名真人开始匹配，检查是否加载Killhouse并出生；不使用剧情或其他模式代替。
3. 使用WASD、空格、鼠标及R验证移动、跳跃、射击和换弹；当前固定ACR，不验证完整仓库装备。
4. 找到一个AI，检查双方可见、互射扣血、死亡后约3秒重生。

`runtime/logs/server.jsonl` 记录 `independent_match_ready`、查询/预订、`match_phase`、`match_state` 和 `match_rejected`；生命值变化及约5秒一次的位置/弹药用于关联人工反馈。当前每次服务启动只维护一场预订；退出对局后重新测试请重启项目服务。不能把资源初始化完成或监听成功写成游戏内验收通过。

2026-10-15 19:09（Asia/Shanghai）已重启本项目服务，PID62484：从34文件独立包完成地图/武器/导航初始化，CRC3852334052；认证443、大厅TCP3074、STUN UDP3074已监听。一次实际加密大厅启动检查读取原有公开档案、取到精确播放列表并查询到UDP28970，未上传档案，也未消耗游戏端握手连接；无旧 `server3333.exe` 进程。新增资源编号导出测试、资源包接线测试和发布入口测试均先失败后通过；已通过的旧检查不重复执行，真实游戏留给用户。

本轮本地阶段提交：`6332840` 地图与碰撞导出，`ee9496a` 玩家/AI模拟，`502a880` 大厅接入。

**完成条件**：原版3.3.3.3客户端的上述操作由独立服维护，关掉/移走旧服安装后仍能完成同一验收。旧服协议探针通过与独立服通过分开记录。

## 核弹小镇人工验收

旧路点直接连线曾返回空路径。当前地图存在低台阶及轻微地面高度差：运行时在原路点上下18单位内用真实玩家盒体寻找支撑面，墙内或无支撑点排除；可达检查采用与移动相同的18单位跨步高度，仍检查顶棚。重新规划可跳过已可见的后继点，避免先折返到最近旧点。三个新增失败用例修复后，与相关移动/导航共12项通过。

本图离线记录 `research/evidence/nuketown-navigation-smoke.json`：初始23节点路径，100步内AI从 `[2071.4,165.7,-64]` 推进到 `[1672.687,372.918,-64]`。这证明实际地图碰撞与路径跟随开始工作，不代表已完成全图巡航或游戏内互射验收。

1. 完全退出旧游戏，在控制器重新启动，让客户端读取赛单版本802。
2. 进入 **玩 → 多人竞技(PVP) → 冲锋团队竞技 → 核弹小镇 → 开始匹配**。复用原赛单110，右侧说明应为一名真人、一个AI、ACR、自由混战，不再出现“本地人机测试”分类。
3. 检查实际进入地图并看见武器，而非停留在加载画面；WASD、鼠标、空格、R分别检查移动、瞄准射击、跳跃、换弹。
4. 检查一个AI是否可见，双方射击是否扣血，死亡后约3秒重生。固定ACR，不以仓库其他武器或配件作为本轮验收对象。

资源包为 `runtime/match/nuketown/`，服务日志应显示 `independent_match_ready` 的 `map=mp_nuked`、`checksum=1765105316`。连接阶段查看 `match_nat_reply`、`match_phase`、`match_start`、`match_state`；失败时报告画面文字及点击时间，结合 `match_rejected.header` 定位。初始预热约31秒；每次服务启动仅维护一场预订，退出对局后重新测试需重启项目服务。

2026-10-15 22:31:36（Asia/Shanghai）项目服务已重载，PID46688；日志确认上述地图/CRC和认证443、大厅TCP3074、STUN UDP3074启动。未启动完整游戏或占用真人对局预订，留给用户验收。

本轮阶段提交：`247a370` 入口/地图身份/NAT，`9ba1170` 核弹小镇资源导出与特效边界。游戏资源、生成包、证据及本地运行数据保持Git排除；原游戏与正式存档未修改。
