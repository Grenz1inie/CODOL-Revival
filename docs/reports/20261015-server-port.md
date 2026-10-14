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

保留旧服的 C/C++、汇编引擎及消息、资源、玩家输入模块，在独立副本应用 [源码补丁](../../tools/native/server3333.patch)。没有另建 Python 对局引擎；`src/story_wire423.py` 是协议研究原型，仅由离线测试使用。

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
& A:/Coding/Python3.13.7/python.exe tools/build_native_server.py
& A:/Coding/Python3.13.7/python.exe -B -m unittest discover -s tests -v
```

构建工具逐个校验补丁涉及的参考文件 SHA-256，严格应用补丁到独立源码，再使用已有 MinGW.org GCC 6.3.0 x86、Git的sh/patch及便携NASM 3.02。NASM放在 `research/experiments/story-native/toolchain/nasm-3.02/`，不修改系统PATH；[官方压缩包](https://www.nasm.us/pub/nasm/releasebuilds/3.02/win64/nasm-3.02-win64.zip) SHA-256为 `161d0bfaff53c2f9e9f3e69fd0672323ebabafd1268976a5cec11be92a19aee7`。

旧源码编译需要 `-fpermissive` 接受既有的DWORD/LONG指针差异，并补充旧MinGW头文件缺失的 `AI_NUMERICSERV=8`。只用相同旧源码重编libtomcrypt中的一个CRT对象，解决工具链不一致；不修改原参考库。

产物为 `research/experiments/story-native/server3333/bin/codol_dedrun.exe`，[构建清单](../../research/experiments/story-native/native-build3333.json)记录源码包、补丁、EXE哈希和编译日志。它是未完成适配的实验构建，未接入控制器或正式大厅候选。

本阶段集中回归 **104项通过，40.827秒**，其中原生移植17项、Python协议研究17项。[测试日志](../../research/evidence/server3333-tests.log)。测试在临时目录从原始源码重建真实C模块；输入整包使用32位ABI程序，客户端侧用Unicorn执行固定哈希EXE中的原始读写函数。UI、时钟等边界调用被隔离，没有启动真实游戏、渲染或网络。

第二批原生适配 **23项通过，14.220秒**，[失败记录](../../research/evidence/server3333-publication-red.log)与[修复后记录](../../research/evidence/server3333-publication-green.log)保留。新增测试覆盖非空快照、对象类型切换、固定配置槽、静态/动态菜单边界、266项注册与损坏导出、死亡图标分区。这里仍是协议和语义接口验收，未执行用户的游戏操作。

## 下一段闭环

1. 保留新增能力值和组合状态的未验证标记；用真实地图对象核对已适配字段，不把合成快照等同于可玩地图。
2. 将已经离线验证的423资源消费者接入原生挂载入口，核对实际资源集合、注册种子和地图CRC。不能仅放宽365版本检查。
3. 完成回环握手、房间预订和真实地图启动后，才交给用户验收加载、移动、射击；原版剧情脚本继续单独跟踪。
