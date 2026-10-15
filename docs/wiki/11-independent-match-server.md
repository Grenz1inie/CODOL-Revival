# 11 独立模拟对局服务器

## 决定与范围

2026-10-15，用户明确停止以旧服务器持续打补丁的路线，改做面向 **3.3.3.3** 的独立模拟对局服。此前“优先复用旧版代码”的要求继续适用于选择性源码移植；不依赖旧服进程或旧安装目录。原游戏 EXE、正式存档和现有认证/商城功能保持原状。

用户随后确认首版改为 **核弹小镇 `mp_nuked`、一名真人、一个服务端AI、一把ACR、自由混战 `dm`**，完成出生、移动、互射、伤害、死亡及重生。Killhouse保留为此前的资源/协议基线；剧情脚本、连杀奖励、全面装备与公网多人不属于这个阶段。

“模拟”指由新服接收输入、维护权威状态并产生当前客户端可消费的快照。预录快照、固定坐标、按请求返回成功或客户端自行减血都不能代替对局实现。

## 核弹小镇参考评估（2026-10-15）

用户提出并批准实施“进入核弹小镇，一名真人与一个AI移动、互射、伤害及死亡重生”，复杂地图效果后置，并指定充分参考相邻 `sh1x_dedicated/`。以下评估保留为实现依据；实际进度见下一节。

- 当前菜单的核弹小镇是赛单110、地图 `mp_nuked`、玩法 `cha`（原9V9）。它不是独立服当前实现的 `mp_killhouse_sh/dm`；恢复赛单目录不会自动切换服务端地图。
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

剩余工作按依赖排序：先修实际赛单轮换启动命令与连接握手（本次游戏日志仍有 `DATA before handshake`）；再导出核弹小镇的隔离资源包、去掉当前启动/连接中写死的Killhouse身份；最后接入本图出生点、可达寻路和已有最小战斗循环。地图迁移主要涉及 `tools/export_match_map.py`、`tools/export_match_loadout.py`、`src/match_server/{runtime,connection,matchmaking}.py` 和 `src/local_server.py`。模型/武器编号需随本图注册表重新解析。

建议先保留完整原菜单，增加明确的“核弹小镇·1v1人机测试”入口，使用最小自由混战规则；不把这个入口标成原9V9玩法已恢复。核弹爆炸、环境事件、破坏物、连杀奖励及高级AI动作均可后置；静态碰撞与射击遮挡先保持一致。核弹小镇可作为首个样板，不必将Killhouse实机验收作为额外前置，但共同握手/出生链路仍必须完成。

参考目录已建立局部索引：CodeGraph为1431文件、27510节点；GitNexus别名 `sh1x-dedicated-reference`，44534节点。范围为 `src/` 与 `tests/`，配置是参考目录的 `codegraph.json` 与 `.gitnexusignore`；GSC、寻路CSV及地图包仍直接按路径读取，不伪称已形成GSC调用图。少量旧头文件无法解析、部分跨语言/函数指针调用不完整，缺边不能推成无调用。未编译或运行旧服，未改动其原有源码。

## 当前方案与参考源码

### 核弹小镇接入（2026-10-15）

- 赛单版本800新增“本地人机测试 → 核弹小镇 · 1对1人机”（赛单240），唯一地图行为 `mp_nuked,ffa,1`；客户端已有 `ffa → dm` 映射。完整原目录保留，原赛单110的9V9没有被改成1V1。
- `runtime → matchmaking → MatchServer → Connection` 传递包内地图身份，连接响应、serverinfo及gamestate使用同一地图名；当前客户端机器码读取器已消费Nuketown的状态。
- REA已保存的 `client-coop-mmstart423.json` 中 `0x6e6bf0` 证明PVP有 `playlist …; start_map_rotate_once …` 分支，不能只识别 `map`。新服接受固定赛单240或明确的 `map mp_nuked` / `g_gametype dm`；不执行客户端任意控制台文本，拒绝其他赛单/地图/玩法。
- 参考源码 `src/codol/net/codol_network.c:359–371` 的明文bdNAT INTRO发生在加密INIT前：29字节 `0d 02 00` 请求原样回显，仅类型改成 `0c`。已补入独立UDP入口，保留客户端MAC与地址，不提前占用预订。定向测试先复现超时，再验证回应和后续INIT_ACK。
- 此前实机日志只记录29字节及 `DATA before handshake`，没有包头，不能仅凭长度认定所有失败包都是INTRO。新日志记录前6字节，供下一次人工测试区分NAT与真正的加密DATA；游戏出生仍未实测。
- REA恢复现有快照成功；新字符串查询在300秒超时，本轮使用已有REA命令链证据与参考源码，没有把缓存恢复表述为新完成的全量分析。

资源提取与地图准备仍在本项目的隔离目录内进行，原游戏与正式档案不写入。只有资源包完成当前最小物理范围后才切换运行实例。

独立服源码位于 `src/match_server/`，已接入现有认证/大厅，资源独立保存在 `runtime/match/killhouse/`。`local_server.py` 已替换 `NativeServer`，启动时读取地图、碰撞、武器与寻路数据；查询时为当前账号建立回环UDP实例。**自动验证覆盖协议消费和服务端模拟；完整客户端开图、画面、操作及对战仍待用户验收。**

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
4. **用户集中验收**：完整游戏加载Killhouse、双方可见、真人与AI互射、伤害及重生。此前只报告自动验证阶段，不提前通知“已可玩”。

新源码放在 `src/match_server/`，协议测试及真实客户端消费探针放在现有 `tests/`、`tools/`；资源与运行产物继续分别放在 `research/`、`runtime/`。接线时才替换 `local_server.py` 中旧后端，并同步服务启停与控制器状态。

## 独立连接阶段（2026-10-15）

- `crypto.py`、`transport.py`：Python Tiger192、P-224 握手、AES-192 CTR、DATA 的 HMAC、序号和重复包处理；不装载旧 EXE 或链接旧引擎。
- `connection.py`：单一预订账号校验、challenge/connect、stats 分片与 CRC、可靠 userinfo 确认、当前版本 gamestate；不写正式玩家档案。
- `server.py`：只绑定 `127.0.0.1` 的独立 UDP 收发。`tests/test_match_server.py` 经真实 socket 和加密层，把地图状态交给当前客户端读取器；确认解析出 `mp_killhouse_sh / dm`。
- stats 的 uint16 是**压缩后总长度**，不是本分片长度；每片最多1238字节，未压缩长度32768，末尾校验CRC。只有全部合法数据齐备才允许地图状态发送。

测试分别使用客户端 `0xa87020/0xa87060/0xa87110`（Tiger）、`0x6d81a0`（stats writer）、`0x5a5960/0x46bf80`（netchan/XOR）和 `0x46dea0`（gamestate）。最后一项在 `0x4651b0` 加载入口停止，**未执行渲染、资源加载或出生**；测试中的 NCS CRC 是协议夹具，不是已经核实的 Killhouse 实际注册表。

REA 已恢复原快照；本轮重复反编译请求300秒超时，未取得新结果。继续使用绑定相同客户端哈希的 `client-tiger423.json`、`client-stats-writer423.json`、`client-connectionless-current423.json` 及机器码验证，不把快照恢复称为新分析完成。

定向验证：

```powershell
$env:PYTHONPATH='src;tests;tools'
python -m unittest test_match_transport test_match_connection test_match_server test_story_wire423 -q
```

## 输入与玩家快照（2026-10-15）

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
- `server.py` 在有效gamestate确认后的首个move上进入模拟，随后按20Hz发送状态。回环测试使用真实加密UDP和当前客户端writer/reader，确认输入改变新服位置、弹药和对手生命值，而不仅是收到回复。
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

## 部署记录与后续对局验收

此前 `data/match-playlist.info` 通过 **10/21 → mp_playlists_shipRetail_release.info** 仅发布 `Killhouse DM`。用户截图显示分类存在但子赛单为空、匹配按钮缺失，不能视为可用入口。现按用户要求先恢复完整菜单供人工复审，实施与步骤见 [05](05-publisher-character-selection.md#赛单恢复与界面复审2026-10-15)。本节后续对局验收暂后置；独立World仍只支持Killhouse/dm，不因菜单恢复而声称其他模式可玩。

1. 界面复审通过后再接回明确的Killhouse/dm测试入口。
2. 一名真人开始匹配，检查是否加载Killhouse并出生；不使用剧情或其他模式代替。
3. 使用WASD、空格、鼠标及R验证移动、跳跃、射击和换弹；当前固定ACR，不验证完整仓库装备。
4. 找到一个AI，检查双方可见、互射扣血、死亡后约3秒重生。

`runtime/logs/server.jsonl` 记录 `independent_match_ready`、查询/预订、`match_phase`、`match_state` 和 `match_rejected`；生命值变化及约5秒一次的位置/弹药用于关联人工反馈。当前每次服务启动只维护一场预订；退出对局后重新测试请重启项目服务。不能把资源初始化完成或监听成功写成游戏内验收通过。

2026-10-15 19:09（Asia/Shanghai）已重启本项目服务，PID62484：从34文件独立包完成地图/武器/导航初始化，CRC3852334052；认证443、大厅TCP3074、STUN UDP3074已监听。一次实际加密大厅启动检查读取原有公开档案、取到精确播放列表并查询到UDP28970，未上传档案，也未消耗游戏端握手连接；无旧 `server3333.exe` 进程。新增资源编号导出测试、资源包接线测试和发布入口测试均先失败后通过；已通过的旧检查不重复执行，真实游戏留给用户。

本轮本地阶段提交：`6332840` 地图与碰撞导出，`ee9496a` 玩家/AI模拟，`502a880` 大厅接入。

**完成条件**：原版3.3.3.3客户端的上述操作由独立服维护，关掉/移走旧服安装后仍能完成同一验收。旧服协议探针通过与独立服通过分开记录。
