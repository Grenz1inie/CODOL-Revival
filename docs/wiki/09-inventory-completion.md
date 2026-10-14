# 点券、全物品与武器成长

本章接续 [玩家数据与商城](08-player-progression-marketplace.md)。协作边界见项目根目录 [AGENTS.md](../../AGENTS.md)。

## 登录与两种余额

本地账号 JSON 的 `currency` 保存游戏币，新增 `premium` 保存点券；旧档案没有该字段时按 0 读取，不覆盖已有余额或物品。ID 1 为游戏币、ID 2 为点券。购买按 SKU 的 `cash_price` 或 `price` 扣对应余额，余额与库存一次原子保存。

首次尝试在 `80/230` 增加第二个货币对象，游戏仍不显示点券。REA 确认 `0x4a5680` 的初始资产回调只复制第一个余额，`0x4a4930` 分别请求游戏币 `80/130` 和点券 `93/1`；`GetCC` 回调 `0x6af970` 从独立缓存取 ID 2。因此点券必须实现 `93/1`，不能仅扩充资产列表。点券购买使用 `93/131`，与游戏币 `80/154` 的请求尾部支付选择值不同。证据见 [余额路由](../../research/evidence/expansion-balance-service-routing.json)、[点券读取](../../research/evidence/expansion-premium-getter-request.json)、[购买构造](../../research/evidence/expansion-cc-requests-weaponrank.json)。

控制器新增点券入口，仍要求退出游戏后修改。数量必须是正整数，增加后的余额不超过 2147483647；布尔值、越界、运行中的修改均拒绝。

## 仓库发放范围

`mp/coMarketplaceItems.csv` 包含 6772 种物品，可购买 SKU 只覆盖 5335 种。发放使用完整物品目录，不能只遍历 SKU，否则会漏掉配件、皮肤等。目录中的武器 201 种、武器配件类 4673 种，其中 `cam` 子类 1680 种。

库存永久期限使用已验证的 `0xffffffff`。发放保留已有数量和余额、按物品 ID 去重，重复执行不累加数量。物品名称仍为客户端资源名，不编造中文译名。

## 武器经验与解锁

`Read-PlayerSchema.ps1 -WeaponProgression` 只读提取当前客户端的 `mp/coWeaponPrimaryRankTable.csv` 和 `mp/coWeaponSecondaryRankTable.csv`，保存在 [武器等级表](../../research/evidence/live-weapon-progression.json)。主武器表 31 行、副武器表 20 行；最后两行分别为 `29/89800、30/121230` 与 `18/35600、19/71200`。

REA 确认 `0x46eb20` 按经验查询 rank，`0x46ee30` 取末行最大 rank，`WL_GetWeaponRank` 的回调 `0x6b7190` 返回 rank+1。因此主武器满级为 31、经验 121230；副武器为 20、经验 71200。`0x695bc0 → 0x695a80` 从库存取经验，协议中为第三个 uint32；武器描述符 byte+6 小于 6 使用主武器表。见 [经验读取链](../../research/evidence/expansion-weapon-experience-path.json) 与 [等级回调](../../research/evidence/expansion-cc-requests-weaponrank.json)。

武器经验、配件所有权、商城条件是不同层次。不得用填满整个私有档案或写入任意巨大经验值代替字段确认。

## 手动续期

控制器列出已拥有的限时物品，包括已过期物品。选择物品和天数，期限按 `max(原期限, 当前时间) + 天数*86400` 计算。允许 1–36500 个整数天；不允许触及永久哨兵值或溢出 uint32。永久物品无需续期，未知物品不能通过续期接口发放。续期不扣余额，不增加数量，写前备份。

## 验证状态

- 44 项自动测试通过；前端 TypeScript 检查及构建通过。覆盖独立点券持久化、加密 `93/1 → 93/131 → 93/1` 购买链、全目录去重发放、主副武器经验编码、续期/过期/溢出和 HTTP 运行中拒绝。
- 16:31 用户确认游戏显示点券、扣款并入库。服务日志连接 `127.0.0.1:59469` 记录 SKU 26997、物品 60135、7 天、380 点券；点券由 100000 变为 99620，游戏币仍为 44445。
- 16:36 实际浏览器续期 30 天，物品 60135 的期限从 1792571478 变为 1795163478，界面到期日从 10 月 21 日变为 11 月 20 日。随后点击全物品发放，持久化 6772 个唯一物品、201 把武器满级经验，均为永久，已有数量及余额保持；写前备份保留。
- 游戏重登，连接 `127.0.0.1:49925`。用户确认仓库大量武器永久、M14 EBR 满级、配件和皮肤可装备、点券仍为 99620。上述为用户人工验收反馈，无新截图；不表示逐一试装了目录中的每件物品。
- 16:55 自动输入验证截图进一步显示 M4A1 为 31 级、贝瑞塔 M9 为 20 级，已装备配件，点券为 99620，见 [仓库背包](../../runtime/captures/screenshots/20261014-admin-input-test.png)。

本轮 REA 已导出 [144 条证据包](../../research/evidence/expansion-evidence-20261014.json) 和 [分析快照](../../research/evidence/expansion-complete.rea.json)，随后关闭会话。项目与客户端 GitNexus / CodeGraph 索引已刷新；客户端索引含 188 份伪代码变体和 4 份随包代码文件，伪代码仍按研究证据使用，不等同于游戏源码。

训练、匹配、对局服务不属于本章，见 [对局服务](07-session-game-server.md)。
