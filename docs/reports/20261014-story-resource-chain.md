# 首关资源消费者与服务端适配

状态：已恢复并校验首关、基础地图及公共合作依赖的内部文件，隔离参考引擎可以打开 FF427；尚不能初始化完整世界、连接当前客户端或进入可操作关卡。游戏验收由用户执行，本轮未要求重复点击，也未重载正式服务。

## 1. 输入与范围

实验产物均在 `research/experiments/story-native/`，代码在 `tools/`，REA 证据在 `research/evidence/`。原游戏、正式存档与系统设置未修改。

- 客户端 SHA256：`e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。
- 参考引擎 SHA256：`1736926655100b53499ae75ea5bddd0741983c12c89cdb51d49aef8a0be03243`。
- IFS2.dll SHA256：`5b0324e0b2ba3545a6c02626287d4fbc6a3116594744f4647333982d85508421`。
- 仅首关 `coop_training_mp_cargoship/coop`、其基础地图 `mp_cargoship` 和 `common_mp/common_gametype_coop` 依赖。基础地图不是拿 PvP 代替剧情的验收目标。

## 2. IFS → FF → 资源目录

`ifs-read.c` 调用当前 IFS2.dll 解析副本，读取自身目录表和原始存储块。构造/销毁是 stdcall，虚表方法是 thiscall；销毁参数是接口指针的地址。目录项0x80字节，文件偏移为64位，名称指针在+0x38。未初始化的跨包文件ID表计数为0，不能据此认定IFS为空。

提取结果：首关7包325条记录、基础地图8包332条、公共依赖2包7条，共17包。首关清单318个去重路径全部找到；315个 loose payload 解码成功。重复补丁文件保留各自来源，尚未推断最终覆盖顺序。清单记录输入、副本、提取工具及输出哈希，原包/副本均未被DLL改写。

FF外层是 `IWff0100`、版本427；签名头 `IWffs100`。从当前客户端读取内嵌材料，验证签名、每张哈希表和每个数据块后解压。FF的AES CTR计数是小端，不能套用 loose 文件解码的大端计数。地图名按客户端规则截断为31字节。参考工具的 `ReadClientRegion` 使用 fseek 文件偏移，不能传VA。

目录头在zone偏移40；字符串后是16字节资源项（类型、相对40的偏移、指针、负载长度）。资源项既可能携带数据，也可能是零长度的共享引用；类型14/17/18在当前客户端被置空。共享引用不能当作“文件丢失”，也不能凭目录顺序构造最终运行时ID。

| zone | 解压字节 | 资源数 | 发现 |
| --- | ---: | ---: | --- |
| coop_training_mp_cargoship | 21583990 | 1174 | 12张NCS、附加实体、模型、特效、武器、9个rawfile |
| coop_training_mp_cargoship_const | 10488 | 2 | 首关实体基线 |
| mp_cargoship | 87492551 | 338 | 碰撞图、渲染世界、公共世界等基础资源 |
| common_mp | 110773546 | 9329 | 公共武器、动画、菜单和注册资源 |
| common_gametype_coop | 41560572 | 1612 | 合作玩法公共模型、武器与动画 |

另有6个加载图、本地化或基础地图常量zone，合计解码11个FF。完整计数和rawfile路径见 [资源清单](../../research/experiments/story-native/zone-assets/manifest.json)。公共/本地化NCS有5张含共享字符串引用，当前独立读取器明确标记 unresolved；最终注册ID、排序和CRC仍未恢复。

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

上述11个FF的rawfile中仅发现4份GSC，分别是剧情地图与基础地图的特效/创建特效脚本；公共MP及合作包中未发现主任务GSC。这是**已检查包的结论**，不是全盘不存在脚本的证明。实体标签给出触发对象和连接线索，但没有提供任务执行顺序、AI行为、目标判定和失败处理的全部实现。基础地图的AI路径目录项为空，也不能直接认定客户端具备完整服务端导航数据。

因此反推服务端应分层进行：先将当前资源转换成实际碰撞/出生状态，再完成注册表、实体/玩家delta和输入；最后按实体关系与更多脚本消费者证据重建任务逻辑。显示加载画面或让静态场景出现都不足以证明剧情恢复。

## 5. 参考引擎实验结果

`tools/story_engine_patch.py` 校验固定原始SHA和每处原字节。归档实验只修改5处指令：两个FF版本分支、材料文件偏移、NCS版本分支、技术表版本分支。签名、块哈希、资源长度校验保留。配置字符串10位补丁是另一份副本，未混合成默认对局引擎。

`--codol-archive-probe <FF路径> <客户端路径>` 在引擎网络初始化前返回。实际结果及输出哈希以 [探针清单](../../research/experiments/story-native/archive427-probes.json) 为准：

- 首关/基础地图常量包：完整资源重建通过。
- 首关主包：已越过12张NCS和第12号rawfile，停在第13号模型的长度检查。
- 基础地图：已越过18张NCS和前面的技术表，停在第33号特效资源。
- 两张加载图：仍停在第1号材质资源。

模型在 `_CODOL_ReplayZoneAsset → ReadXModelExtent → ReadXModelBounds → ReadXModelCollision` 中先做独立长度检查，之后才进入 `replay_model`。材质有两套消费者（预检查与重建），均须适配；当前客户端材质0x68字节、名称+0x10、三个计数+0x50/51/52，旧引擎为0x60字节及旧偏移。单改重建器不能通过前置检查；未通过的候选已归档为 `material-candidate-patches.json`，未纳入当前探针副本。

`ReplayZone` 遇到后续失败会释放上下文，随后 `ReadNetConst` 全部失败并不证明前面NCS重建失败。不能删掉长度检查来制造成功。旧GDB无法在随机基址上插入静态断点；另有仅调试副本清除DYNAMIC_BASE的记录，此更改没有应用到探针正式实验副本、客户端或系统。

## 6. 复现与下一步

在项目根目录，使用已安装Python、cryptography、pefile及x86 GCC：

```powershell
# 仅编译器进程所需PATH；不要改变系统PATH
$storyBuildPath = $env:Path
try {
  $env:Path='A:\Coding\MinGW\bin;C:\Windows\System32;C:\Windows'
  gcc -O2 -Wall -static-libgcc -o research/experiments/story-native/ifs-read.exe tools/ifs-read.c
} finally { $env:Path = $storyBuildPath }
python tools/extract_story_resources.py
python tools/extract_story_resources.py --base
python tools/extract_story_resources.py --common
python tools/inspect_story_resources.py
python tools/export_story_zone_assets.py
python tools/probe_story_archives.py
python -B -m unittest discover -s tests -v
```

提取命令拒绝覆盖已有目录；已提取时直接使用manifest，不删除历史证据重跑。`probe_story_archives.py` 本身完成不等于所有归档通过：逐项查看记录的引擎退出码，0通过、3资源重建失败。

后续顺序：同时适配材质预检查/重建与嵌套图片 → 特效及模型资源 → 基础世界碰撞转换 → 公共注册表/CRC → gamestate和首帧snapshot → 玩家输入 → 任务逻辑。到实际具备新的可测行为后，再由用户验证对应地图、移动、射击及剧情触发。

收尾验证：60项测试通过，308个文档本地链接无缺失；17个原IFS与提取前哈希一致，原客户端和原参考引擎SHA均未变化。见[验证记录](../../research/evidence/story-resource-final-verification.json)。项目与客户端CodeGraph已同步，GitNexus分别为48/310文件。索引文本不改变上述可玩性结论。
