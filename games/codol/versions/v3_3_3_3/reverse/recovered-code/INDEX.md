# 关键功能索引

按功能查找入口，再沿地址读取伪代码和证据。业务名称为分析标签；地址与原始符号保留。

[使用说明](README.md) · [机器索引](function-index.json) · [维护方法](MAINTENANCE.md)

## 账号认证与票据

包：`codol.client.account.auth`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x00a598b0](codol/client/account/auth/FUN_00a598b0.c) | 认证响应与 client_ticket 解码入口 | REA 历史证据 |
| [0x00a678c0](codol/client/account/auth/FUN_00a678c0.c) | 128 字节认证票据字段读取 | REA 历史证据 |
| [0x00a595c0](codol/client/account/auth/FUN_00a595c0.c) | 当前版本票据校验回调 | REA 历史证据 |
| [0x00a36e40](codol/client/account/auth/FUN_00a36e40.c) | 认证票据文本解码包装 | Ghidra 定向分析 |
| [0x00a676f0](codol/client/account/auth/FUN_00a676f0.c) | 认证对象 24 字节字段双向掩码转换 | Ghidra 定向分析 |
| [0x00a678b0](codol/client/account/auth/FUN_00a678b0.c) | 认证会话字段双向掩码转换 | Ghidra 定向分析 |
| [0x00a36c10](codol/client/account/auth/FUN_00a36c10.c) | 认证票据 Base64 字符解码和长度边界 | Ghidra 定向分析 |

## 公开和私有档案的序列化、解压与任务入口

包：`codol.client.account.profile`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x006d9c10](codol/client/account/profile/FUN_006d9c10.c) | 公开和私有 dwProfile 对象初始化 | REA 历史证据 |
| [0x006d7740](codol/client/account/profile/FUN_006d7740.c) | 档案反序列化与 DDL 扩展字段读取 | REA 历史证据 |
| [0x00a5a370](codol/client/account/profile/FUN_00a5a370.c) | 档案基类字段读取 | REA 历史证据 |
| [0x006d7430](codol/client/account/profile/FUN_006d7430.c) | 档案解压与数据检查 | REA 历史证据 |
| [0x006d7d80](codol/client/account/profile/FUN_006d7d80.c) | 档案 CRC 计算路径 | REA 历史证据 |
| [0x006d7500](codol/client/account/profile/FUN_006d7500.c) | 档案序列化与扩展字段写入 | REA 历史证据 |
| [0x006d7b20](codol/client/account/profile/FUN_006d7b20.c) | 按档案类型选择 DDL 定义 | REA 历史证据 |
| [0x006d87d0](codol/client/account/profile/FUN_006d87d0.c) | 默认档案初始化路径 | REA 历史证据 |
| [0x006d8560](codol/client/account/profile/FUN_006d8560.c) | 档案下载状态处理 | REA 历史证据 |
| [0x006d83e0](codol/client/account/profile/FUN_006d83e0.c) | 档案异步任务完成处理 | REA 历史证据 |
| [0x00a5a890](codol/client/account/profile/FUN_00a5a890.c) | 公开档案查询任务 8/1 | REA 历史证据 |
| [0x00a5a420](codol/client/account/profile/FUN_00a5a420.c) | 公开档案保存任务 8/3 | Ghidra 定向分析 |
| [0x006d7340](codol/client/account/profile/FUN_006d7340.c) | 档案压缩辅助 | Ghidra 定向分析 |
| [0x00a5a9d0](codol/client/account/profile/FUN_00a5a9d0.c) | 私有档案查询任务 8/2 | REA 历史证据 |
| [0x00a5a530](codol/client/account/profile/FUN_00a5a530.c) | 私有档案保存任务 8/6 | REA 历史证据 |
| [0x006d7290](codol/client/account/profile/FUN_006d7290.c) | 档案远程任务引用转移 | Ghidra 定向分析 |
| [0x006d7c70](codol/client/account/profile/FUN_006d7c70.c) | 档案数据和扩展缓存清空 | REA 历史证据 |
| [0x006d7ce0](codol/client/account/profile/FUN_006d7ce0.c) | 公开或私有 DDL 版本头初始化 | REA 历史证据 |
| [0x006d82f0](codol/client/account/profile/FUN_006d82f0.c) | 档案任务结束和状态复位 | Ghidra 定向分析 |
| [0x006d8a00](codol/client/account/profile/FUN_006d8a00.c) | 档案随机掩码初始化 | REA 历史证据 |
| [0x006d8a70](codol/client/account/profile/FUN_006d8a70.c) | 保存前清理无效装备并同步档案 | Ghidra 定向分析 |
| [0x006d90c0](codol/client/account/profile/FUN_006d90c0.c) | 装备与名片缓存回写档案 | REA 历史证据 |
| [0x006d9da0](codol/client/account/profile/FUN_006d9da0.c) | 账号切换时重置公开和私有档案 | REA 历史证据 |
| [0x006da140](codol/client/account/profile/FUN_006da140.c) | 当前账号档案上下文获取 | REA 历史证据 |
| [0x00a5a650](codol/client/account/profile/FUN_00a5a650.c) | 指定账号公开档案保存任务 8/8 | Ghidra 定向分析 |
| [0x00a5a770](codol/client/account/profile/FUN_00a5a770.c) | 指定账号私有档案查询任务 8/7 | REA 历史证据 |
| [0x006d7e60](codol/client/account/profile/FUN_006d7e60.c) | 档案下载完成后的标志与缓存处理 | Ghidra 定向分析 |

## 大厅配置与握手派生

包：`codol.client.lobby.connection`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x00641e10](codol/client/lobby/connection/FUN_00641e10.c) | dwauth 与 STUN 配置读取 | REA 历史证据 |
| [0x00a61980](codol/client/lobby/connection/FUN_00a61980.c) | 协议 210 握手 transcript 与密钥派生 | REA 历史证据 |
| [0x00a60120](codol/client/lobby/connection/FUN_00a60120.c) | 握手带标签的分块密钥扩展 | Ghidra 定向分析 |
| [0x00a5fb90](codol/client/lobby/connection/FUN_00a5fb90.c) | 握手摘要和密钥材料组合 | Ghidra 定向分析 |
| [0x00a60fd0](codol/client/lobby/connection/FUN_00a60fd0.c) | 握手输出加入发送队列并驱动发送 | Ghidra 定向分析 |
| [0x00a613c0](codol/client/lobby/connection/FUN_00a613c0.c) | 连接失败状态切换和 socket 清理 | Ghidra 定向分析 |
| [0x00a60470](codol/client/lobby/connection/FUN_00a60470.c) | 发送队列链表插入 | Ghidra 定向分析 |
| [0x00a60690](codol/client/lobby/connection/FUN_00a60690.c) | 连接建立轮询与发送队列推进 | Ghidra 定向分析 |

## 大厅前置引导判断

包：`codol.client.lobby.onboarding`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x005c3670](codol/client/lobby/onboarding/FUN_005c3670.c) | un_mp_tutorial 完成判断 | REA 历史证据 |
| [0x005c36f0](codol/client/lobby/onboarding/FUN_005c36f0.c) | onboard_complete 完成判断 | REA 历史证据 |
| [0x005c6350](codol/client/lobby/onboarding/FUN_005c6350.c) | UI 通知定义查询 | REA 历史证据 |
| [0x005953a0](codol/client/lobby/onboarding/FUN_005953a0.c) | UI 通知状态访问 | REA 历史证据 |

## 登录资产包与所有者结构

包：`codol.client.inventory.assets`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x00a472b0](codol/client/inventory/assets/FUN_00a472b0.c) | 资产获取任务 80/230 | REA 历史证据 |
| [0x004a5120](codol/client/inventory/assets/FUN_004a5120.c) | 资产请求和结果绑定 | REA 历史证据 |
| [0x00a4a5b0](codol/client/inventory/assets/FUN_00a4a5b0.c) | 资产对象构造 | REA 历史证据 |
| [0x00a4a6b0](codol/client/inventory/assets/FUN_00a4a6b0.c) | 余额、库存和权益复合对象读取 | REA 历史证据 |
| [0x00a45950](codol/client/inventory/assets/FUN_00a45950.c) | 账号 ID 与账号类型读取 | REA 历史证据 |
| [0x00a64ad0](codol/client/inventory/assets/FUN_00a64ad0.c) | 继承所有者的余额条目读取 | REA 历史证据 |
| [0x00a4bd80](codol/client/inventory/assets/FUN_00a4bd80.c) | 权益条目读取（需结合汇编） | REA 历史证据 |
| [0x004a5680](codol/client/inventory/assets/FUN_004a5680.c) | 登录资产结果转移到余额和库存缓存 | REA 历史证据 |
| [0x004a5280](codol/client/inventory/assets/FUN_004a5280.c) | 资产结果与已有权益和库存的对比诊断 | REA 历史证据 |
| [0x004a4f40](codol/client/inventory/assets/FUN_004a4f40.c) | 权益刷新完成处理与监听通知 | Ghidra 定向分析 |
| [0x00a45630](codol/client/inventory/assets/FUN_00a45630.c) | 账号标识对象的类型字段和 ID 比较 | REA 历史证据 |
| [0x004a5080](codol/client/inventory/assets/FUN_004a5080.c) | 资产获取重试回调与远程任务替换 | REA 历史证据 |

## 仓库获取、物品结构与缓存更新

包：`codol.client.inventory.items`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x00a468c0](codol/client/inventory/items/FUN_00a468c0.c) | 库存刷新任务 80/203 | REA 历史证据 |
| [0x004a6b10](codol/client/inventory/items/FUN_004a6b10.c) | 库存刷新请求入口 | REA 历史证据 |
| [0x004a6c10](codol/client/inventory/items/FUN_004a6c10.c) | 库存刷新完成回调 | REA 历史证据 |
| [0x00a4b850](codol/client/inventory/items/FUN_00a4b850.c) | 库存条目反序列化 | REA 历史证据 |
| [0x00a4b4e0](codol/client/inventory/items/FUN_00a4b4e0.c) | 库存条目默认值初始化 | REA 历史证据 |
| [0x004a57d0](codol/client/inventory/items/FUN_004a57d0.c) | 库存结果消费路径 | REA 历史证据 |
| [0x004a6cc0](codol/client/inventory/items/FUN_004a6cc0.c) | 库存条目转移路径 | REA 历史证据 |
| [0x005e2a50](codol/client/inventory/items/FUN_005e2a50.c) | 库存到物品目录的映射 | REA 历史证据 |
| [0x004a7a50](codol/client/inventory/items/FUN_004a7a50.c) | 库存哈希表按编码物品 ID 查找 | Ghidra 定向分析 |
| [0x004a6a10](codol/client/inventory/items/FUN_004a6a10.c) | 库存刷新重试回调与远程任务替换 | Ghidra 定向分析 |

## 游戏币、点券与大厅显示

包：`codol.client.inventory.currency`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x004a4930](codol/client/inventory/currency/FUN_004a4930.c) | 游戏币与点券请求路由 | REA 历史证据 |
| [0x00a461d0](codol/client/inventory/currency/FUN_00a461d0.c) | 游戏币余额请求任务 80/130 | REA 历史证据 |
| [0x00a4bfc0](codol/client/inventory/currency/FUN_00a4bfc0.c) | 点券余额请求任务 93/1 | REA 历史证据 |
| [0x00a4c4a0](codol/client/inventory/currency/FUN_00a4c4a0.c) | 简单余额条目读取 | REA 历史证据 |
| [0x004a47f0](codol/client/inventory/currency/FUN_004a47f0.c) | 游戏币结果处理入口 | REA 历史证据 |
| [0x004a4890](codol/client/inventory/currency/FUN_004a4890.c) | 点券结果处理入口 | REA 历史证据 |
| [0x006af9e0](codol/client/inventory/currency/FUN_006af9e0.c) | GetCP 界面回调 | REA 历史证据 |
| [0x006af970](codol/client/inventory/currency/FUN_006af970.c) | GetCC 界面回调 | REA 历史证据 |

## 购买构造与结果反馈

包：`codol.client.inventory.purchase`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x004a6550](codol/client/inventory/purchase/FUN_004a6550.c) | 购买任务分派 | REA 历史证据 |
| [0x00a467e0](codol/client/inventory/purchase/FUN_00a467e0.c) | 游戏币购买任务 80/154 参数构造 | REA 历史证据 |
| [0x00a4c220](codol/client/inventory/purchase/FUN_00a4c220.c) | 点券购买任务 93/131 参数构造 | REA 历史证据 |
| [0x00a45b40](codol/client/inventory/purchase/FUN_00a45b40.c) | 购买参数序列化 | REA 历史证据 |
| [0x004a6940](codol/client/inventory/purchase/FUN_004a6940.c) | 购买完成回调分派 | REA 历史证据 |
| [0x00a4c0b0](codol/client/inventory/purchase/FUN_00a4c0b0.c) | 点券购买任务 93/4 或 93/131 参数分支 | REA 历史证据 |
| [0x00a47370](codol/client/inventory/purchase/FUN_00a47370.c) | 游戏币购买的默认参数包装 | REA 历史证据 |
| [0x00a4c280](codol/client/inventory/purchase/FUN_00a4c280.c) | 点券购买的默认参数包装 | REA 历史证据 |
| [0x00a64ca0](codol/client/inventory/purchase/FUN_00a64ca0.c) | 点券购买参数校验与序列化 | Ghidra 定向分析 |

## 商品、SKU、物品与解锁条件

包：`codol.client.inventory.catalog`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x00693160](codol/client/inventory/catalog/FUN_00693160.c) | SKU 界面对象与购买条件 | REA 历史证据 |
| [0x004a4b10](codol/client/inventory/catalog/FUN_004a4b10.c) | 解锁条件名称到索引 | REA 历史证据 |
| [0x004a4ca0](codol/client/inventory/catalog/FUN_004a4ca0.c) | unlockFlagsNew 条件比较 | REA 历史证据 |
| [0x004a4c10](codol/client/inventory/catalog/FUN_004a4c10.c) | 转生和等级阈值解释 | REA 历史证据 |
| [0x007070b0](codol/client/inventory/catalog/FUN_007070b0.c) | SKU 价格和期限读取 | REA 历史证据 |
| [0x00706f10](codol/client/inventory/catalog/FUN_00706f10.c) | 产品内物品与数量读取 | REA 历史证据 |
| [0x005840a0](codol/client/inventory/catalog/FUN_005840a0.c) | 目录编码值读取 | REA 历史证据 |

## 武器经验、等级与界面消费

包：`codol.client.equipment.progression`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x006b7190](codol/client/equipment/progression/FUN_006b7190.c) | WL_GetWeaponRank 界面回调 | REA 历史证据 |
| [0x00695bc0](codol/client/equipment/progression/FUN_00695bc0.c) | 按武器 ID 读取库存信息 | REA 历史证据 |
| [0x00695a80](codol/client/equipment/progression/FUN_00695a80.c) | 库存信息提取（含经验） | REA 历史证据 |
| [0x0046eb20](codol/client/equipment/progression/FUN_0046eb20.c) | 经验到武器 rank 查询 | REA 历史证据 |
| [0x0046ee30](codol/client/equipment/progression/FUN_0046ee30.c) | 武器最大 rank 查询 | REA 历史证据 |
| [0x006b5070](codol/client/equipment/progression/FUN_006b5070.c) | 武器最高等级的界面消费 | REA 历史证据 |
| [0x005845b0](codol/client/equipment/progression/FUN_005845b0.c) | 物品描述符查询 | REA 历史证据 |
| [0x00695a10](codol/client/equipment/progression/FUN_00695a10.c) | 引导角色或特殊物品的库存缺省判定 | Ghidra 定向分析 |
| [0x00695c90](codol/client/equipment/progression/FUN_00695c90.c) | 物品所有权查询的布尔结果包装 | Ghidra 定向分析 |

## 武器配件装备与槽位限制

包：`codol.client.equipment.attachments`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x006b43c0](codol/client/equipment/attachments/FUN_006b43c0.c) | WL_EquipWeaponAttachment 配件装备回调 | Ghidra 定向分析 |
| [0x006c1190](codol/client/equipment/attachments/FUN_006c1190.c) | 防暴盾例外与六槽位装备检查 | REA 历史证据 |
| [0x006b7950](codol/client/equipment/attachments/FUN_006b7950.c) | WL_EquipWeaponAttachment 注册入口 | Ghidra 定向分析 |
| [0x006c2090](codol/client/equipment/attachments/FUN_006c2090.c) | 配件装备直接写入路径 | Ghidra 定向分析 |
| [0x006bf680](codol/client/equipment/attachments/FUN_006bf680.c) | 配件槽位同步到编辑缓存 | Ghidra 定向分析 |
| [0x00699de0](codol/client/equipment/attachments/FUN_00699de0.c) | 装备变更后的界面状态刷新 | Ghidra 定向分析 |
| [0x006bf050](codol/client/equipment/attachments/FUN_006bf050.c) | 武器与六槽配件组合有效性检查 | Ghidra 定向分析 |
| [0x006bf0c0](codol/client/equipment/attachments/FUN_006bf0c0.c) | 读取所选武器与配件到编辑缓存 | Ghidra 定向分析 |
| [0x006bf310](codol/client/equipment/attachments/FUN_006bf310.c) | 配件编辑槽的编码值和有效标志写入 | Ghidra 定向分析 |
| [0x007096c0](codol/client/equipment/attachments/FUN_007096c0.c) | 配件目录关系表兼容性查询 | Ghidra 定向分析 |
| [0x006c4240](codol/client/equipment/attachments/FUN_006c4240.c) | 校验武器与六槽配件并清理无效缓存 | Ghidra 定向分析 |
| [0x006c41c0](codol/client/equipment/attachments/FUN_006c41c0.c) | 配件兼容性子规则组合判断 | Ghidra 定向分析 |

## 武器装备与指定槽位入口

包：`codol.client.equipment.loadout`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x006b4230](codol/client/equipment/loadout/FUN_006b4230.c) | WL_EquipWeapon 回调 | Ghidra 定向分析 |
| [0x006b4350](codol/client/equipment/loadout/FUN_006b4350.c) | WL_EquipWeaponInSlot 回调 | Ghidra 定向分析 |
| [0x006c1e70](codol/client/equipment/loadout/FUN_006c1e70.c) | 武器装备写入路径 | Ghidra 定向分析 |
| [0x006bf130](codol/client/equipment/loadout/FUN_006bf130.c) | 装备槽位上下文辅助 | Ghidra 定向分析 |
| [0x006b7740](codol/client/equipment/loadout/FUN_006b7740.c) | WL_EquipWeapon 注册入口 | Ghidra 定向分析 |
| [0x006b78a0](codol/client/equipment/loadout/FUN_006b78a0.c) | WL_EquipWeaponInSlot 注册入口 | Ghidra 定向分析 |
| [0x006c33c0](codol/client/equipment/loadout/FUN_006c33c0.c) | 装备占用计数与数量限制输入 | Ghidra 定向分析 |
| [0x007051e0](codol/client/equipment/loadout/FUN_007051e0.c) | 当前角色和套装组合索引读取 | Ghidra 定向分析 |
| [0x006c2800](codol/client/equipment/loadout/FUN_006c2800.c) | 当前选择项分类不为 3 的判定 | Ghidra 定向分析 |
| [0x006c29e0](codol/client/equipment/loadout/FUN_006c29e0.c) | 按类别清除冲突装备并提交变更 | Ghidra 定向分析 |
| [0x00706740](codol/client/equipment/loadout/FUN_00706740.c) | 当前选择项编码 ID 读取 | Ghidra 定向分析 |
| [0x006c4160](codol/client/equipment/loadout/FUN_006c4160.c) | 武器类别与装备槽位匹配判断 | Ghidra 定向分析 |

## 大厅远程任务与异步回调

包：`codol.client.lobby.tasks`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x00a62db0](codol/client/lobby/tasks/FUN_00a62db0.c) | 远程任务缓冲对象初始化 | Ghidra 定向分析 |
| [0x00a3b1b0](codol/client/lobby/tasks/FUN_00a3b1b0.c) | 服务号和任务号写入请求 | Ghidra 定向分析 |
| [0x00a3be40](codol/client/lobby/tasks/FUN_00a3be40.c) | 远程任务创建并交给提交器 | Ghidra 定向分析 |
| [0x00a44d00](codol/client/lobby/tasks/FUN_00a44d00.c) | 远程任务结果对象与数量绑定 | Ghidra 定向分析 |
| [0x00a44cf0](codol/client/lobby/tasks/FUN_00a44cf0.c) | 远程任务错误码读取 | Ghidra 定向分析 |
| [0x006f5fb0](codol/client/lobby/tasks/FUN_006f5fb0.c) | 客户端异步任务及回调登记包装 | Ghidra 定向分析 |
| [0x00a3b8a0](codol/client/lobby/tasks/FUN_00a3b8a0.c) | 任务缓冲检查与传输虚调用 | Ghidra 定向分析 |
| [0x006f5d20](codol/client/lobby/tasks/FUN_006f5d20.c) | 客户端异步任务槽位分配及回调路径 | Ghidra 定向分析 |
| [0x00a44d90](codol/client/lobby/tasks/FUN_00a44d90.c) | 远程任务状态对象初始化 | Ghidra 定向分析 |
| [0x00a62c40](codol/client/lobby/tasks/FUN_00a62c40.c) | 远程任务缓冲内存和游标初始化 | Ghidra 定向分析 |
| [0x00a46060](codol/client/lobby/tasks/FUN_00a46060.c) | 任务参数有效性检查与提交包装 | REA 历史证据 |
| [0x00a63f20](codol/client/lobby/tasks/FUN_00a63f20.c) | 服务号和任务号参数对象构造 | Ghidra 定向分析 |
| [0x00a63d80](codol/client/lobby/tasks/FUN_00a63d80.c) | 任务参数对象引用清理 | Ghidra 定向分析 |
| [0x00a63eb0](codol/client/lobby/tasks/FUN_00a63eb0.c) | 任务参数追加账号字段的有效性检查 | Ghidra 定向分析 |
| [0x00a44cb0](codol/client/lobby/tasks/FUN_00a44cb0.c) | 远程任务返回结果数量读取 | Ghidra 定向分析 |
| [0x006f6070](codol/client/lobby/tasks/FUN_006f6070.c) | 带上下文的客户端异步任务登记包装 | Ghidra 定向分析 |
| [0x006f60d0](codol/client/lobby/tasks/FUN_006f60d0.c) | 按任务类型转发远程任务引用 | Ghidra 定向分析 |
| [0x006f5b70](codol/client/lobby/tasks/FUN_006f5b70.c) | 任务槽位初始化并保存完成回调 | Ghidra 定向分析 |
| [0x00a3c6f0](codol/client/lobby/tasks/FUN_00a3c6f0.c) | 参数对象绑定远程任务并进入提交包装 | Ghidra 定向分析 |
| [0x006f62d0](codol/client/lobby/tasks/FUN_006f62d0.c) | 远程任务状态轮询和完成标志设置 | Ghidra 定向分析 |
| [0x006f4d60](codol/client/lobby/tasks/FUN_006f4d60.c) | 异步任务计数和耗时统计 | Ghidra 定向分析 |
| [0x006f6130](codol/client/lobby/tasks/FUN_006f6130.c) | 重试任务引用更新和退避间隔递增 | Ghidra 定向分析 |
| [0x006f6470](codol/client/lobby/tasks/FUN_006f6470.c) | 异步任务完成回调调用与槽位回收 | Ghidra 定向分析 |
| [0x006f64c0](codol/client/lobby/tasks/FUN_006f64c0.c) | 异步任务轮询、重试和完成分支调度 | Ghidra 定向分析 |
| [0x00a3bf10](codol/client/lobby/tasks/FUN_00a3bf10.c) | 远程任务缓冲区准备及最终提交包装 | Ghidra 定向分析 |

## 装备缓存与档案写入

包：`codol.client.equipment.persistence`

| 地址 | 功能标签 | 来源 |
|---|---|---|
| [0x005946c0](codol/client/equipment/persistence/FUN_005946c0.c) | 武器与六槽配件写入编码缓存并标脏 | Ghidra 定向分析 |
| [0x005948f0](codol/client/equipment/persistence/FUN_005948f0.c) | 遍历脏装备缓存并触发档案字段同步 | Ghidra 定向分析 |
| [0x005945b0](codol/client/equipment/persistence/FUN_005945b0.c) | 读取编码缓存中的武器与六个配件槽 | Ghidra 定向分析 |
| [0x00592b10](codol/client/equipment/persistence/FUN_00592b10.c) | 武器与配件缓存按 weaponClasses 路径写入档案 | Ghidra 定向分析 |
| [0x005926d0](codol/client/equipment/persistence/FUN_005926d0.c) | DDL 资源边界和字段路径检查及写入包装 | Ghidra 定向分析 |

