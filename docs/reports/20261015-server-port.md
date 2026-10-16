# 3.3.3.3 对局服务移植

目标：复用并适配 2.6.9.7 PVP服务端的通用对局能力，为当前客户端实现首关从开始战斗到地图加载、玩家操作的链路。这份参考没有现成的原版剧情实现；3.3.3.3剧情脚本的实际来源与任务逻辑恢复单独追查、估算和验收。资源解包或界面解锁不作为可玩验收。

## 实施与验证

1. 固定当前客户端的资源编号和网络读取契约。测试涵盖字段宽度、索引边界、截断与校验；以客户端实际读取函数作为独立校验来源。
2. 实现对应的回环对局流程，连接地图状态、快照和玩家输入。先验证协议与状态转换，再交付用户测试；不复用未经核实的旧地址或伪造匹配成功。
3. 用户验收首关加载、移动、射击与剧情触发。未观测到的行为保持待验证。

已获测试边界与分阶段本地提交授权。源码参考保留于 `research/experiments/story-native/reference-source/`，不直接改动；实验客户端、服务端与证据沿用 [隔离边界](20261014-dedrun-3333-compatibility.md)。

## 当前版本差异

当前客户端 SHA-256：`e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。

- `0x46db20`：武器别名数量为 10 位，旧源码为 11 位；配置字符串最大索引 7057。
- `0x46dea0`：地图状态携带地图名、类别和 NetConst 校验；旧源码把类别写死为 `mp`。
- 配置字符串的普通字节与位字段共用消息空间，普通字节写入不能擅自对齐位游标。
- 当前 NetConst 有 21 种布局，运行时值类型为 19；不能沿用旧版类型 18。

详细资源进度见 [首关资源链路](20261014-story-resource-chain.md)。以下阶段完成原生模块适配与离线客户端消费验证，尚未交付可操作关卡。

## 通用原生模块移植（2026-10-15）

保留旧服的 C/C++、汇编引擎及消息、资源、玩家输入模块，在独立副本应用 [源码补丁](../../games/codol/versions/v3_3_3_3/reverse/tools/native/server3333.patch)。没有另建 Python 对局引擎；`games/codol/versions/v3_3_3_3/server/story_wire423.py` 是协议研究原型，仅由离线测试使用。

| 链路 | 已实现并验证 | 当前边界 |
| --- | --- | --- |
| 配置与地图头 | 7058槽；10位别名数量；8位皮肤、9位扩展、14位配件；类别按地图传入 | 原始 `0x46db20/0x46dea0` 能读取，未执行地图加载 |
| 资源注册 | 21类布局、保留槽、中文前缀chi、顺序/去重/CRC；静态/动态名称双向解析 | 菜单与提示字符串从0编号；实际地图挂载集合尚未对齐 |
| 玩家状态 | 235字段顺序；受保护6位字段、13位组合字段；4个新增数组段；引擎位置/视角/武器转换 | 新版无旧服生产者的字段保持中性；仍需真实游戏预测验证 |
| 背包与生命值 | 生命值、武器槽、弹夹与备弹进入当前客户端数组 | 离线读取通过，不代表游戏内开枪成功 |
| 对局事件 | 当前162个名称/参数宽度；旧引擎事件按名称映射 | 全部事件编码由原始客户端读取；事件效果尚未实测 |
| 输入 | 当前客户端生成移动/视角/开火等命令，原生旧服解码；新增11位近战目标与第五个32位尾字段 | 尾字段语义待定；保留读取游标，不用于模拟 |
| 输入基线 | 按当前 `0x5a18e0` 重建武器、角度、姿态与瞄准位 | 与客户端机器码输出一致，不能替代移动闭环 |
| 分片与初始快照 | 分片步长1154；乱序/重复包；空及非空快照存入当前客户端基线 | 合成场景验证通过，实际地图尚未初始化 |
| 世界对象 | 实体61字段、23种表、事件基数22；客户端76字段；Actor24字段 | 创建、位置增量、类型切换、模型与挂接标签读取通过；新增能力值和组合状态语义仍待验证 |
| 配置发布 | 玩家名、环境、视觉、定位选择、图标、挂接特效与链接标签使用当前配置槽；266项网络变量注册 | 按消费者与原生发布函数验证，仍需实际挂载集合 |

关键新增证据：

- 玩家表 `0xc55f70`；[输入编码](../../research/evidence/client-usercmd-writer423.json) `0x5a1be0`、[整包发送](../../research/evidence/client-send-command423.json) `0x4602a0`、[输入基线](../../research/evidence/client-default-usercmd423.json) `0x5a18e0`。
- [事件表](../../research/evidence/client-event-profile423.json)：名称 `0xce4390`、参数宽度 `0xc56d70`，共162项。旧表135项，不能只沿用前面的相同编号。
- [Perk消费者](../../research/evidence/client-perk-player-consumer423.json) `0x43b5d0` 操作 `PS+0x4c0` 起的3个32位位集；`0x415520` 上限96。
- [玩家数组读取](../../research/evidence/client-snapshot-readers423.json) `0x5a4230`：新增4段位于备弹之后、任务目标与HUD之前。
- [实体消费者](../../research/evidence/client-entity-decoder423.json) `0x5a3670`：当前61字段、23种表，事件实体基数22；已替换旧62字段、22种表、基数21。增量测试同时核对客户端结果与服务端保留基线，包含位置量化。
- 当前客户端/Actor字段表为 `0xc55b68/0xc54298`，通用读取器 `0x5a34f0`。真实C语义适配与快照编码输出2个实体、1个玩家外观、1个Actor，原始客户端 `0x46d170` 完整读取并存入各环形缓冲区。
- [配置分发器](../../research/evidence/client-config-fixed-banks423.json) `0x57a300`；[玩家名](../../research/evidence/client-playername-instructions423.json) `0x4faec8`；[链接标签](../../research/evidence/client-linktag-instructions423.json) `0x50373f`；[定位选择](../../research/evidence/client-locsel-instructions423.json) `0x43923f`；[特效配置](../../research/evidence/client-tagfx-instructions423.json) `0x50e7fa`。旧编号部分越界，现按实际消费者映射；零起点字典的首个动态条目不再被遗漏。
- [死亡图标消费者](../../research/evidence/client-obituary-reader423.json) `0x50d270`：900以下为武器，900起为伤害原因；保留旧生产者700边界，在适配时重编号并处理DOG插入项。全部17种旧伤害原因及武器边界由当前读取器验证。

## 构建与复现

在项目根目录执行：

```powershell
& A:/Coding/Python3.13.7/python.exe games/codol/versions/v3_3_3_3/reverse/tools/build_native_server.py
& A:/Coding/Python3.13.7/python.exe -B -m unittest discover -s tests -v
```

构建工具逐个校验补丁涉及的参考文件 SHA-256，严格应用补丁到独立源码，再使用已有 MinGW.org GCC 6.3.0 x86、Git的sh/patch及便携NASM 3.02。NASM放在 `research/experiments/story-native/toolchain/nasm-3.02/`，不修改系统PATH；[官方压缩包](https://www.nasm.us/pub/nasm/releasebuilds/3.02/win64/nasm-3.02-win64.zip) SHA-256为 `161d0bfaff53c2f9e9f3e69fd0672323ebabafd1268976a5cec11be92a19aee7`。

旧源码编译需要 `-fpermissive` 接受既有的DWORD/LONG指针差异，并补充旧MinGW头文件缺失的 `AI_NUMERICSERV=8`。只用相同旧源码重编libtomcrypt中的一个CRT对象，解决工具链不一致；不修改原参考库。

产物为 `research/experiments/story-native/server3333/bin/codol_dedrun.exe`，[构建清单](../../research/experiments/story-native/native-build3333.json)记录源码包、补丁、EXE哈希和编译日志。它是未完成适配的实验构建，未接入控制器或正式大厅候选。

本阶段集中回归 **104项通过，40.827秒**，其中原生移植17项、Python协议研究17项。[测试日志](../../research/evidence/server3333-tests.log)。测试在临时目录从原始源码重建真实C模块；输入整包使用32位ABI程序，客户端侧用Unicorn执行固定哈希EXE中的原始读写函数。UI、时钟等边界调用被隔离，没有启动真实游戏、渲染或网络。

第二批原生适配 **23项通过，14.220秒**，[失败记录](../../research/evidence/server3333-publication-red.log)与[修复后记录](../../research/evidence/server3333-publication-green.log)保留。新增测试覆盖非空快照、对象类型切换、固定配置槽、静态/动态菜单边界、266项注册与损坏导出、死亡图标分区。这里仍是协议和语义接口验收，未执行用户的游戏操作。

第三批已将先前的423离线消费者移入原生源码，使用真实C调用替代旧EXE地址跳转：材质104字节头、持久图片别名、64字节特效采样、武器/配件资源遍历、45类目录、碰撞区段、72字节子模型及动态对象依赖。FastFile解密仍验证原有签名与长度；共享目录仅接受已有同类型别名，空客户端AI条目不被当作导航数据。

三个资源集成测试先记录[旧版格式失败](../../research/evidence/server3333-assets-red.log)，修复后 **3项通过，8.413秒**，见[结果](../../research/evidence/server3333-assets-implementation.log)。未改动的商城8728项、首关1174项、基础地图338项资源均完整重建；五包联合生成9173个静态模型实例、246个动态模型、8个特效、246个物理预设及64个基础触发模型，未发布世界或激活物理。原生协议23项回归同时通过。新源码构建的隔离启动已完成九个公共资源包初始化，但随后被旧目标入口的MP限制拒绝，见[启动失败](../../research/evidence/server3333-startup-red.log)。正式服务和客户端没有重启。

## 下一段闭环

第四批复用了源码已有的类别与附加地图流程，限定当前验证过的 `coop / mp_cargoship / coop_training_mp_cargoship`。隔离启动已挂载四个地图资源包，随后停在武器注册 `none`，见[真实启动记录](../../research/evidence/server3333-startup-map.log)。旧服的服务端文本通过既有脚本读取器加载；当前FF内同名资源仍优先。

武器依赖读取已按当前加载器 `0x4915b0` 适配：10个前置模型、`+0x38`隐藏标签、3组56项动画、35个特效槽、18个视觉依赖及当前尾部依赖。保留所有条目与原偏移，仍检查完整消费和解析失败；没有把423原始结构交给旧版运行时。AK104、沙鹰、白磷弹、闪光弹的完整源数据读取已通过[先失败后通过的测试](../../research/evidence/server3333-weapon-source-green.log)。这尚不包含武器运行时构造、弹药编号或射击验收。

可用 `python games/codol/versions/v3_3_3_3/reverse/tools/probe_native_server.py` 重现原生初始化边界：仅启动本项目新构建的隔离服务端，绑定回环28970端口，最多40秒，自动结束它创建的进程；不启动客户端。命令、日志和构建哈希保存在独立实验目录。`ready`只表示地图初始化与资源发布探针通过，不代表客户端已经连接或可操作。

1. 保留新增能力值和组合状态的未验证标记；用真实地图对象核对已适配字段，不把合成快照等同于可玩地图。
2. 423资源消费者已接入源码；继续复用既有类别/附加地图装载流程，核对实际资源集合、注册种子和地图CRC。当前仍缺武器运行时字段转换，资源遍历通过不代表能开枪。
3. 完成回环握手、房间预订和真实地图启动后，才交给用户验收加载、移动、射击；原版剧情脚本继续单独跟踪。


## 地图状态与武器注册（第五批）

当前读取器 `0x49a320` 不再装载旧 GameWorldMp。首关的12块玻璃仍在 FxWorld，`0x48c7b0` 保留116字节头和实际放置数据。原生端校验重放记录、数量和范围，使用这些位置初始化新对局的完好玻璃状态；没有虚构原版命名玻璃组或历史损坏记录。AddonMapEnts 名称定位改为423的52字节头，已复用旧服的实体合并和触发索引重定位。

隔离初始化现在得到：5071个碰撞叶、246个动态实体、69盏主灯、12块玻璃，以及64+142=206个触发模型。实体文本由470302字节合并至644417字节，见[启动证据](../../research/evidence/server3333-startup-world-registry.log)。随后进入 `G_SetupWeaponDef`，在 `none` 的武器运行时构造处拒绝当前数据；没有越过校验或发布可用候选。

当前武器注册规则由原始客户端函数验证：`0x42bfa0`弹药、`0x42c1b0`弹匣、`0x42c0a0`共享上限、`0x42c270`备用武器、`0x42c3e0`递归注册。编号使用武器槽位，不是旧服的连续弹药池编号；独立去重标志、大小写规则、共享容量冲突和备用弹匣继承均已适配。测试直接执行这些函数，只替换资源查找边界，保留递归注册与继承顺序。

验证记录：
- [弹药编号失败](../../research/evidence/server3333-weapon-keys-red.log) → [2项通过](../../research/evidence/server3333-weapon-keys-green.log)。
- [递归注册失败](../../research/evidence/server3333-recursive-weapons-red.log) → [通过](../../research/evidence/server3333-recursive-weapons-green.log)。包含共享容量冲突及多层备用武器的复制时机。
- [玻璃源失败](../../research/evidence/server3333-glass-source-red.log)；缺失记录、截断、数量不一致、超上限和头部内的错误位置均拒绝，失败不改输出。
- 全量119项运行中118项通过，唯一失败是集成用例把五包子集误写成完整启动的武器数量。按实测修正为297后，[5项资源回归通过，21.884秒](../../research/evidence/server3333-map-registry-assets-final.log)。完整启动是315个命名条目加隐式none；子集与完整启动的数量不能混用。

下一步是将当前武器结构字段映射到已有原生引擎，再推进实际地图初始化、回环连接、移动与射击。原版剧情任务脚本仍后置。


## 武器副本与当前状态机（第六批）

旧服用于配件合成的武器副本已适配423来源：10个模型、168个动画、35个特效、18个视觉依赖以及72项容量的尾部依赖。隐藏标签、资源引用、声音数组和精度曲线指针不能被当作标量覆盖；曲线可以缩短，不能越过原始数组增长。新版动画不得通过旧144项接口截断。配件运算规则与原生WeaponDef转换仍单独适配，本批没有解除它们的版本门禁。

[失败用例](../../research/evidence/server3333-weapon-image-red.log)定位到旧版本门禁；[边界测试通过](../../research/evidence/server3333-weapon-image-green.log)，并由四种真实武器的[资源集成测试通过](../../research/evidence/server3333-weapon-image-assets.log)，耗时分别5.586秒与6.834秒。没有新增游戏内验收结论。

进一步静态对照：参考包与当前`common_mp`共有154种同名武器。分别用原始/移植C读取器解析头部和动画名称，作为结构差异线索；相同值不自动等于相同字段。REA已经定位当前开火`0x4253e0`、换弹`0x4230a0/0x4232d0`、抬枪`0x423b10`、冲刺`0x4283c0/0x428490`等消费者，供后续字段转换核验。原始来源、字段候选和消费者证据保存在`research/experiments/story-native/reference-zone-assets/`及`research/evidence/client-weapon-pmove-consumers423.json`。

## 最小装备与流式模型（第七批）

用户将主线收紧到默认装备完成首关初始化、当前客户端连接出生、移动与射击。当前采用 `defaultweapon_mp`（真实来源含2个模型、20项非空动画、10发弹匣）；旧合作脚本列出的 `m16_basic` 在13个实际启动包中不存在。原版剧情与复杂装备后置。

423武器的开火、换弹、抬枪、冲刺、弹药和伤害参数转换已接入保留引擎。动画保留3组56项并映射原生槽位；新版前置模型已无独立手臂槽，不能按旧11槽解释。俯卧限制由当前 `0x418ec0` 确认为 `+0xd88`，`+0xd87` 属于换弹分支。未实现的中间伤害曲线明确拒绝，不压平为两段。参数边界用例覆盖溢出、布尔值、NaN、截断和失败不改输出；开火时序还执行当前客户端 `0x4253e0` 核对。

`python games/codol/versions/v3_3_3_3/reverse/tools/prepare_native_models.py` 从原IFS的隔离副本提取并解码模型，缓存文件和来源哈希。274个无冲突模型写入隔离 `startup-assets/main/models/`；10个同名异内容条目保留证据，未猜测补丁优先级。[模型清单](../../research/evidence/server3333-model-streams.json)。材质未找到曾是五包测试集合不完整，补齐真实13包后解决；没有因此放宽材质校验。

`none/defaultweapon_mp` 的真实依赖、早期/晚期失败回滚、缓存复用和退役后重建已通过，[运行时失败记录](../../research/evidence/server3333-minimal-runtime-red.log) → [通过记录](../../research/evidence/server3333-minimal-runtime-green.log)，1项11.038秒。默认武器之外的四种源数据保留测试仍在；不要求复杂装备构造全部通过才能推进出生。

隔离启动工具仅运行本项目编译的 `server3333.exe`，不是旧启动器或旧客户端。它复制参考合作回调并在私有目录改为默认单武器，补上最小货轮关卡入口，避免加载PVP的整套地图脚本。`codol_clientExe` 始终指向固定哈希的3.3.3.3客户端。真实启动已通过 `G_SetupWeaponDef`、首关脚本编译和1879个导航节点构建，随后因 `mp/playeranim.script:427` 的 `movetype prone` 定义缺失而结束，见[启动日志](../../research/evidence/server3333-startup-minimal-script.log)。导航节点的可恢复 `ERROR:` 文本不再被探针误当作进程致命错误；真实 `Server crashed:` 单独判定。

REA继续复用活动客户端会话；当前证据包为 `research/evidence/client423-rea-bundle.json`。会话结束时另存分析快照以复用查询记录；证据包本身不等于持久Ghidra数据库。尚未连接真实客户端、出生或完成用户操作验收。

本批集中回归122项通过，87.501秒，见[日志](../../research/evidence/server3333-minimal-stage-tests.log)。审查范围为本批参数转换、资源提取与启动工具；没有将下一处动画解析错误标为完成。
## 当前动画脚本装载（第八批）

REA `0x409040` 确认新版在一次定义初始化后先解析 `mp/playeranim_defines.script`，再解析 `mp/playeranim.script`。旧入口只加载主文件，因而无法解析 `prone` 别名。现按同一顺序构造独立文本副本，完成后释放；缺失定义和文本内嵌零字节仍拒绝，原始资源不变。

当前客户端 `0xce4a20` 的33项事件和 `0xce4c18` 的Perk条件表已逐项对照。新增事件追加到原有24项之后，`meleehold/meleecharge` 追加到原生条件值表，保留旧生产者的编号，尤其 `FIREWEAPON=2`。这些修改恢复脚本解析，不代表新增能力动作已经可用。普通移动与射击不需要按55/47项移动表长度整体重排；快照传递的是动画树节点与重播位。

两项集成回归通过，12.828秒：[失败记录](../../research/evidence/server3333-animation-tokens-red.log)、[通过记录](../../research/evidence/server3333-animation-tokens-green.log)。覆盖真实当前表的每个名称、大小写查询、未知名称、事件存储上下界及重置，以及定义和主文件的装载顺序。

新的[隔离启动](../../research/evidence/server3333-startup-anim-tokens.log)越过上述解析错误，随后因 `pb_team_jug_spawn_kingpin` 名称查找失败而停止：13个缺失的特殊动画被旧服共用同一个 `void` 对象，未保留请求名称。下一步检查缺省动画身份与建树编号；当前仍未完成地图初始化或客户端出生。

## 最简首关初始化通过（第九批）

当前客户端 `0x406a90` 从叶节点动画资源读取名称，随后再次解析玩家动画脚本；旧服 `DB_CreateDefaultEntry` 的正常契约也会保留请求名称。CoDOL专用缺省分支却直接返回共享 `void`，导致所有缺失动作丢失身份。现为每个缺失名称缓存独立头部和名字，借用已验证的空动画载荷，并随其资源归档释放；原始 `void` 不变，损坏资源仍报错。13个特殊动作仍是空动画，不能宣称这些动作已恢复。

[失败用例](../../research/evidence/server3333-default-xanim-red.log)记录两次不同名称都返回 `void`、`distinct=0`；[修复后](../../research/evidence/server3333-default-xanim-green.log)验证独立名称、同名复用、不同名隔离及源载荷不变，1项7.488秒。涉及档案、控制器、协议与资源的集中回归 **125项通过，106.063秒**，见[日志](../../research/evidence/server3333-animation-stage-tests.log)。

[真实隔离启动](../../research/evidence/server3333-startup-named-xanim.log)首次完成最简首关初始化：`Calculate referenced files checksums...` 后资源注册CRC为 `9eaffd84`、种子为 `cdb31851`，`publication dry encode=1 bytes=353 actual_client_crc=1`，可靠配置审计无失败。探针随后按设计停止自身服务端，结果 `ready=true`；未启动旧版启动器或客户端。

这证明服务端地图初始化和资源发布检查通过。**大厅21/5仍未接入此实例，客户端连接、出生、移动与射击尚未验收。** 后续只推进真实就绪实例的预订/连接，不发布虚构候选，不扩大到原版剧情或复杂装备。

## 旧连接桥接的复用边界

对旧包的 `room_host2697.py`、`client_room2697.cpp` 和 `client_native_loopback.cpp` 仅作静态检查。其链路为DLL请求文件 → Python启服并回写ready → 本地包队列转发到回环28969；服务端设置 `codol_admissionRequired=0`、空安全密钥及 `codol_localChannel2697=1`。这不是原版房间预订和安全UDP已经恢复的证据，也不是新版必须采用的依赖。本阶段执行的是本项目重编的隔离服务端，没有执行旧启动器。

可复用同一 `seq + map` 的请求/ready校验及资源发布完成后才允许连接的时序。当前仍须验证：21/5候选被客户端读取 → 所选服务器身份匹配 `mmbook accepted` → `mmstart` → 地址和安全材料进入服务端准入 → challenge/connect、stats、gamestate。现有初始化探针要求准入但未配置客户端安全材料，不能只改端口就接入。

只有选用客户端桥接时才需要重新定位其钩子。旧send/receive地址 `0x5b1cf0/0x5b1c30` 尚未在当前版本验证；已知当前连接指针为 `*[0x1a2a538] ^ 0xd362501f`，旧地址和档案补丁不能照搬。证据见 [当前连接消费者](../../research/evidence/story-native-client-connection.json) 与 [剧情连接流程](../wiki/10-pve-story.md)。

## REA快照与索引恢复

本阶段在同一REA客户端会话中完成分析，收尾由 `close_binary` 保存 [分析快照](../../research/evidence/client423-native-stage.rea.json) 后关闭目标。保存结果为3039503字节、89项工作流缓存、180条证据，见 [保存记录](../../research/evidence/client423-native-stage-snapshot-save.json)。[证据包](../../research/evidence/client423-rea-bundle.json)另行保留；两者均为本地生成物，不进入Git。

恢复时使用相同客户端SHA-256（见本报告开头）、`ghidra`提供方和原分析配置。在项目根运行 `node tools/rea-session.mjs`，输入以下一行JSON：

```json
{"name":"open_binary","arguments":{"path":"E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe","provider_id":"ghidra","snapshot_path":"E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/evidence/client423-native-stage.rea.json"},"output":"client423-native-stage-restore.json"}
```

快照保存与后续恢复均已成功，恢复记录见 `research/evidence/client423-native-stage-restore.json`。恢复后读取服务器候选的新查询仍触发了Ghidra分析；快照提供已保存查询的缓存复用，不是持久Ghidra工程。目标、提供方或配置不符时应使用匹配快照，不能忽略身份校验。

主项目与客户端CodeGraph/GitNexus均已刷新。客户端索引含596份伪代码变体和4份随包代码，统计及重建命令见 [索引说明](../../research/client-code-index/README.md)。伪代码调用边仍有名称回退，不能代替机器码证据。

## 服务器候选与档案导出（第十批，连接准备）

当前客户端的 `MatchMakingInfo` 为0x228字节；REA `0x701db0 / 0xa55700` 确认候选读取顺序，`0xa55530` 确认地址区37字节。新增编码器仅生成回环候选数据，尚未接入大厅21/5。3项测试直接执行固定哈希客户端的实际读取器，核对完整消费、服务器身份、8字节安全ID、16字节密钥、地址和端口，并拒绝截断及非法连接材料。见 [REA证据](../../research/evidence/client-matchmaking-result423.json) 与 [通过记录](../../research/evidence/server3333-matchmaking-green.log)。通过读取不等于已预订或连接服务器。

`PrivateProfileStore.export_native` 从已校验的v19私有档案中导出原有zlib片段，写入隔离目录的 `mpdata_s.<十进制UID>`，不重压缩或修改源档案。5项Python测试覆盖字节保持、定点原子替换，以及非法UID、压缩长度、CRC、缺失档案时不改输出。实际原生读取验证受下述拦截阻塞，不能报告其通过。启动实例仍须准备匹配的安全ID、准入名册、私有档案，并核对当前客户端的预订、安全握手和公开stats流程。

### 2026-10-15 原生档案探针被拦截

用户截图显示火绒在北京时间12:27:35及12:28:33报告 `Trojan/Agent.cuhk!crit`。选中记录的路径为 `C:\Users\john\AppData\Local\Temp\codol-profile-native-5gc23n60\story_profile.exe`，操作进程为MinGW的 `ld.exe`、父进程为 `collect2.exe`。对应本项目 [测试构建入口](../../games/codol/versions/v3_3_3_3/tests/test_story_profile.py) 的两次TDD运行，探针源码为 [story_profile.c](../../games/codol/versions/v3_3_3_3/tests/native/story_profile.c)，链接现有档案读取器、资源解压代码和zlib；用途是读取测试档案并向标准输出写入32768字节。

两次均未成功执行探针：第一次停在缺失导出方法，第二次5项Python测试通过，但启动探针时报 `FileNotFoundError / WinError 2`。日志归档为 `research/evidence/server3333-profile-export-red.log`、`server3333-profile-export-native-blocked.log`。已暂停该测试类的自动构建；解除拦截原因前不得把跳过项算作通过，或自动重建、恢复、改名绕过检测。没有修改杀毒设置、添加白名单或上传样本。

本次只能确认构建来源，尚未判定为误报。两个已有服务端副本仍存在，SHA-256均为 `3dc6d05c39b036dffcdb69759b4463bb4acdd14a02d52a2d51109e9a649bf43f`，与构建清单一致。后续可继续独立的协议分析和Python测试；客户端出生、移动与射击仍未验收。

用户随后自行将两个样本恢复至桌面。只读核对得到：`story_profile.exe` 为130384字节，SHA-256 `e66a5b94a48d1d4eaa0db15d5c2b29a977e4fc17f7a1b82a01dcb2fa11b52ea7`，PE时间12:28:33；`story_profile2.exe` 同大小，SHA-256 `afbe4438ba9e3384167d8f944356d303ddc22b76ba2919ad2a5546a4499d064f`，PE时间12:27:33。全文件仅偏移136、216、217三字节不同，分别属于编译时间和PE校验和；代码、数据及符号表完全相同。两文件均有有效PE校验和，尾部为完整COFF符号/字符串表。详见 `research/evidence/story-profile-restored-static.json`。

REA静态核对恢复样本的 `_main @ 0x40148e` 与 `CODOL_ReadSecureProfile @ 0x40184a`，行为与探针源码一致：读取所选UID档案，成功后向标准输出写入32768字节。仅导入KERNEL32及MSVCRT；已检查路径未发现新增可疑行为，倾向误报，尚无杀毒厂商复核结论。未运行恢复样本；REA快照为 `research/evidence/story-profile-restored.rea.json`，分析记录为 `story-profile-restored-main-rea.json` 与 `story-profile-restored-reader-rea.json`。快照文件已落盘，随后REA清理自身临时导入副本时遇到访问拒绝；未强制清理或修改保护设置。

暂停原生探针后的集中接口回归为 **13项通过、1项明确跳过，0.312秒**，见 `research/evidence/server3333-connection-preparation-tests.log`。跳过发生在测试类初始化前，不再自动生成EXE；这不替代原生消费验证。
