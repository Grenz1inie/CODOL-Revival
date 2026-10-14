# codol_dedrun 与 3.3.3.3 原生对局兼容性

目标：剧情页开始战斗后，加载所选地图并使玩家可操作。本文记录协议证据及已授权的隔离实验；参考引擎实验副本已完成信息查询和离线归档探针，原游戏未修改。实际开图仍未通过，最新资源链见[首关资源消费者](20261014-story-resource-chain.md)。

用户最新纠正：旧启动器应以静态参考为主。对照源码用于解释资源/协议消费者，不把直接运行或重编译2697启动器作为新版方案。正式启动入口的隔离探测已定位版本门禁及公共包第506项的图片别名问题；此后优先回到423资源及3.3.3.3协议契约的离线验证，未发布对局候选，也未启动实验客户端。

## 固定对象

- 参考引擎：`research/references/codol2697/codol_dedrun.exe.bin`，SHA256 `1736926655100b53499ae75ea5bddd0741983c12c89cdb51d49aef8a0be03243`。
- 3.3.3.3 客户端：`codoMP_client_shipRetail.exe`，SHA256 `e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。
- 以下地址均为首选镜像基址 0x400000 下的静态 VA；运行时须按实际模块基址重定位。
- 用户补充的 `native-source.zip`：SHA256 `152755e1ee460b8cbb1bf5c6e0069dd7a13541bf9a4a2e65b5a11ebf36fa5978`。2772个文件已提取到隔离实验目录 `reference-source/`；其中包含引擎C/C++、汇编、构建目标和测试。`CODOL_LoadStartupArchives`、`mount_archives`、`CODOL_LoadMapArchivesEx`已与当前参考二进制的REA反编译逐段对照；源码只作参考，整包重建不是当前目标。来源及逐文件哈希见 `research/evidence/reference-native-source.json`。
- 首关表项为 `coop_training_mp_cargoship`，地图分类和玩法均为 `coop`。来自已有 `live-pve-tables.json`，不能用 PvP `mp_cargoship/war` 替代验收。

## 从开始战斗到可操作关卡

1. 大厅查询与预订：现有 21/5 → mmbook → mmbook accepted → mmstart 链；必须由实际就绪的对局实例提供候选。
2. 客户端连接：3.3.3.3 `0x466790` 消费 challenge/connectResponse 等无连接消息；连接对象取自 `DAT_01a2a538 XOR 0xd362501f`。参考桥接使用的2.6.9.7地址、异或值不能沿用。
3. 初始世界：3.3.3.3 `0x46dea0` 读取 gamestate，核对 netconst 校验值；不一致产生 `EXE_CONFIGSTRINGMISMATCH`。通过后调用 `0x465a30` 进入资源/客户端世界初始化。
4. 持续世界与输入：参考引擎有 `SV_WriteSnapshotToClient`、`SV_UserMove` 及2697专用玩家/实体转换；是否符合3.3.3.3仍待逐字段核对。函数存在不证明该剧情可玩。
5. 剧情资源：地图几何、碰撞、脚本和AI必须就绪。客户端加载画面不能代替移动、射击及任务流程验收。

## 已确认差异

| 契约 | 参考引擎 | 3.3.3.3 消费者 | 适配影响 |
| --- | --- | --- | --- |
| 配置字符串别名组数量 | `0x4a084d` 写11位；上限2047 | `0x46dc25` 按10位读 | 原样发送会使后续位流错位；需要10位与1023上限同时处理 |
| 配置字符串索引 | `0x4a0468` 允许0..0x1dd6 | `0x46db20` 允许0..0x1b91 | 资源索引必须重新映射；只改一个计数位宽不足以兼容 |
| 客户端编号 | `0x4a21b8` 接受0..31 | `0x46dea0` 接受0..18 | 本地单人取0可落在交集，不表示多人协议已恢复 |
| 客户端注册表 | `0x4a3dab` 缺有效表就停止发送gamestate | `0x5850b0` 汇总已加载 ncs 资源并校验 | 需要实际3.3.3.3注册顺序与校验值，不能伪造通过 |
| 资源载入 | `0x54d8b3` 接受FF版本334/365；2697正式挂载只允许365 | IFS内部签名FF为0x1A7，即423 | 独立副本已完成首关依赖的归档重放与基础世界转换；正式开图入口仍待适配 |
| 玩家状态布局 | `0x4a2840` 固定229字段，每描述6字节；实体62字段×22表 | 235字段，每描述12字节；已读取字段表 | 不复制2697偏移；资源匹配也不能证明snapshot兼容 |
| NCS分类 | 旧表没有新版17类sts，运行时codinfo占17 | 21类；sts为17，codinfo/codinfovalue/network为18/19/20 | 不能沿用旧资源bank或只移动数组下标，须同时核对消费者 |
| 本地化排序前缀 | 参考资源构建传入`chinese` | 当前中文索引11对应`chi`，排序检查名称+8 | 按实际语言表还原，不能照抄参考字符串 |

位宽差异已经由 REA 汇编确认，而非仅凭伪代码：

- 服务端 `0x4a084d`：`MOV dword ptr [ESP+8],0xb`，随后调用写位函数。
- 客户端 `0x46dc25`：`PUSH 0xa`，随后调用 `0x5a13a0`。
- 服务端原字节 `c7 44 24 08 0b 00 00 00`，文件偏移 `0x9fc4d`；计数限制 `0x4a04b4` 原字节 `81 7d 1c ff 07 00 00`，文件偏移 `0x9f8b4`。已生成并测试独立配置字符串实验副本；未接入正式启动，也不是完整兼容补丁。

## 隔离实验范围（已获用户授权）

实验放在 `research/experiments/story-native/`，独立日志/配置/临时存档。原游戏、本地账号档案、原始参考文件保持不变。

已在隔离副本执行固定哈希参考引擎的 `--codol-2697-info`：`_Sys_Main` 的静态分支只输出元数据后返回，未进入平台/引擎初始化。该输出自带“未完成”文字，可能是旧状态说明，不作为当前可玩性的结论。

随后在实验副本中适配已经核对的协议和资源布局；需要客户端桥接时，只对实验客户端装载本项目桥接。逐项校验目标哈希与原字节，记录前后哈希与差异；不移植参考的系统WFP规则、不改变hosts/证书/防火墙、不操作正式客户端进程。实际启动前再次核对具体入口与参数，只使用回环端点。

测试顺序：错误哈希/原字节拒绝 → 有效副本仅变更指定位置 → 资源/注册表匹配 → gamestate → 首帧snapshot → 移动/射击 → 剧情任务与返回大厅。地图未就绪不发布候选；任何前置失败就保存原因，不伪造成功。涉及新的输入输出接口时先确定测试边界再按TDD实现。

当前进展：19个IFS包已提取、23个FF已验签解码。五包联合离线探针完成9173个静态模型实例、246个动态模型、8个特效、64个基础触发模型及首关142个附加触发模型转换；商城包图片共享引用也已通过回归。当前离线入口明确不启动引擎、网络或物理模拟。此前普通启动实验曾初始化回环网络，随后因资源失败退出；该入口及其四处版本门禁补丁现已撤回，不能笼统写成“从未初始化网络”。

新注册表实现已由3.3.3.3消费者核对；当前进程193个网络变量名对应种子`0xcdb31851`。十个候选依赖中的61张NCS得到候选CRC `0xc6280541`，但尚未与客户端加载首关后的资产集合比对，不能发布为已就绪服务器。正式开图、玩家/实体快照、输入和主任务逻辑仍未恢复。具体证据见[资源链报告](20261014-story-resource-chain.md)。

## 原始证据

- [服务端地图状态/输入/挂载](../../research/evidence/dedrun-gamestate-input-assets.json)
- [服务端注册表与玩家转换](../../research/evidence/dedrun-target-registration-layout.json)
- [服务端字段表与归档挂载](../../research/evidence/dedrun-netfields-archive-mount.json)
- [服务端FF解析](../../research/evidence/dedrun-zone-format.json)
- [服务端配置字符串与入口](../../research/evidence/dedrun-configstrings-and-info-command.json)
- [服务端位宽汇编](../../research/evidence/dedrun-configstrings-instructions.json)
- [客户端连接处理](../../research/evidence/story-native-client-connection.json)
- [客户端gamestate处理](../../research/evidence/story-native-client-gamestate-dispatch.json)
- [客户端配置字符串与注册](../../research/evidence/story-native-client-configstrings.json)
- [客户端位宽汇编](../../research/evidence/story-native-configstrings-instructions.json)


## 后续源码移植（2026-10-15）

用户现优先要求复用旧服通用能力。已从只读参考源码生成独立服务端，按当前客户端证据修改网络与输入模块，并编译成功。旧启动器仍以静态参考为主；源码构建是当前移植载体，不能据此声称旧版启动方案适用于新版。阶段验证及尚缺的实体、挂载与运行闭环见[对局移植记录](20261015-server-port.md)。
