# 3.19.26.22 网页档案操作

选择并匹配本版本游戏目录，启动生成实例档案后，网页显示账号、等级、转生、GP和CP。退出游戏即可增加两种货币、设置最高等级与转生、解除剧情前置条件、发放完整物品目录。运行中修改返回409；未生成档案、错误账号和无效输入不会写入。

所有操作限定于选中实例的 `server/profile319.json` 和 `server/local-profiles319/`。写入前保存原文件到实例 `backups/`，使用临时文件加原子替换。余额溢出与损坏JSON会明确失败；读取状态不创建钱包。提供工具启用无限货币时显示其固定余额，并拒绝无效的固定余额增加操作。

| 操作 | 本版本实现 |
| --- | --- |
| 游戏币 / 点券 | 分别修改wallet键1 / 2，保留其他币种；标签GP / CP |
| 最高等级与转生 | 70级、4转生，累计XP 3,582,550，rankVersion=4；同步等级解锁条件1 |
| 剧情前置条件 | 将条件150–159至少设为1，保留更大的已有值和其他条件 |
| 全物品 | 读取本实例完整item-registry319.json，当前21,740个目录项；合并已有库存、永久发放，不只遍历可购买SKU |
| 后续购买 | 保留网页已发放物品；首次发放前固定旧格式SKU兼容记录，避免把新物品ID当成已购买SKU |

剧情条件解除与地图启动分别验收。当前测试对局仍为Seatown、单人、无AI；这次没有实现原版剧情服务。全物品操作没有额外修改武器经验、配件解锁规则或皮肤消费逻辑。

## 当前版本证据

游戏EXE SHA256：`36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537`。只读提取目标为隔离实例PID44184，枚举出的模块基址为`0x400000`；运行时指针直接读取，不进行二次重定位。

首先复用了已保存的stage6快照。text快照SHA256为`2894b36077fc6fe07e7235bb532c75895928ce69ac0b46bec15184e077199e0c`；rdata为`0e24e7a86acb4a13d851bad92935cef4169865082a3aca3153970b7687f309b2`。未对当前游戏执行注入、断点或内存写入。

REA/Ghidra完整及按页裁剪分析两次超时。备援Ghidra headless使用`-noanalysis`按已知入口反编译，随后回REA对保留原字节的最小分析映像交叉确认。该映像SHA256为`2168c3384dfca22a30cc73c1b741a2c05cab43d2dbfaba6fd92696d7d7cceff8`，只保留指定函数字节，其余代码为INT3，不能执行。REA部分伪代码因未包含的callee被判定不返回而截断，因此使用完整指令和REA字节读取复核，不将裁剪伪代码视为完整函数分析。

| 地址或资源 | 来源与覆盖范围 | 未验证项 |
| --- | --- | --- |
| `0x49c870`、`0x49ca70` | 当前text指令、备援Ghidra、REA；类型参与hash，mod120000，bucket `0x1e2d338`，entry `0x239b120`，stride28。用于定位实际挂载资源 | 不覆盖其他版本资产表 |
| `0x50f2c0`、`0x512120` | 当前指令及只读结构；secure分支读取`mp/playersecuredata.def`，数据区长0x7ffc | 不代表所有私有档案字段均已实现 |
| `0x474310`、`0x67ee40` | 当前指令、备援Ghidra；从实际rankTable的maxprestige行读取并返回4。REA完整字节证据`ev_e60e840494440d5261e5372cd4e1cee467e29b8787c9c3612e18841008a964b7` | 游戏UI对最高等级/转生的最终显示待重登确认 |
| 实际`mp/rankTable.csv` | 当前进程ReadProcessMemory：0x29c53f4，72行；version4、最高等级70、对应XP3,582,550。原包rankTable319.csv的2,434,700不是当前实际表，结算与网页统一改用版本内提取数据 | 未恢复转生流程本身 |
| 实际私有DDL | v19/hash2739108020，size15124，10007个槽；经验offset4840、转生4879、等级4883、rankVersion4887，偏移不含CRC。36个扩展字段与提供包逐项核对一致 | 其他版本/其他DDL不适用 |
| `0x4a6d60` | REA完整165字节证据`ev_a530c0cd2f5656b72b39a0bb56dd1cf90b4301ce2e00cf0522fd7e44f615815a`，指令访问secure的unlockFlagsNew并与条件阈值比较；稀疏条件名映射来自当前unlockFlags.csv | 菜单模式可见性与剧情地图可玩性未恢复 |
| 当前coMapList/unlockFlags/DDL | 0x29c5484 / 0x29c57c4及当前结构；coMapList中10项coop前置名映射150–159，按实际槽偏移写入8591…8609（不含CRC） | 未声称其他条件全部解锁 |
| `0x7f6330` | 私有档案读取入口；REA完整字节证据`ev_b693ac18bcbd0baef614343cf7d6efd9653180ada1bfdac92a6e91965e8cbe11`。沿用提供工具的封包与压缩，正文及扩展字段同步 | 本轮未进行新的协议分帧、密钥或状态机恢复 |
| `0x7f6a70`、`0x7bc4d0` | 原始快照指令在Unicorn执行；32764字节正文，CRC多项式0xedb88320，三个向量与zlib逐一一致，覆盖初始化及写回`context+0x8c` | 不代替真实加密回环抓包与客户端验收 |
| `0xb8d050` | REA完整字节证据`ev_acbad3db30faba401112c45a5c6e880465266a86e6fa761373990be8c0a8bf6d`；库存项目ID/数量/第三字段、blob、int64期限等读取顺序与提供实现一致 | 全量库存是否均能展示、装备及使用待游戏内验收 |

本机原始证据位于`work/codol319-console/`：`live-schema319.json`记录只读范围、资源地址和哈希；`analysis-image.json`与`micro-image.json`记录派生映像来源；`fallback-consumers.c`、`rea-evidence.json`、`native-crc319.json`记录静态及模拟验证。版本内`resources/definitions/profile319.json`绑定提取文件SHA256，禁止将3.3的定义哈希代入。

REA快照保存为同目录`rea.snapshot.json`并已关闭。恢复需使用上述最小映像和快照路径。此次9项工作流查询中1项地址未识别为函数，其余伪代码存在上述裁剪限制；字节读取成功。此轮是新分析，未声称命中既有客户端分析缓存。

## 验收

定向测试覆盖两种货币、等级/转生上下界、剧情字段保留、完整目录合并、重复发放、后续购买保留库存、JSON损坏、溢出、备份、写入失败、实例隔离、重启序列化以及全部五项HTTP运行锁。原生CRC模拟单独记录，不把Python自我编解码当作客户端消费证明。

2026-10-16集中回归：`python -B tools/run-tests.py`共378项，375通过、1跳过、2失败，耗时245秒。两项失败与改动前一致，均为3.3.3.3的旧完整快照字典断言：`test_native_server423.NativeServer423Tests.test_native_initial_snapshot_reaches_current_baseline_store`及`test_story_wire423.Configstrings423Tests.test_initial_snapshot_reaches_current_baseline_store`。本轮没有修改这些实现或断言。前端33项测试通过，TypeScript/Vite构建通过。

网页控制器已重载，新能力与现有档案在真实页面可见。游戏及大厅服务保持原会话，档案写入按钮因游戏仍运行而锁定；新版私有档案编码器将在下次启动游戏时加载。

游戏内余额、等级、转生、剧情锁及全量库存需要在重新启动后人工确认；新增代码通过测试和页面显示不代表这些实机验收已完成。
