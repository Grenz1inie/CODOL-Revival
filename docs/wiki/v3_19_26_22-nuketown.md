# 3.19 核弹小镇 9V9

目标：保留原菜单的赛单110；进入等待厅即有一名真人和17个人机，双方各9人。
房间名单、队伍与实际对局共享身份；Rust对局服放在本版本的
`server/native/match-server/`。本轮不修改3.3的DM实现。

## 当前状态

- Rust房间规则与名单：5项定向测试先失败后通过；人数、分队、唯一身份、重入稳定性、错误身份已覆盖。
- Rust名单编码：3项新增测试先失败后通过，含当前客户端原生写入/读取函数的Unicorn重放；18人1232字节，保留真人准备状态及未解释字段。尚未发布给运行中的客户端。
- Rust入房消息：17条消息通过原生写入/读取重放；真人房主已实际接纳17个人机，客户端内存确认双方各9人。
- 人数规则：已修正赛单110的发布名称并通过3项定向测试，含原生规则消费者；重启后的真实会话请求与频道上限均为18。
- 等待厅网络接入：真实报文修正后人机出现，频道名Base64修正后用户确认Bot01～Bot17显示正常；原版名字和配装表尚未接入。
- Rust UDP连接、stats重组及服务端封包已有独立实现和定向验证，尚未接入管理器的真实核弹小镇对局。资源挂载、AI互射、队伍计分与实机可玩尚未验证。
- 真人Ready规则：49ea5c7的启动参数与名单准备位修改未通过实机验收，用户仍反馈进房即倒计时；见下方最新证据。
- 用户本次观察：只有一个人时进入房间即自动倒计时；不要求用户停留在一个无法保持的“Ready前”状态。
- 用户回忆自己未准备也会倒计时，猜测可能是半数人数门槛；此为待验证假设，没有将门槛写为9或要求18人全部准备。

## 名单消息与频道成员

以下地址均绑定下述目标哈希，来自本版本REA静态分析与Unicorn重放。
`0x627d80 -> 0x623880`写入消息14：一位无类型标签标记、8位消息类型、
32位人数，以及每人545位字段；`0x627e00 -> 0x623de0`读取同一格式。
原生成员结构步长`0x1d0`，UID在`+0`、队伍在`+0x88`、准备状态在`+0x90`。
Rust对真人保留输入结构中的其他网络字段，人机使用`0x623770`构造器默认值。
完整18人原生样本与来源见Rust测试的`fixtures/README.md`。

名字不在该名单消息内。`0x6304b0 / 0x630520`从聊天频道成员数组取得UID和姓名；
频道成员变化处理在`0x7e7a50`。`0x634870`处理消息14时要求当前房间是非房主，
且发送者是频道房主。当前只读实例是本地房主，因此不能仅推送名单14就宣称人机可见。
加入远端房间的`0x62dee0`清除本地房主标记，随后`0x7e7ee0`发起频道订阅。
当前创建频道走`0x7e7e30 -> 0xb8e7b0`，对应服务11/任务13。

来源：`work/codol319-nuketown/room-members-rea.evidence.json`、
`room-wire-rea.evidence.json`、`room-network-rea.evidence.json`；
名单原生重放见`tests/client_room319.py`。覆盖已确认消息格式、成员来源及房主检查；
搜索结果、频道初始成员、名单推送顺序和实际UI仍待接通验证。未将频道人数视作真实对局AI。

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

## 当前房间的开局与人数限制

本节复用已保存的REA结论，并以新的限定只读数据和Unicorn重放交叉检查。
目标仍为上述3.19 EXE哈希，不适用于3.3。IDA Pro 9.4首次接入后对
`0x632a70`的新反编译与REA结论一致，存于`ida-ready-632a70.json`；
不能将此次IDA分析称为REA/IDA缓存命中。

| 地址 / 结论 | 来源、覆盖 | 未验证项 |
| --- | --- | --- |
| `0x632a70`普通房间准备判断：满足最低人数后，有人准备可启动计时；全员准备可直接开局；计时到期也可开局 | REA `ev_e473ade0305b9f32d8c46d3e0dbeea4ab52e4f43c2596b3583e186ba7ce58881`与IDA交叉核对；`+0x90`是成员准备标志，排除team6后检查最低人数 | 未恢复停服前服务端的人机策略，不推断必须18人全部准备 |
| `0x63c5e0`另有自动开局分支，要求房间`+0x10614 != 0` | 同一REA证据；`room-context-81072.json`当前值为1，`0x8269818`指向名称3291的启用项；与用户进房即倒计时观察相符 | 未证明后续地图启动或实际开局完成 |
| `0x62ca80`创建房间调用`0x761c30`，按人数dvar实际名称筛选并执行赛单规则，再复制至房间`+0x105fd/+0x105fe` | 已存`room-network-rea.evidence.json`创建路径；新REA `ev_27606f3954748d20e38a3973713525c1b386561c0a8e08ee4b696603528697da`确认规则消费者；`room-policy-81072.json`确认`0x1c2b0c0`名称1011、`0x1c2b064`名称3265，最大人数当前值为0 | 重启后的房间上限及UI需要实际验收 |
| 原发布文件使用`party_minplayers/party_maxplayers`，`0x761c30`无法按1011/3265找到它们 | Unicorn执行原生扫描/匹配/复制；原名称产生0条执行命令，转换后分别得到`1011 1`、`3265 18`；仅模拟选定赛单和最终命令执行边界 | 未把“找到命令”当作实时客户端已更新 |
| 入房消息6：`0x6270d0 -> 0x627230`，722位；`0x634870`校验内容版本后由`0x634340 -> 0x62a100`加入成员 | 新REA、原生写入/读取重放；版本值797经`0x7b25a38`限定只读核实；合成样本见Rust fixtures说明 | 频道成员登记、完整接纳状态机、等待厅显示和AI实机行为 |
| 频道成员事件9/10走`0xb7b4b0`；频道消息7/8走`0xb7b300 -> 0x7f1060 -> 0x7e7c90`；外层消息kind2由`0xb838a0`分发 | 新REA `room-results-rea.evidence.json`、`room-policy-rea.evidence.json`；确认分发与读取字段顺序 | 服务端推送、原生完整消费与实际UI仍待验证 |

修正仅在发布`mp_playlists_shipRetail_release.info`时转换赛单110的两个人数
规则名称；保持原GB18030字节、9V9说明、地图/玩法、分数和时间规则以及其他赛单。
人机入房保持未准备，真人点击Ready后开始倒计时；这是用户确认的本地规则，
不以该选择声称恢复原服门槛，也不改写真人准备状态。

## 本地房主接纳链路

`Room`仅对真实抓包中21/5查询的内容版本797、赛单110启用。11/13返回
频道资料，等待客户端首次11/4发送后，才发布17个频道成员事件9，避免
创建频道的异步回调尚未执行。随后以第一名人机身份发送原生消息13，
取得房主的消息14；Rust从中提取真人实际队伍和兼容字段，生成17条消息6。
本地房主仍通过原生接纳函数决定是否加入。最后再次查询名单，日志记录
客户端回报人数；该人数不是AI已出生或可玩的证明。

| 地址 / 结论 | 来源、覆盖 | 未验证项 |
| --- | --- | --- |
| `0x62af10`初始化真人队伍：部分玩法固定2，其他分支可随机1/2 | 新REA `room-policy-rea.evidence.json`，绑定本页EXE与切片哈希；Rust新增测试分别覆盖真人队伍1/2并保持9/9 | 实际新房间的最终队伍、进入地图后的队伍映射 |
| `0x634870`消息13分支由房主向请求者返回14；消息6随后走`0x634340 -> 0x62a100` | 复用已保存REA `room-results-rea.evidence.json`；频道登记与房间入队分开 | 完整实机接纳及等待厅显示 |
| `0xb7b4b0`与`0xb7b300`读取服务端事件9/7 | 新Unicorn重放原函数；核对频道ID、房主、成员UID/名字及原始房间消息；仅上层回调被替代以观察结果 | 回调之后的实际房间状态及UI |
| `0x629e40 -> 0x629cd0 -> 0x7f4630`多人房间广告/会话创建 | 新REA `ev_6085ff04cd53d5e8e54ee8c9a6dbdc174db78933d8b05daa44b59d38bc06f6bb`；最大人数从0改为18后会涉及该路径；`0xb9ae30`发送21/1 | 会话结果和后续对局接入仍需真实客户端核对 |

当前名字`Bot01`至`Bot17`为联调占位，不代表原版名单。用户提供线索：
他人的恢复成果中出现停服前名字和配装。REA新字符串证据
`ev_1e61f41bbcfa24774d6cb0734dfba831bb47be710bf28427b5bf3d73589de144`
在本版本`0xde70fc`发现`mp/botClassTable.csv`，`0xdc2104`发现`botsAddAll`。
当前房间分析切片不含这些字符串的调用代码，空xref不代表原程序未使用；
后续实际消费者与表内容已找到，见下节；当前联调占位名字尚未替换。

新分析切片`room-policy319.exe` SHA-256：
`371771424451aa18aeddeaa2a4211926716df215543dac0ad471c2ab84ede307`；
扩展的地址范围见`room-policy-image.json`。此前`room-results319.exe` SHA-256：
`97d4f44d56ff86b8f3c09f6e42cde205de9df6941eef3a1e5eb423120708644c`，
其REA证据和快照已保存。所有切片均不可运行，缺页不作为已分析内容。

### 人机配装线索

首次登录阶段的限定只读提取未找到人机表；进入等待厅后再次提取，控制项
`mp/rankTable.csv`与`mp/botClassTable.csv`均存在。后者运行时地址
`0x029c5444`（PID15592，模块基址`0x400000`），共46行22列：首列字段名，
20列`botclass0..19`，最后一列是无uniqueName的默认数据。原始字节、读取
范围、版本与EXE哈希保存在`bot-assets-waitroom-15592.json`，不能对该指针再次重定位。

配装包含主副武器、五类附件、三技能、连杀奖励、致命/战术装备、近战武器、
角色及两方衣装。`botPersonalities`出现default、run_and_gun、camper；
`botDifficulties`包含recruit、regular、hardened、veteran。这证明当前客户端
持有配置，不证明原服分配算法或Rust已经应用。未找到所试的
`mp/botNames.csv`/`mp/botNameTable.csv`；这些只是候选名，不能据此否定本地昵称数据。

REA `ev_e0e3a4b324503dac1a86c8babb7b20d1fd12f4945579608d9fd92270d1f6505b`
确认代码`0x44e487`引用该表并调用`0x76b7a0`，随后调用`0x810360`；
`0x44d2e0`回调消费外观资源。当前切片入口人为设在函数中段，反编译的
`entry`不是原函数真实入口；仅引用该区段已核实的指令和调用，不视为完整函数恢复。
`botsAddAll`经`0x5cf530`读取为配置字段，不能单凭名字视为可执行的人机命令。
切片`bot-resources319.exe` SHA-256：
`a3d4ec1325c3eef121b0ff79b44d8390b53f00c81fdb3da041f066f70d354f0e`。

2026-10-17新REA分析`bot-consumers-rea.evidence.json`确认`0x7c6950`按语言
选择`mp/namesTable.csv`或`mp/namesTableEnglish.csv`，调用`0x7c68a0`分别
填入队伍2/1的本地数组；后者随机选表行的第二列作为名字。
PID17208的限定只读提取`bot-names-17208.json`得到745个中文名字、19个英文
名字；首个中文名字为“AK47宝贝”，原始字节为UTF-8。
表运行时地址分别为`0x029c5754/0x029c5764`，不做二次重定位。
`0x810360`同时证实按配装列、字段名查找并通过资源回调预缓存外观。
覆盖范围为静态消费者和已加载表；尚未证明这些本地数组被当前网络房间采用，
也未将配装应用于Rust对局。分析切片`bot-consumers319.exe` SHA-256：
`d9611673a0eba066c056d92653b628f83ccdde19358e817254c3ac308a37d14b`，
原程序哈希仍为本页顶部3.19 EXE哈希。

## 真实回环流量

`room-baseline.pcapng`：2026-10-16 22:49:35至22:56:36，共104包。
SHA-256：`39090eebdd785bf0511168a24230f1845f00c1f2a69bc878a01d34d38880290c`。
过滤范围为TCP31901和UDP28970。

- 帧65：21/5查找赛单110；帧69：11/13；帧73：28/1；帧77、89、93：11/4房间消息。
- 对应服务器返回空成功；捕获区间没有对局UDP流量。控制器对局状态仍为waiting。
- 捕获开始于现有TCP会话中段。密钥由同一端口20029会话的既有握手十六进制日志重建；抓到的双向完整帧均通过HMAC校验。不能声称本次PCAP包含握手。
- `decode_room_capture.py`按TCP序号重组并核对重传重叠、长度及HMAC；未用日志包长度推断帧结构。
- 分帧与加密包校验已核对；房间状态机和原生重放未完成，协议恢复尚未完成。

首次等待厅验收抓包`room-admission.pcapng` SHA-256：
`f4a0e4504162934caa8e09e4e53e77e6301c4609e7e63bc7ef2d721162d9c10a`。
TCP客户端端口35690；本次包含完整hello、认证和确认，143个加密消息均通过
重组、握手证明与HMAC验证。帧340的11/4实际尾部为类别1及任务结束字节0；
原测试遗漏结束字节，使解析器未发出任何事件9/7。帧356的21/5查询1为房间
内会话刷新，不能按新的赛单选择清空状态。两个行为均已加入失败回归并修复；
7项房间测试通过，包括以真实帧340驱动生产TCP服务。

第二次验收`room-admission-fixed.pcapng` SHA-256：
`11c63fe98da725992cfbbbbdc59a0f8fefa10e0e3d5a99cde3e372aa6acd457c`。
端口21914，完整握手与281个加密消息均校验通过。用户确认出现人机，但名字
乱码且真人未准备即倒计时。`room-live-17208.json`确认当前房间18人、双方各9人，
真人`+0x90=0`、17名人机均为1；`+0x10614=1`，仍处于原生自动开局分支。
这证明名单接纳，不证明地图加载、AI出生或实机可玩；未假设半数准备门槛。

### 频道成员名字修正

缓存REA `0x7e7a50`表明，事件9读到的名字继续经`0x7f3440`解码后才保存。
新REA分析和Unicorn执行该函数确认Base64契约：原回包`Bot01`被转换成
`06 8b 74 d4`，与实机成员数组`+8`完全一致；`Qm90MDE=`才得到`Bot01`。
原测试止于事件回调入口，漏掉了这个实际消费者。现扩展回归，运行原生解码
验证ASCII以及上述真实表的UTF-8中文名字；先复现同一乱码失败，再以Base64
封装频道名字修复。7项房间测试通过，覆盖生产TCP路径。
来源为`room-name-rea.evidence.json`、`room-name-rea.snapshot.json`及上述
PCAP/内存快照；分析镜像为`room-network319.exe`，SHA-256：
`71242c1d50ed26a9e88f2431df3c57646fe1dbbc0e653e9b688ce8e0c20d93c5`。
用户在重新启动后确认名字正常，仍反馈真人未准备就倒计时。

### 真人Ready控制本地开局

2026-10-17用户明确选择：进入等待厅先显示完整9V9，真人点击Ready后才开始
倒计时。原服是否存在半数准备门槛仍未确认，本地规则不据此推断历史行为。

| 地址 / 结论 | 来源、覆盖 | 未验证项 |
| --- | --- | --- |
| `0x62ca80`创建房间时把名称3291的dvar当前值复制到房间`+0x10614`；虚表`+0x64 -> 0x62fe80`读取该标志 | 复用REA创建函数及`room-policy-81072.json`只读快照；新REA精确指令确认`CMP [ECX+0x10614],0`，解编器未把短函数识别为独立过程 | 启动命令在本次实际客户端中是否保持到创建房间，待重启只读核对 |
| `0x632a70`在该标志为0时统计成员`+0x90`；无人准备不倒计时，有人准备且计时未启动则调用虚表`+0x40`；全员准备直接开局 | 复用REA与IDA证据，新Unicorn测试消费Rust名单后运行原生决策函数：全员未准备、真人Ready、重复tick、60秒到期均通过；仅替换时钟、环境查询和外部动作 | 实际等待厅UI、Ready操作及地图加载 |
| `0x62fc00`发布原生消息17；普通房间采用`dw_startGameCountingDown`，自动房间写0 | 新REA；本次保留客户端已有倒计时长度 | 原服准备人数门槛、多人真人联机 |

证据仍绑定本页3.19 EXE哈希；REA镜像`room-results319.exe` SHA-256
`97d4f44d56ff86b8f3c09f6e42cde205de9df6941eef3a1e5eb423120708644c`。
新增结果已保存到`work/codol319-nuketown/room-results-rea.evidence.json`，
缓存命中与本次新分析如上区分。生产修改仅增加启动项`+set 3291 0`并让Rust
加入消息/名单中的人机准备位为0；真人原始字段保持不变。原生消息6、14的历史
ready=1测试样本保留，测试仅转换已核实的准备位，同时重跑原生写入器与读取器。
此阶段完成源码和离线原生测试；随后的实机验收失败，不能据此声称Ready规则生效。

### 2026-10-17实机失败与续接位置

用户反馈“还是一进入就倒计时”。`room-policy-76284.json`只读快照显示18名
成员的ready均为0，房间`+0x10614`仍为1，dvar3291当前值也为1；加载器日志
确实收到`+set 3291 0`。原生普通Ready分支的离线通过没有覆盖实机自动模式。

新REA分析：`0x63c5e0 -> 0x63c550`的自动分支根据人数、分队/组队条件推进；
`0x631a20 -> 0x62bd00/0x62be70`处理组队成员，不以成员ready位控制这个入口。
证据仍绑定上述EXE及`room-results319.exe`哈希，已保存40条REA记录和23项
可恢复查询。覆盖静态调用链和当前只读房间状态；尚未证明具体哪处运行时写入
把3291恢复为1，也未验证实际Ready按钮的完整调用链。

最终停止后的`room-human-ready.pcapng` SHA-256为
`2e91d87487d627009edc8644a3d227c8f9a263ce806158589f0514c1c43f7013`。
2026-10-17恢复后已对停止后的文件重新解码：完整握手和281条加密消息均通过
HMAC，已替换此前279条消息前缀的解码结果。

`work/codol319-nuketown/ready_gate_proposal.py`仅在Unicorn中验证自动入口门控：
两个模块基址下共8项通过，检查未准备、已准备、已倒计时及其他赛单，并检查
栈/寄存器保留。提案见同目录`ready-gate-proposal.md`。未写入任何游戏进程；
保存时仅有离线提案。2026-10-17继续后，用户已明确授权在独立实验副本验证该
门控，范围见`work/codol319-nuketown/ready-gate-proposal.md`最新一节。实验只针对
固定A盘副本，备份档案，不修改原游戏或正式进度；当前尚待实机Ready验收。

### 隔离门控实测与Ready回送修正

2026-10-17，A盘独立实验PID24416确认门控保持，进入房间后18名成员均未准备、
没有自动开局。用户确认双方各9人，但点击Ready没有反应；场景中仅自己的角色。
等待厅成员接纳、同队角色/配装展示、对局AI分别验收，后两项仍未完成。

本次真实抓包`room-ready-gated.pcapng` SHA-256：
`6a4d43b542d22e5522a2c7392a0c0184b8503adb6979a385974486505a24ea69`。
TCP端口5377，最终293条消息均通过HMAC。帧644的11/4包含消息16/true（`20 02`）；
服务器只返回任务成功，未回送频道事件7，因此实机成员ready仍为0。
补齐选定房间内该消息的回送，保留真人UID/名字；准备与取消均支持。

| 地址 / 结论 | 来源、覆盖 | 未验证项 |
| --- | --- | --- |
| `0x7cf850 -> room虚表+0x84 -> 0x6301a0`构造消息16，通过`0x62c5a0`发送 | 新REA `room-ui-rea.evidence.json`；反编译省略的消息常量/栈参数用本版指令交叉核对；真实帧644印证发送 | UI点击至回包的修正后实机效果 |
| `0x634870 case16 -> 0x629090`按发送者UID写成员`+0x90` | 复用`room-results-rea.evidence.json`的case16，新REA读器；Unicorn执行真实分派和解析，Ready/取消仅改真人一位，其他17人不变；环境可用性与后续通知替换 | 等待厅角色渲染、地图开局 |
| `0x6302d0`读取当前用户的成员准备位，供`GetReadyState`返回 | 新REA；解释任务成功但按钮状态不变的原因 | 原服多人准备门槛 |

新分析镜像`room-ui319.exe` SHA-256：
`1cfec4a2e40e8003fea722627d95ec7a67c8ad102a0cec55f7284dd9a0501f0d`，
由同一3.19快照补入UI页面生成，原EXE哈希仍为本页所列值。
本次9项定向测试通过，含真实Ready帧、取消/错误输入、原生状态写入和真实TCP服务。
只给A盘实验源更新`room319.py`后重启；门控仍只存在该实验进程，未移入正式实例。

### Ready人工验收与角色展示续接（2026-10-17）

A盘实验PID58400使用相同门控、`c5fb681`回送。用户确认“点击准备可以开始
倒计时并载入战斗”，随后要求优先接入地图载入。只读观察在
`1792205961.385904`记录18人ready均为0，在`1792206001.2373524`记录仅真人
ready变为1，门控保持。此处“载入”指客户端进入加载流程，不代表对局服或地图
已经就绪；当时监督进程match仍为waiting，没有对局UDP。

`room-ready-echo-live.pcapng`从TCP26811会话中段开始，握手未抓全；使用本次
同端口握手十六进制日志重建密钥。已捕获消息的HMAC全部通过，帧421为Ready，
帧427为消息23，帧439为消息4，帧443为消息17。停止后重解码的321条TCP消息
全部通过HMAC；最终SHA-256为
`a88de051c7d04abffe0b794e2321ec5964c9054619f199bfb69e75a62f609f01`。
文件还包含后续135个对局UDP报文，不能沿用早期“无UDP”的前缀描述。

新REA人物展示证据保存于`room-ui-rea.evidence.json`及可恢复snapshot；镜像哈希
仍为`1cfec4a2e40e8003fea722627d95ec7a67c8ad102a0cec55f7284dd9a0501f0d`，
绑定本页原EXE哈希。

| 地址 / 结论 | 来源、覆盖 | 未验证项 |
| --- | --- | --- |
| `0x7cad60 -> 0x7c6dc0`按成员`+0xb0`和队伍布置角色，交给`0x620880` | 新REA；复用`room-policy-76284.json`确认两队实际槽位均为0..8，排除“复制真人槽位导致全部重叠”的初始猜测 | 真实角色创建/渲染链路 |
| `0x7c54b0/0x7c5500`查询/分配38项、步长0xa8的外观缓存；`0x7cbab0`接收0xa0字节外观后调用`0x7c69f0/0x620ca0` | 新REA；`0x634870 case18`与`0x628b90`为外观消息消费者；现有只读成员外观区全零 | 人机外观消息尚未接入，不声称渲染已修复 |
| `0x7c6950/0x7c68a0`加载namesTable或namesTableEnglish，并为原生补位角色选名/装备 | 新REA，语言决定名字表；原表为此前只读提取证据 | 当前赛单补位开关、与botClassTable实际对局配装的关系 |

按用户最新优先级，人物展示暂停在以上证据位置，先接Rust地图加载。

### Rust UDP基础阶段（地图接入前）

`codol-match319 serve room.json`接收当前房主名单，保持18人的UID、槽位和队伍，
仅绑定回环UDP；支持现有代理的直接connect/challenge=0、stats上传与停止文件。
分片覆盖乱序、重复、冲突、长度/索引错误及严格32768字节zlib输出；档案仅留内存。
服务端序号/确认号封包及XOR由当前客户端原生函数离线消费，未使用3.3布局。

| 地址或输入 | 来源和覆盖 | 未验证项 |
| --- | --- | --- |
| `0x470a60` | 新REA与Unicorn，4种命令内容及512项历史环绕，消费Rust封包 | 真实客户端连续收包、分片与压缩标志 |
| `0x7f6df0 / 0x7f6ec0 / 0x7f6b00` | 新REA；Unicorn原生发送器产生27片原始stats及预压缩stats，Rust重组；错误响应掩码为`0x07ffffff` | 原生压缩函数、真实对局stats生命周期 |
| 既有Seatown代理的原始connect报文 | `runtime/instances/codol-3.19.26.22-911c42a0027c/matches/1792149611999599500/diag-host319.jsonl`，SHA-256 `eda60c82f3c1fcf19c52c2cb8162c195bac66f074369a1b8d7570f5eb3c393f8`；直接challenge=0、无protocol字段 | 此输入为原始报文日志，尚无本轮核弹小镇真实UDP抓包 |

分析镜像`udp319.exe` SHA-256：
`f4f06040b1c6fe03b3e24c9aeb927a4fcbc581c37edc3ada6d941564fbd3fc68`；
REA证据/快照位于`work/codol319-nuketown/udp-rea.*.json`。
定向测试已通过：transport 7项、packet 3项（已启用原生重放）、真实回环UDP
进程测试1项、原room_cli回归2项。保存时复用这些结果，未重复全套构建或测试。
该阶段尚未接通gamestate、快照、输入、地图或AI；后续进展如下。

### Rust地图加载与首帧（2026-10-17）

`b0f77b6`在名单确认18人且真人Ready后发布当前房间请求，保留UID、名字和
原生名单；`1dc9fc3`交给版本内Rust服务。未准备、名单未确认、取消准备和切换
赛单有定向回归。每次游戏启动仍只接一场。

上述最终抓包以tshark的`udp.payload`核对：560/561为connect/响应，564/565
为压缩stats/statResponse 0；569、575、577为序列1～3的EOF，579为序列4
gamestate（UDP载荷135字节、正文127字节）；580、581、586、589、592、593
依次为gamestateupdate 1～6。peer为127.0.0.1:57042。此时Rust没有首帧，
客户端序列5～121重复确认gamestate并带可靠命令`qtalk.hal 0 0 0 0 0 0`。
用户反馈仍在加载。统计见本机`work/codol319-map-load/udp-loading.json`。

当前PID的first-netchan快照重建NCS为`E1D5A30A`，与stage6原生结果一致。
这不证明世界挂载：后续只读检查时房间已为空，活动clipMap仅有`mp_ui_viewer`，
不能据此断言核弹小镇从未载入或已完成挂载。

| 地址 / 结论 | 来源与覆盖范围 | 未验证项 |
| --- | --- | --- |
| `0x4709e0`客户端DATA正文XOR依赖确认号、serverid、challenge及可靠服务端命令历史 | 复用udp319的REA结论；新REA及Unicorn执行本版原函数，核对真实序列1、5、121，见`client-crypto.json`。当前服务端命令历史为空 | 非空可靠服务端命令、移动正文 |
| `0x662e41..0x662e62`以类型15查clipMap，复制0x40个word至`0x77e1c00` | 全镜像REA超时后r2初筛，新REA原指令交叉确认；不依赖截断的伪代码 | 实机核弹小镇clipMap挂载 |
| `0x617045..0x61705c`读取clipMap+0x98的MapEnts，再取其+4实体文本，写解析游标`0x3143770/0x3143774` | 当前版本r2指令与新REA原字节一致；离线zone中对应MapEnts头含文本指针和长度 | 原服出生点分队/选择规则、当前地图实际消费 |
| `snapshot_fields319.json`玩家246字段及表地址 | 复用本版EXE字段导出和Python编码器参考；Rust首帧逐字节对照，连续帧flag0；真实回环覆盖重发、确认、后续帧 | 新Rust帧的完整原生CG消费、地图画面、移动/武器/AI |

以上绑定本页原EXE哈希。受限镜像`map-consumer319.exe` SHA-256为
`f236fe4a38a2cbe2ea41e82857717a431391be16751fc801fb71c724ffa216af`，
来自已有本版代码快照；完整镜像`analysis-client319.exe` SHA-256为
`4fa4db2b90a3590aea271904096021dcbed28f81dc84b42607e7c9285469cdd3`。
本机`work/codol319-map-load/rea-map-consumer.evidence.json`及`.analysis.json`
保存11条新REA证据、0条可重放查询绑定。不得称完整镜像分析成功；受限镜像
对未包含函数的调用可能被误判为不返回。

出生点从原游戏`IIPS/IIPSDownload/ff_init_mp_nuked_V74.ifs`生成：先校验IFS，
用源码构建的IFS读取器提取，FF461解码验证签名与块，再校验zone哈希。
版本内`resources/definitions/nuketown319.json`仅保存哈希和偏移，资源不入Git。

- IFS SHA-256：`6949721e772917b17cfed32e3f2e212852a2c1d466595d58a7822dc81627a810`。
- FF SHA-256：`cba6309d58ab5614f5ab1eb85238700cf743addc907cc8387ad7d7e8886590a0`。
- zone SHA-256：`0c6171361ee9f450cc973471360a5aea5254f6c94b00421bbece144bc67ecf38`。
- 实体文本偏移`0x264fed9`、含终止符130443字节；共87个`mp_tdm_spawn`。
  本地首帧选第一个`[-1601.8, 1176.2, -24]`、yaw330，这是实验选择策略，
  不声称原服规则已恢复；未借用3.3坐标。

Rust在阶段6后主动发静止、无武器的玩家基线，确认后发flag0连续帧。
可靠客户端命令按连续序号确认并参与服务端XOR；暂不解码移动或模拟AI。
首帧不等待move、重复阶段6不重置时钟、未确认基线重发原序列，均有回归。
新增测试先红后绿：首帧2项、可靠控制2项、加载状态3项、出生点2项、Python
交接1项；transport7项及扩展的真实UDP进程测试通过。房间9项、真实TCP1项、
Seatown生命周期6项通过后未重复全套；本次release构建4.53秒。

A盘实验房间交接文件已备份更新，保留此前验收的启动组件。PID64480已到大厅，
门控经哈希和原字节检查安装；新抓包为`work/codol319-map-load/first-frame-live.pcapng`。
助手等待本次真实Ready，不再回放旧房间请求。仍待人工开局，构建和回环通过
不能表述为地图画面已显示。8名队友展示、原版配装、对局AI、移动/战斗后续继续。

### 地图画面验收（2026-10-17晚间）

复用`1dc9fc3`和REA已存快照，启动固定A盘PID50876。用户截图已显示核弹小镇
绿房、庭院和HUD；本轮地图画面通过，尚未验证移动、武器或AI。截图中未显示
第一人称武器、小地图为空，与当前静止无武器首帧范围一致。

实机Rust为PID47152，run为
`A:/CODOL-Lab/ready319-20261017/matches/1792241041425579000`。
冻结启动器的`startup.json.match`仍为waiting；本轮对局由单独实验助手接管，
实际服务状态在`nuketown-experiment.json`，不能只看旧启动器字段判定未开局。

证据保存在本机`work/codol319-map-live-20261017/`，绑定本页3.19 EXE哈希：

| 证据 | 已验证范围 | 未验证项 |
| --- | --- | --- |
| `map-visible.png`，SHA-256 `f6896f2ec1b4c40479916d06b642d914c9630cbbf1fbca7f26a6d05ac30af0b1` | 用户提供的地图场景画面 | 操作手感、武器、队友和AI |
| `map-visible.pcapng`，SHA-256 `9821f46cac495f373b49326069af6d935a1f9f148ea5e8055a9b82af53d4bcff` | 持续抓包的完整块前缀，非最终全程文件。帧652～665为加载1～6；666为基线seq5/flag8，676确认seq5，677为seq6/flag0。共2381个快照报文，末尾客户端确认seq2380。正文按已获原生验证的本版XOR解码，未出现缺失可靠命令历史 | PCAP中19414个move报文的正文及模拟结果未验证 |
| `mapents.json` / `mapents-comparison.json` | `0x617045`消费者原字节与缓存一致；运行时clipMap `0x2810380`、MapEnts `0x295fed4`、文本 `0x2a46b680`，运行时指针未重定位。130443字节实体文本与原zone偏移`0x264fed9`逐字节一致，SHA-256 `b75d5df2553414b10a2356ec9a1b20f92b2b90a05aaaab8f7f85081f952e1ce8` | 原服出生点分队/选择规则、碰撞模拟 |

此轮没有新增反编译结论；复用上一节REA快照，补上真实客户端消费、资源挂载与
画面证据。已有出生点、封包和状态机测试未重复执行。地图载入阶段完成，完整
9V9对局、同队角色展示、武器/移动/AI及小地图仍在后续范围。

### 移动输入解码与服务端移动（2026-10-17晚间，离线）

无新增反编译：usercmd 布局复用本版本已验证的 Python 参考
（`match_host/client_message319.py`，原生写入器`0x66F410`的逆、密钥`0x5B2E96`、
包写入器`0x5B2C10`、正文变换`0x4709E0`），全部结论以2026-10-17真实回环抓包核对。
本轮没有重启游戏；运行现场（PID50876/47152等）保持交接时状态。

最终抓包 `work/codol319-map-live-20261017/session.pcapng` 已由tshark按计划
于21:12:43结束收尾，共322,664包、1764.6秒：客户端→服务器289,472包，其中
289,460个move包全部为增量op0、0条moveNoDelta、0条解码错误；首个move在帧676
（基线确认后），每包2条usercmd（重复上包最新+新增），server_time自1000起、
每条5～6ms（约180fps逐帧生成）。

| 证据 / 结论 | 来源与覆盖 | 未验证项 |
| --- | --- | --- |
| Rust usercmd解码与Python参考逐字段一致（134个真实包×3窗口：head/moving/tail） | `tests/client_move.rs` 对 `tests/fixtures/move319-*.json`；fixtures由已验证解析器从全链基线生成，含buttons/angles/move_class/条件字节字段/预测尾迹 | 非空可靠服务端命令下的正文混入与命令哈希（本轮服务端未发布服务端命令） |
| 客户端预测origin全程冻结在出生点 | 真实抓包：用户按住LEFT（cls=8）约1.3秒、buttons位0x8000000保持、早期按过开火位0；预测尾迹始终为出生点[-1601.8,1176.2,-24]且时间正常推进 | 预测冻结原因未定位：截图无菜单遮挡、HUD/小地图在、无武器（弹药0、按1提示）；候选：无武器状态、pm_type/flags或武器状态机阻断pmove，需新REA（CL_Frame/pmove门控）或实机对照 |
| 移动窗口内含可靠命令18～21（`n 85`等） | fixture解析统计：60包无命令、14包携带 | 这些命令的语义未查；session严格连续编号门控如实拒绝跳号包 |
| Rust服务端移动闭环 | `src/movement.rs`：live_sim319无碰撞积分器（Q3摩擦6.0/加速10.0/速度190/步长上限200ms/z锁定）+C1wish缩放（后0.7/侧0.8/疾跑1.5）+16单位reconcile；角度按short差分累计到出生朝向（首条cmd yaw=0而出生yaw=330） | 实机客户端跟随服务器origin的画面表现；碰撞、跳跃、攀爬未实现 |
| 快照逐字节对齐Python编码器（4个移动状态含负速度/pitch） | `tests/movement.rs` 的 `snapshot_bytes_match_the_python_codec_for_moving_player_states`；`Snapshot::set_player`更新origin 8/11/10、velocity 14/13/16、pitch 19、yaw 18 | 原生CG对移动中快照的实际消费 |
| 真实移动轨迹复现参考 | `move319-trajectory.json` golden：74包reconcile全采纳（冻结客户端把服务器拉回出生点，符合容差设计）；无reconcile纯积分向yaw330左侧移动约18单位（方向与+0.5/+0.866期望一致） | 实机闭环时客户端回显服务器新origin后的反馈 |

Session按包链维护usercmd基线并驱动Movement；tick把origin/velocity/pitch/yaw
写入快照、command_time取最后执行的命令时间（未收到move前仍为stamp）；
disconnect重置基线与移动状态。可靠命令前缀、加载门控与快照基线行为保持
原回归（40项通过，release构建验证）。生成脚本与case记录在
`work/codol319-move-input/`。此阶段只完成解码与服务端模拟：移动的实际画面、
手感与客户端冻结问题的实机结论待下一次启动验收，用户已同意随时联调。

## 定向测试

```powershell
powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 test --offline --manifest-path "$PWD/games/codol/versions/v3_19_26_22/server/native/match-server/Cargo.toml" --target-dir "$PWD/runtime/builds/codol/v3_19_26_22/rust-match" --test room
powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 build --release --offline --manifest-path "$PWD/games/codol/versions/v3_19_26_22/server/native/match-server/Cargo.toml" --target-dir "$PWD/runtime/builds/codol/v3_19_26_22/rust-match"
python -B -m unittest discover -s games/codol/versions/v3_19_26_22/tests -p 'test_room*.py' -v
```

Rust新增host_roster、room_cli各2项测试均先失败后通过；Python房间状态/原生
事件解析4项与生产TCP联调1项通过。大厅改动后库存7项回归通过，包括真实
TCP登录任务和原生读取；没有重跑全项目套件。此阶段不证明实际游戏画面。

移动输入阶段新增`client_move` 2项、`movement` 6项测试（真实包解码对照、
合成边界、golden轨迹、reconcile容差、快照字节、session集成），先红后绿；
全套crate回归40项通过，release在临时target目录验证（正式release输出被
运行中的实验进程锁定，未打断现场）：

```powershell
powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 test --offline --manifest-path "$PWD/games/codol/versions/v3_19_26_22/server/native/match-server/Cargo.toml" --target-dir "$PWD/runtime/builds/codol/v3_19_26_22/rust-match" --test client_move --test movement
```
