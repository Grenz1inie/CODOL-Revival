# 关键链路与使用边界

以下连接用于导航，结合当前目标哈希的 REA 伪代码、原项目 Wiki 和保留的汇编证据整理。异步回调和虚表连接不是普通直接调用；没有把它们伪装成完整调用图。

后续补全见 [关键调用链](CALL_CHAINS.md) 和 [机器调用位置索引](call-chains.json)。其中补充了指定账号档案 `8/7` 查询、`8/8` 保存、任务提交及回调调度、背包消费、点券任务分支和装备缓存到 DDL 字段的写入；下文保留首批导出的背景与边界。

## 账号和大厅

- `0x00a598b0` 解析认证响应与票据，`0x00a678c0` 读取票据结构。明文票据路径及 magic 检查以代码为准；加密票据密钥推导仍未完整还原。
- `0x00641e10` 读取 dwauth/STUN 配置；`0x00a61980` 处理大厅协议 210 的握手 transcript 和密钥派生。这里没有完整导出 TCP 帧解密、任务分发和全部 STUN 状态机。
- 公开档案查询入口 `0x00a5a890` 构造服务 8 / 任务 1，保存入口 `0x00a5a420` 为 8/3；私有档案查询 `0x00a5a9d0` 为 8/2，私有保存 `0x00a5a530` 为 8/6。本次定向反编译和 [SDK 指令](evidence/focused/profile-sdk-disassembly.txt) 均观察到公开保存处传入 `8,3`。
- 档案消费链从 `0x006d7740` 关联基类读取 `0x00a5a370`、解压 `0x006d7430` 与 CRC 路径 `0x006d7d80`。序列化入口 `0x006d7500` 还输出 DDL 扩展字段；不能只修改或返回压缩体。
- `0x005c3670`、`0x005c36f0` 是进入大厅前的两个引导完成判断；其存在不代表整个引导或对局流程已经恢复。

导航：[认证](codol/client/account/auth/README.md)、[档案](codol/client/account/profile/README.md)、[大厅连接](codol/client/lobby/connection/README.md)、[引导](codol/client/lobby/onboarding/README.md)。

## 背包、余额和购买

| 路径 | 入口与消费点 | 重点 |
|---|---|---|
| 首次资产获取 | 请求 `0x004a5120` → `0x00a472b0`；对象读取 `0x00a4a6b0`；完成回调 `0x004a5680` | 80/230 为复合资产；三段不是连续直接调用；子对象可继承账号信息 |
| 仓库刷新 | `0x004a6b10` → `0x00a468c0` → 回调 `0x004a6c10` | 80/203；条目读取消费 `0x00a4b850` |
| 游戏币 / 点券 | `0x004a4930` 分别调用 `0x00a461d0` / `0x00a4bfc0` | 分别为 80/130、93/1；不能只增加登录资产里的余额条目 |
| 大厅余额显示 | `0x006af9e0` / `0x006af970` | 分别为 GetCP、GetCC 回调 |
| 购买 | 游戏币 `0x00a467e0` → 参数 `0x00a45b40`；点券 `0x00a4c220` → `0x00a4c0b0` → 参数 `0x00a64ca0`；完成回调 `0x004a6940` | 游戏币 80/154；点券按账号对象比较结果选择 93/4 或 93/131，详见补全说明 |
| 商品可购买判断 | `0x00693160`、`0x004a4b10`、`0x004a4ca0`、`0x004a4c10` | 目录条件、私有档案解锁值、转生和等级阈值各自有消费者 |

物品读取 `0x00a4b850` 的主要顺序为三个 uint32（ID、数量、经验）、blob、uint32 到期值、int64 使用限制、uint16 冲突 ID、uint32 修改时间、uint8 来源。完整参数和是否读取所有者仍需结合调用上下文；构造函数 `0x00a4b4e0` 保存默认值依据。

`0x00a4bd80` 的 Ghidra 输出含多条 `Removing unreachable block`，不能把被消除的分支视为原程序没有逻辑。已原样复制 [权益读取汇编](evidence/support/controller-entitlement-instructions.json)、[物品读取汇编](evidence/support/controller-inventory-instructions.json)、[虚表依据](evidence/support/controller-assets-vtables.json)。

另一个具体类型恢复问题：`0x00a4b850` 被输出为 `void`，但 `0x00a4a6b0` 的调用点把其结果当作成功标志使用。导出保留这两个原始结果；重新实现接口时应核对汇编和寄存器约定，不能照抄 `void` 签名。

导航：[资产](codol/client/inventory/assets/README.md)、[物品](codol/client/inventory/items/README.md)、[余额](codol/client/inventory/currency/README.md)、[购买](codol/client/inventory/purchase/README.md)、[目录](codol/client/inventory/catalog/README.md)。

## 装备和武器成长

`WL_GetWeaponRank` 回调 `0x006b7190` 从 `0x00695bc0` / `0x00695a80` 取得库存经验，再调用 `0x0046eb20`，界面值为 rank + 1。`0x0046ee30` 查询最大 rank；描述符 byte+6 与主副武器等级表选择有关。

`WL_EquipWeaponAttachment` 入口为 `0x006b43c0`。函数在特定参数分支遍历六个槽位、比较描述符 byte+6、清除同类型的其他槽位，再写入目标槽位；另一分支调用 `0x006c2090`，其中还包括拥有状态检查和实际配置写入。该写入函数同样存在六槽位的同类型替换循环。不要把编辑缓存分支当作完整持久化流程。

本次以 PE 原始字符串、注册函数及虚表共同确认以下绑定，字节记录在 [equipment-bindings.json](evidence/focused/equipment-bindings.json)，注册函数的反编译和完整指令在 [loadout.json](evidence/focused/loadout.json)。这是独立 Ghidra 和离线字节证据，不是本次 REA 默认分析的新结果。

| 界面名称 | 注册函数 | 虚表 | 回调（虚表 +4） |
|---|---|---|---|
| WL_EquipWeapon | 0x006b7740 | 0x00c7bc4c | 0x006b4230 |
| WL_EquipWeaponInSlot | 0x006b78a0 | 0x00c7bc64 | 0x006b4350 |
| WL_EquipWeaponAttachment | 0x006b7950 | 0x00c7bc70 | 0x006b43c0 |

普通武器和指定槽位入口关联 `0x006c1e70` 写入路径及 `0x006bf130` 槽位上下文辅助。配件所有权、描述符类型、槽位、武器等级和商城条件仍是不同层次；未做运行时装备或持久化验收。

缓存读取 `0x005945b0`、写入 `0x005946c0`、脏缓存校验和回写 `0x005948f0`、字段路径构造 `0x00592b10`、DDL 写入包装 `0x005926d0` 已补入独立包。具体字段及脏标志含义见 [关键调用链](CALL_CHAINS.md)，仍未验证保存任务的在线完成和重登恢复。

导航：[武器成长](codol/client/equipment/progression/README.md)、[配件装备](codol/client/equipment/attachments/README.md)、[武器装备](codol/client/equipment/loadout/README.md)、[缓存与档案写入](codol/client/equipment/persistence/README.md)。

## 明确保留的未知项

- 原始类型、变量名、函数签名及所有间接调用尚未完全恢复。
- 多账号绑定、在线认证兼容、全部权益语义和完整大厅状态机不在本批导出覆盖范围内。
- 反编译中的寄存器输入和 `WARNING` 需要继续结合汇编判断；导出成功不是协议或运行行为验证。
- 本批功能名称与包边界是维护约定，不能作为原厂架构证据。
