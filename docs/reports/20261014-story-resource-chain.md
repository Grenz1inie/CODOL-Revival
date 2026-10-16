# 首关资源消费者与服务端适配

状态：首关、基础地图和公共依赖的模型、材质、动态对象、特效及碰撞离线转换已通过。商城包图片共享引用已修复；新版资源表排序、编号和CRC已实现离线计算。完整世界初始化、gamestate/快照/输入及主剧情逻辑仍未打通，尚未进入可操作关卡。旧启动器按用户纠正以静态参考为主。游戏验收由用户执行，本轮未要求重复点击，也未重载正式服务。

## 1. 输入与范围

实验产物均在 `research/experiments/story-native/`，代码在 `tools/`，REA 证据在 `research/evidence/`。原游戏、正式存档与系统设置未修改。

- 客户端 SHA256：`e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。
- 参考引擎 SHA256：`1736926655100b53499ae75ea5bddd0741983c12c89cdb51d49aef8a0be03243`。
- IFS2.dll SHA256：`5b0324e0b2ba3545a6c02626287d4fbc6a3116594744f4647333982d85508421`。
- 仅首关 `coop_training_mp_cargoship/coop`、其基础地图 `mp_cargoship` 及公共、画面、商城依赖。基础地图不是拿 PvP 代替剧情的验收目标。

## 2. IFS → FF → 资源目录

`ifs-read.c` 调用当前 IFS2.dll 解析副本，读取自身目录表和原始存储块。构造/销毁是 stdcall，虚表方法是 thiscall；销毁参数是接口指针的地址。目录项0x80字节，文件偏移为64位，名称指针在+0x38。未初始化的跨包文件ID表计数为0，不能据此认定IFS为空。

首阶段提取结果：首关7包325条记录、基础地图8包332条、公共依赖2包7条，共17包。后续加公共画面、商城各1包，当前共19包。首关清单318个去重路径全部找到；315个 loose payload 解码成功。重复补丁文件保留各自来源，尚未推断最终覆盖顺序。清单记录输入、副本、提取工具及输出哈希，原包/副本均未被DLL改写。

FF外层是 `IWff0100`、版本 **0x1A7（423）**；此前十进制写成427是笔记换算错误。历史实验文件名中的 `427` 暂保留，已生效补丁一直使用 `a7010000`。签名头 `IWffs100`。从当前客户端读取内嵌材料，验证签名、每张哈希表和每个数据块后解压。FF的AES CTR计数是小端，不能套用 loose 文件解码的大端计数。地图名按客户端规则截断为31字节。参考工具的 `ReadClientRegion` 使用 fseek 文件偏移，不能传VA。

目录头在zone偏移40；字符串后是16字节资源项（类型、相对40的偏移、指针、负载长度）。资源项既可能携带数据，也可能是零长度的共享引用；类型14/17/18在当前客户端被置空。共享引用不能当作“文件丢失”，也不能凭目录顺序构造最终运行时ID。

| zone | 解压字节 | 资源数 | 发现 |
| --- | ---: | ---: | --- |
| coop_training_mp_cargoship | 21583990 | 1174 | 12张NCS、附加实体、模型、特效、武器、9个rawfile |
| coop_training_mp_cargoship_const | 10488 | 2 | 首关实体基线 |
| mp_cargoship | 87492551 | 338 | 碰撞图、渲染世界、公共世界等基础资源 |
| common_mp | 110773546 | 9329 | 公共武器、动画、菜单和注册资源 |
| common_gametype_coop | 41560572 | 1612 | 合作玩法公共模型、武器与动画 |

首阶段另有6个加载图、本地化或基础地图常量zone，合计解码11个FF。该阶段计数和rawfile路径见 [资源清单](../../research/experiments/story-native/zone-assets/manifest.json)。公共/本地化NCS当时有5张含共享引用；现已按同一zone的持久块解析，详见下一节。

继续核查 `ff_init_common_gfx_V43.ifs`，恢复10个FF并逐块验签；累计18个提取IFS、21个FF。该包新增两份 `mp_ui_viewer_fx.gsc`，均为UI地图特效脚本，没有找到首关主脚本。其文件和rawfile目录见[公共画面包清单](../../research/experiments/story-native/resources-common-gfx/manifest.json)。

本轮再提取 `ff_init_common_marketplace_V38.ifs` 的2个FF，累计19个IFS、23个FF。重新核验全部23个FF的签名、哈希表及数据块，见[脚本来源审计](../../research/evidence/story-script-origin-audit423.json)。商城包包含8728项资产，不能因零长度共享图片条目而判定文件缺失。

### 2.1 当前客户端资源编号与校验

实现位于 `games/codol/versions/v3_3_3_3/reverse/tools/story_netconst423.py`，不沿用2697的资源bank。REA链：`0x5855d0` 计算网络变量名种子 → `0x5857b0` 建运行时表 → `0x585000` 排序资产表 → `0x584d80` 跨表去重 → `0x584ed0` 分配编号并累计CRC。布局读取当前客户端 `0xc57118` 的21条记录；新增sts为17类，codinfo/codinfovalue/network依次为18/19/20。中文索引11在 `0xcdbc1c` 的代码为`chi`，不是参考源码传入的`chinese`。

- 排序依次为source、type、本地化标志、名称逐字节顺序；长度大于12的名称在+8处检测`chi_`。同表内重复值保留，只删除同类型早先表已有的值。
- configstring使用各类别自己的起点、容量和保留槽；15类不进入常量索引。CRC按新增字符串字节连续计算，不含NUL，必须显式传入已验证种子。
- `read_ncs` 共享名称/数组/字符串只允许引用同一zone已经重建的块3范围；未知块、越界、截断仍失败，不把地址“看起来有效”当作解析成功。
- `Read-PlayerSchema.ps1 -Netconst` 对核验后的当前客户端只读提取193个网络变量名、152个codinfo名；重算得到`0xcdb31851`，与进程种子一致。它不写进程，也不触发开图。见[实时注册证据](../../research/evidence/live-netconst-registration423.json)。
- 十个候选依赖合并为61张NCS，全部引用已解析；候选CRC `0xc6280541`。例如三种载具对应configstring3076–3078，三种sts对应6344–6346。完整来源、块哈希、名称和编号见[候选注册表](../../research/evidence/story-netconst-candidate423.json)。

**候选表尚未通过地图运行时验收**：当前种子来自大厅进程，选择的资产集合尚未与首关加载后的客户端比对；运行时变量值表、网络发布及快照也未完成。旧引擎 `CODOL_LoadMountedNetConsts` 拒绝423版输入的负例保存在 `netconst-source423.log`，未修改其门禁来伪造成功。当前实现直接按新版契约离线读表。

证据：[排序](../../research/evidence/client-netconst-order423.json)、[去重与语言](../../research/evidence/client-netconst-dedup423.json)、[种子计算](../../research/evidence/client-netconst-seed-writers423.json)。

## 3. 初始实体状态的实际消费者

文件 `mp/constbaselines/bl_pc_coop_training_mp_cargoship_coop.bin` 为190408字节。

REA链路：

1. `0x584880` 查询 `mp/constBaselinesTable.csv` 的地图/玩法适用关系。
2. `0x5849f0` 拼出rawfile名，核对 `IWCB000\x01`、长度、实体编号与类型。
3. 首关包含700条、每条0x110（272）字节；编号27..813并不连续，697条类型6、3条类型11。
4. `0x46c250` 按**记录序号**复制基线；`0x46c2f0` 在新实体解码且snapshot flags含0x10时调用它，然后以网络实体编号覆盖首字段，再应用delta。

磁盘状态和运行时原点编码分开处理。不能把基线序号当实体编号，不能把此文件直接当作可发送的完整snapshot。玩家状态仍需适配：当前客户端235个字段描述，参考引擎229个；字段数或偏移碰巧相同不是语义匹配证明。

解析器和测试已覆盖700条上限、空基线、错误头、截断、额外记录、非法编号/类型以及客户端允许的编号2048边界。输出保留原始rawfile，不改磁盘坐标。

## 4. 剧情资源与逻辑缺口

[实体审计](../../research/evidence/story-resource-dependency-audit.json) 从首关附加实体中恢复956个对象，包括出生点、敌我角色、直升机及触发区。可见 `intro_player`、`intro_rappel_start`、`bridge_flags`、`escape_flags` 等剧情标签。

目前检查的23个FF中发现6份GSC，均为剧情/基础/UI地图的特效文本，另有26份ATR动画树。唯一尚未还原名称的rawfile（基础地图第337项）压缩和未压缩长度均为0，不包含隐藏的主脚本负载。这是**已检查包的结论**，不是全盘不存在脚本的证明。实体标签给出触发对象和连接线索，但没有提供任务执行顺序、AI行为、目标判定和失败处理的全部实现。基础地图的AI路径目录项为空，也不能直接认定客户端具备完整服务端导航数据。

因此反推服务端应分层进行：先将当前资源转换成实际碰撞/出生状态，再完成注册表、实体/玩家delta和输入；最后按实体关系与更多脚本消费者证据重建任务逻辑。显示加载画面或让静态场景出现都不足以证明剧情恢复。

脚本来源追踪：参考引擎 `GScr_LoadScripts(0x467a0a)` 寻找 `maps/mp/<mapname>::main`；`Scr_LoadScriptInternal(0x4672c3)` 尝试 `.gsx` 再 `.gsc`，经 `Scr_ReadFile(0x586fee)` 从脚本根目录、overlay、loose文件及FF rawfile读取。参考包的 `scripts/coop/maps/mp/gametypes/coop.gsc` 是作者重建的基本出生/武装/存活流程，其注释将目标、AI、载具、突破和复活列为后续工作。基础 `mp_cargoship.gsc` 仅加载地图公共逻辑，不是首关剧情脚本。

完整本地参考包又核对1198份GSC/GSX、98份overlay脚本及其哈希。其 `room_host2697.py:88–89` 固定`mp/war`，指定`scripts`及`script-overlay2697`。按该真实配置解析，`maps/mp/coop_training_mp_cargoship`与`maps/mp/gametypes/coop`均找不到；基础货轮命中overlay中的`maps/mp/mp_cargoship.gsc`，只调用公共加载、设置小地图和阵营。参考源码 `load_target_map` 也明确限定MP。另一个`coop/`子目录里有基础脚本，不表示启动器实际选择了它，更不代表原剧情已恢复。路径优先级和逐文件证据见[脚本来源审计](../../research/evidence/story-script-origin-audit423.json)。

当前客户端 `0x435f60 → 0x435e20/0x435920` 的下游已追至 `0x435b00/0x435740`：它们解析 `loadfx`、`createLoopSound`、`createOneshotEffect` 等特定文本，不是主任务脚本虚拟机。另对15个公共loose包只读列目录，共8878项，未发现GSC/GSX/CSC/ATR；这不覆盖所有FF或其他未检查包。证据：[客户端特效解析器](../../research/evidence/story-fx-script-parser-and-reference-loaders.json)、[公共目录](../../research/evidence/story-common-loose-directory.json)、[参考脚本来源和哈希](../../research/evidence/reference-story-scripts.json)。参考脚本中关于其他地图的作者注释尚未经本项目验证。

## 5. 参考引擎实验结果

`games/codol/versions/v3_3_3_3/reverse/tools/story_engine_patch.py` 校验固定原始SHA和每处原字节。归档实验适配版本分支、材料位置及下述布局，并将缺少的附加实体读取器编译进独立PE节；保留ASLR、签名、块哈希和资源长度校验。配置字符串10位补丁是另一份副本，未混合成默认对局引擎。

`--codol-archive-probe <FF路径> <客户端路径>` 在引擎网络初始化前返回。实际结果及输出哈希以 [探针清单](../../research/experiments/story-native/archive427-probes.json) 为准：

- 首关/基础地图常量包、两张加载图：完整资源重建通过。
- 首关主包：1174项资源流通过；68个模型转换通过，包含8864个碰撞三角形、6组共享三角形数组；12张NCS均被原生运行时读取器接受。
- 基础地图：338项资源流通过，`collision_conversion map=mp_cargoship status=1`。包含18346个平面、27472个刷体、49762个顶点、68916个地形三角形和470302字节实体文本。

单包归档探针不提供模型解析器，因此其 `unresolved_models=9173` 不表示缺失9173个模型文件。随后使用 `--codol-runtime-probe <客户端> mp_cargoship <FF...>`，联合挂载 `code_post_gfx_default_mp/code_post_gfx_mp/common_mp/mp_cargoship/coop_training_mp_cargoship` 五个FF，得到 `instances=9173 unresolved=0 model_calls=9173 failures=0`；原生碰撞构建包含929种材质、27472个刷体、68916个地形三角形、5071个叶节点。动态世界转换也已通过：246个模型、8个特效、246个物理预设绑定及64个触发模型，最终 `runtime_complete ok=1`。见[世界探针记录](../../research/experiments/story-native/runtime-world423.json)及其日志。此入口明确报告 `published=0 physics_activated=0 engine_started=0 network_started=0`，不等同于实际剧情开图。

新增兼容点：

- `story_collision423.c` 按当前顺序定位碰撞子流；72字节子模型较旧版增加cinfo指针，阶段列表从clipMap头恢复到实体读取器。共享刷体索引的背后存储不能再算一份叶节点索引。当前限定货轮的布局；混合共享叶索引、不同子模型cinfo仍明确拒绝。
- 材质依赖查找与原生材质转换同步采用104字节头、名称+16、标志+20、表面信息+24；只修资源重放不会自动修复这两个消费者。
- 商城包第506项图片引用`0x301f4ae1`指向材质纹理字段，而不是新插入槽。按当前客户端`0x488bd0 → 0x4888f0 → 0x487d60`，纹理记录12字节、图片指针+8，在持久纹理字段登记类型10别名，遇到-2时同时登记插入槽。`replay_material423`修复了旧读取器遗漏的字段别名；单包8728项回放现已通过，仍保留两阶段长度和类型校验。见[材质图片消费者](../../research/evidence/client-material-images423.json)、[纹理记录](../../research/evidence/client-texture-images423.json)、[图片指针](../../research/evidence/client-imageptr423.json)。
- 公共菜单采用现有404字节菜单、392字节item分支。配件记录类型改为首字节，新增字符串类型42/43；不能继续读取旧版+4的类型字段。
- 公共包类型45按客户端 `0x496ca0` 及子读取器完整消费固定头、嵌套数组、字符串，保留原始数据与块分配。此适配不声称已经实现该类型的游戏逻辑。
- 公共包三项零长度共享条目必须找到同类型的既有资产。重放阶段登记表尚未排序，不能提前调用运行时二分查找；不接受未知或跨类型引用。
- 原生特效读取与打包也须采用64字节视觉采样；只修改资源重放仍会使灭火器特效 `props/fire_extinguisher_exp` 在运行时解码失败。完整保留64字节数组，不以48字节截断复制。
- 货轮动态对象156引用的物理预设是 `,weapon_light` 占位项。当前客户端 `0x49e570` 从 `0xce0540[0]` 指定的 `default` 复制模板，类型0没有额外转换回调。因此仅对已验证的423版、类型0、显式外部引用采用当前默认包的真实模板，并输出 `runtime_preset default=default requested=weapon_light`。这不声称恢复了原服务端专用预设；缺失默认模板、其他类型与非占位定义仍失败。

证据：[原生材质字段](../../research/evidence/dedrun-native-material-layout423.json)、[当前菜单](../../research/evidence/story-menu-layout423.json)、[新增类型](../../research/evidence/story-type45-layout423.json)、[动态记录登记](../../research/evidence/dedrun-dynamic-record-registry423.json)。

模型在 `_CODOL_ReplayZoneAsset → ReadXModelExtent → ReadXModelBounds → ReadXModelCollision` 中先做独立长度检查，之后才进入 `replay_model`。材质两套消费者现已同步：当前材质0x68字节、名称+0x10、三个计数+0x50/51/52；图片0x34字节；技术表0xD0字节、48项。此前 `material-candidate-patches.json` 只记录未通过阶段，不能代表当前已集成结果。

特效视觉采样由48改为64字节；撞击特效表由16改为19行，每行35个引用。渲染世界采用0x648字节头及扩展数组。附加实体头由36变为52字节，增加碰撞信息、子模型等子流；武器0xe28字节、曳光0x74字节并新增特效引用；当前碰撞图仍为256字节头，但内部字段顺序改变。新读取器在 `games/codol/versions/v3_3_3_3/reverse/tools/native/story_archive427.c`，保留分配边界与两次重建流程。类型14/17/18仅允许客户端实际置空的零长度目录项，不生成虚构AI导航。

模型重定位回归曾暴露一个适配错误：新武器读取器将物理预设与碰撞模型的回调接反，68字节预设被按72字节读取，名称开头被吞掉，后续块3共享骨骼地址出现16字节偏移。源流长度检查仍会通过，因为字符串变短抵消了头部多读；因此增加模型转换成功断言，先确认失败，再修正回调映射。客户端 `0x489e60` 对应参考 `0x550d9e`（预设），客户端 `0x48a0f0` 对应 `0x550d80`（碰撞模型）。证据：[类型消费者](../../research/evidence/story-physics-preset-map423.json)、隔离目录下的 `weapon-allocation423.gdb.log`。不能用填补16字节或跳过骨骼校验替代修复。

`ReplayZone` 遇到后续失败会释放上下文，随后 `ReadNetConst` 全部失败并不证明前面NCS重建失败。不能删掉长度检查来制造成功。旧GDB无法在随机基址上插入静态断点；另有仅调试副本清除DYNAMIC_BASE的记录，此更改没有应用到探针正式实验副本、客户端或系统。

按用户“旧启动器以静态参考为主”的纠正，已移除普通启动探针脚本、撤回其四处正式挂载版本门禁修改；没有继续重建旧启动器或安装新工具链。历史`startup-r3tv5a84`保留图片第506项失败记录，该失败转为无引擎初始化的离线回归后修复。当前稳定世界探针报告首关附加实体174339字节、142个触发模型、169个hull、62个slab，最终`runtime_complete ok=1`；`published=0 physics_activated=0 engine_started=0 network_started=0`。

## 6. 复现与下一步

在项目根目录，使用已安装Python、cryptography、pefile及x86 GCC：

```powershell
# 仅编译器进程所需PATH；不要改变系统PATH
$storyBuildPath = $env:Path
try {
  $env:Path='A:\Coding\MinGW\bin;C:\Windows\System32;C:\Windows'
  gcc -O2 -Wall -static-libgcc -o research/experiments/story-native/ifs-read.exe games/codol/versions/v3_3_3_3/reverse/tools/ifs-read.c
} finally { $env:Path = $storyBuildPath }
python games/codol/versions/v3_3_3_3/reverse/tools/extract_story_resources.py
python games/codol/versions/v3_3_3_3/reverse/tools/extract_story_resources.py --base
python games/codol/versions/v3_3_3_3/reverse/tools/extract_story_resources.py --common
python games/codol/versions/v3_3_3_3/reverse/tools/inspect_story_resources.py
python games/codol/versions/v3_3_3_3/reverse/tools/export_story_zone_assets.py
python games/codol/versions/v3_3_3_3/reverse/tools/probe_story_archives.py
python games/codol/versions/v3_3_3_3/reverse/tools/probe_story_world.py
python -B -m unittest discover -s tests -p 'test_story_*.py' -v
```

提取命令拒绝覆盖已有目录；已提取时直接使用manifest，不删除历史证据重跑。`probe_story_archives.py` 本身完成不等于所有归档通过：逐项查看记录的引擎退出码，0通过、3资源重建失败。

后续按新版契约推进：核对实际地图依赖集合和注册值 → 完整世界初始化 → gamestate和首帧snapshot → 玩家输入 → 主任务逻辑。静态REA已确认`0x46dea0`在进入`0x465a30`前核对NCS CRC；当前玩家状态235字段，不能直接复制旧版229字段及其事件、武器编号。见[新版地图状态到初始化](../../research/evidence/client-mapstate-init423.json)。到实际具备新的可测行为后，再由用户验证对应地图、移动、射击及剧情触发。

前阶段60项测试保留在[历史记录](../../research/evidence/story-resource-final-verification.json)。本阶段材质共享引用、NCS共享块和注册算法均按失败→修复→通过执行；集中运行18项剧情相关测试全部通过。19个原IFS、客户端、参考引擎和源码ZIP哈希不变；2772个导入源码文件也均与提取清单一致。四处已撤回的启动门禁字节与原件一致。详见[本阶段验证](../../research/evidence/story423-validation.json)，其结果只覆盖离线消费者和只读数据，不代表游戏可玩。
