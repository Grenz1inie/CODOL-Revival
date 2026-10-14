# 08 玩家等级、余额与商城

本章接续[公开档案及新手引导](06-onboarding-profile.md)，记录进入大厅后的玩家数据恢复。界面显示商品、余额变更、购买成功、仓库所有权是不同验收点。

## 当前状态（2026-10-14）

- 13:55：通过 Web 控制器启动，真实客户端进入大厅，显示 johnClient、马库斯、1 级、游戏币 0。
- 用户手动进入商城、仓库，反馈“出现商品或已有物品”。这是用户观察，尚未通过购买、余额变化或物品重载证明所有权接口可用。
- 同连接 `127.0.0.1:57444` 出现 `80/70`、`80/107`、`80/230`、`80/173`、`80/174`。此前服务返回空结果。
- 15:00：控制器写入私有档案和余额，重启服务及游戏后，大厅实测显示 **3 转生、70 级、游戏币 100000**。15:03 退出再进仍保持；连接 `127.0.0.1:65291`，事件见 [重登记录](../../runtime/captures/progression-currency-relogin-events.jsonl)。
- 15:08：用户购买后反馈余额未减少、购买无反应；随后补充连 3 级商品仍未解锁。捕获 `80/154`（SKU 3386、937），目前未实现扣款与发货。等级显示、解锁条件、仓库所有权须分别恢复。
- 15:44：修复后用户确认等级限制解除、扣款且入库。服务记录 SKU 2687（`m14ebr_mp`，物品 10057），扣除 55555，余额从 100000 变为 44445，永久物品一件。15:46 重登后用户再次确认枪仍在、余额 44445。见 [购买事件](../../runtime/captures/marketplace-purchase-events.jsonl)、[重登事件](../../runtime/captures/marketplace-relogin-events.jsonl)。界面结果来自用户反馈，不冒充已保存截图。

## 等级与转生：定义、数据、扩展字段

目标客户端 SHA256：`e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。

REA 静态证据：

| 函数 | 事实 | 证据 |
|---|---|---|
| `0x00590720` | 从玩家资料读等级，再减 1，负值归零；界面等级不能直接照内部索引写入 | [等级读取](../../research/evidence/controller-stat-lookup.json) |
| `0x00590550` | 联合 `experience`、`prestige`、`rankVersion` 及两份 CSV 计算经验值 | 同上 |
| `0x00592870` | 按参数选择 `mp/playerdata.def` 或 `mp/playersecuredata.def`，解析字段路径 | [档案上下文](../../research/evidence/controller-profile-context.json) |
| `0x00630750` | 按定义遍历字段，标志 `0x20` 的叶字段进入扩展列表；偏移从定义表读取 | [扩展字段遍历](../../research/evidence/controller-stat-lookup.json) |
| `0x0049e370` / `0x0049e170` | 通过类型、名称哈希和链表查找加载的资源 | [资源查询](../../research/evidence/controller-stat-lookup.json)、[哈希](../../research/evidence/controller-stat-context.json) |

公开档案解压后仍读取扩展字段，单改压缩区可能被覆盖。还需区分公开资料和私有资料；不能把公开存档内一个类似数值的位置直接命名为等级。

用户授权管理员只读提取后，已取得[实际字段定义与等级表](../../research/evidence/live-player-schema.json)。普通权限读取曾报 Windows 错误 5；第一次管理员提取因忽略 ASLR 报 299。修复为主模块基址加 RVA，本次基址 `0x410000`；资源名称比较按大小写不敏感处理。入口为 [Read-PlayerSchema.ps1](../../scripts/Read-PlayerSchema.ps1)，仅申请查询和读取权限。

`mp/playersecuredata.def` 为版本 19、定义哈希 2318499177。下表偏移从 DDL 数据起算，实际解压档案还需加 4 字节 CRC 前缀。

| 字段 | 偏移 | 本次写值 |
|---|---:|---:|
| experience | 4840 | 0（当前等级内经验） |
| prestige | 4879 | 3 |
| rank | 4883 | 70 |
| rankVersion | 4887 | 4 |

等级表最高索引 69、最高转生 3；本版本没有第 4 转生定义。私有档案有 36 个扩展字段，其中 kills/wins 为 float32，其余 int32；写入同步压缩区、扩展字段及 CRC。`8/2` 返回当前私有档案，`8/6` 接收带账号 ID 的保存数据。实现见 [dw_progression.py](../../src/dw_progression.py)，证据见 [任务分派](../../research/evidence/controller-profile-service-tasks.json)、[默认初始化](../../research/evidence/controller-private-profile-defaults.json)。修改前备份至 `runtime/backups/private-profiles/`，不覆盖公开角色资料。

### 商城等级限制的独立条件

REA `0x693160` 构造 SKU 的 `requirementLevel`、`requirementPrestige`、`purchasable`。它经 `0x4a4b10` 从 `mp/unlockFlags.csv` 获取索引，再由 `0x4a4ca0` 比较私有档案 `unlockFlagsNew[index]` 与商品阈值。`0x4a4c10` 将 `uf_prestige_rank` 阈值按除以 100、模 100 解释。因此只写 `rank/prestige` 不会自动补齐此解锁值。见 [商城条件调用链](../../research/evidence/controller-market-unlock-consumers.json)、[阈值解释](../../research/evidence/controller-market-requirements.json)。

用户另行授权管理员只读商城数据后，[实际商城资源](../../research/evidence/live-marketplace.json)确认 `uf_prestige_rank` 对应索引 1，私有 DDL 偏移 8293，含 CRC 前缀后为 8297。现在设置等级同步写入 `prestige * 100 + level`，本次为 370。新增断言先失败（原值 0），修复后通过。真实客户端已解除此前连 3 级商品都受限的问题；其他活动权益不等同于等级条件。

## 货币：按真实请求还原

REA 已确认 `0x00a472b0` 发起服务 `0x50`、任务 `0xe6`，即实际捕获的 `80/230`，带 context 字符串，最多绑定一个返回对象。[任务证据](../../research/evidence/controller-task230.json)

另一路 `0x004a4930` 同时调用 `80/130` 与 `93/1`；它们不能代替实际 `80/230` 的结构。公开 IW7 协议代码只用于对照，不直接搬用其任务号。[旧入口](../../research/evidence/controller-currency-protocol.json)

### 已还原的返回对象

`0x004a5120` 将 `80/230` 的结果绑定到 `0x07bdc6f8`。初始化器调用 `0x00a4a5b0`，虚表首函数是 `0x00a4a6b0`；后者反序列化的是复合资产对象。

| 顺序 | 线上字段 | 依据 |
|---|---|---|
| 1 | typed uint64 玩家 ID，typed string 账号类型 | `0x00a45950` |
| 2 | typed uint32 余额数量 | `0x00a4a6b0` |
| 3 | 每条余额：typed uint8 货币 ID，typed uint32 数量 | `0x00a64ad0`；子对象从父对象继承玩家信息，不重复写 ID |
| 4 | typed uint32 物品数量，随后逐个物品 | `0x00a4a6b0` / `0x00a4b850`，本次返回零个 |
| 5 | typed uint32 权益数量，随后权益条目 | `0x00a4bd80`，本次返回零个 |

`0x004a5680` 将第一条余额的 ID/数量复制给大厅显示使用的余额对象。`0x004a5a20` 的开发命令以 `cp` 对应 ID 1、`cc` 对应 ID 2；本次只实现 ID 1，实测对应大厅游戏币显示，并已用于真实购买扣款。

进一步追踪 Scaleform 注册表：`GetCP` 绑定的 `0x006af9e0` 在两个余额槽中寻找货币 ID 1，取数量返回界面。[GetCP 消费函数](../../research/evidence/controller-ui-balances.json)已连接协议到 UI；15:00 和 15:03 的真实客户端显示补足运行验收。

每五分钟还捕获到 `80/130`，参数 `080100000000`。其返回对象由 `0x00a4c4a0` 读取 typed uint8 + typed uint32。因此两个任务都从同一个持久化余额读取，避免初次显示与刷新后不一致。`93/1` 点数分支保持原有行为。

证据：[资产任务调用方](../../research/evidence/controller-task230-result.json)、[构造函数](../../research/evidence/controller-assets-constructor.json)、[虚表](../../research/evidence/controller-assets-vtables.json)、[资产反序列化](../../research/evidence/controller-assets-deserialize.json)、[子对象读取](../../research/evidence/controller-assets-read-fields.json)、[货币指令](../../research/evidence/controller-currency-instructions.json)、[权益指令](../../research/evidence/controller-entitlement-instructions.json)、[CP/CC 名称字节](../../research/evidence/controller-currency-names.json)、[简单余额读取](../../research/evidence/controller-simple-currency-fields.json)。Ghidra 在权益函数中误判了一段不可达分支，已用完整汇编确认数量及后续循环；不单凭伪代码作协议结论。

### 实现与回滚

代码见 [dw_marketplace.py](../../src/dw_marketplace.py)。余额保存在 `runtime/data/marketplace/<用户ID>.json`；每次覆盖前将原 JSON 保存至 `runtime/backups/marketplace/`。只接受正整数增加量，当前界面采用有符号 32 位上限 `2147483647`；线上字段本身为 uint32。公开档案二进制不随货币操作改写。

控制器仅允许为已有且校验通过的档案增加余额，并要求游戏已退出。恢复余额时先退出游戏，复制对应备份覆盖单个账号 JSON，再重启读取。服务端当前仅支持本机单账号，沿用首次 `8/1` 查询绑定的玩家 ID。

测试覆盖余额累计、上限及越界拒绝、备份内容、重载、HTTP 非法账号/非法值/运行中拒绝，以及加密会话中两种任务的完整返回字节。测试期望来自上述 REA 结构的独立小样例，未从编码函数反算。

截至商城购买接入，本轮集中验证 36 项测试通过；前端源码未变，沿用此前 TypeScript 检查、Vite 构建和浏览器主题/窄屏/Wiki 验证。服务 PID 52432 采用购买协议；游戏 PID 6488、连接 `127.0.0.1:53917` 完成首次购买，随后 PID 15592、连接 `127.0.0.1:51466` 重登读取。旧进程强制退出产生的连接重置记录不算新连接协议失败。

## 购买、仓库刷新和重登

### 静态目录来源

`Read-PlayerSchema.ps1 -Marketplace` 读取两份 CSV 及已加载的商品、SKU、物品和解锁条件表，仅使用查询/读取进程权限。`tools/export-marketplace.py` 按 `0x5840a0` 的地址异或与循环位移还原值，按 `0x7070b0` 解释价格/期限，按 `0x706f10` 获取商品中的物品与数量，生成 [商城目录](../../data/marketplace-catalog.json)。目录记录 EXE 与捕获源 SHA256，包含 12316 个启用 SKU。服务不需要再读取游戏内存。

SKU 3386 是物品 789、5000 游戏币、永久；SKU 937 是相同物品、950 游戏币、30 天，用作独立测试样例。实际人工购买的是 SKU 2687、M14 EBR。不同 SKU 可指向同一物品，不能用 SKU 直接充当物品 ID。

### 线上调用链

| 阶段 | 请求与响应 | 证据 |
|---|---|---|
| 购买 | `80/154`，已验证单 SKU、数量 1、默认收件人；成功无结果对象 | [请求构造](../../research/evidence/controller-purchase-wire-instructions.json)、[参数序列化](../../research/evidence/controller-purchase-params.json) |
| 仓库刷新 | `80/203`，context 空字符串、上限 20000；每件物品带账号信息 | [任务与回调](../../research/evidence/controller-inventory-task203.json) |
| 初次登录 | `80/230` 资产对象内写入余额和物品，子物品继承账号 | [资产到仓库](../../research/evidence/controller-assets-to-inventory.json) |
| 余额刷新 | `80/130` 读取同一余额文件 | [简单余额结构](../../research/evidence/controller-simple-currency-fields.json) |

物品读取函数 `0xa4b850` 依次读取三个 uint32、blob、uint32、int64、uint16、uint32、uint8。字段首项为物品 ID，第二项数量，`+0x80` 是到期时间；其余目前保留 `0xa4b4e0` 默认值。永久到期值 `0xffffffff`，有限期限按目录天数换算。见 [类型标签](../../research/evidence/controller-inventory-wire-types.json)、[默认值与拷贝](../../research/evidence/controller-inventory-consumers.json)、[仓库使用方](../../research/evidence/controller-inventory-catalog-links.json)。

### 原子性、失败与边界

同一账号 JSON 同时保存余额与库存，先验证商品/解锁/余额，再备份并原子替换；增加游戏币保留已有库存。余额不足返回 `0x1f47`、未知商品 `0x1f41`，其他不支持的购买返回 `0x1f43`。客户端错误分支见 [购买反馈](../../research/evidence/controller-purchase-entrypoints.json)。失败不扣款，返回错误而非成功空对象。

本阶段已支持：单件游戏币商品、永久或按天计期物品、购买后刷新及重登读取。36 项测试包括真实请求字节、加密响应、重复拒绝、非法请求、余额不足、等级条件、期限、备份和重载。后续点券、控制器全物品发放和手动续期见 [09](09-inventory-completion.md)；批量/赠送、重复叠加及活动权益仍未实现。重复拥有时拒绝扣款。

## 验收边界

1. 数据接口：合法边界、非法值不改原数据、备份、校验和、重新读取。
2. HTTP：操作结果与持久化状态一致；游戏运行时避免旧档案覆盖新修改。
3. 游戏：重新登录显示目标等级/余额；退出再进仍保持；商城解锁另以具体物品验证。

训练、匹配和对局服务的状态仍见 [07](07-session-game-server.md)。
