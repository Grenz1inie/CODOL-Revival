# 商城已拥有状态修复：进度记录

2026-10-17：用户因电脑电量不足暂停，后已要求继续。以下保留暂停时记录；本次恢复结果见末尾“恢复实施结果”。

## 目标与授权

- 原问题：全解锁后，仓库已有武器，商城仍显示可购买。用户授权限定范围实施、严格TDD、阶段性本地提交，不推送。
- 工作仓库：`E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival`，当前分支main。
- 当前选中版本3.19.26.22，实例`runtime/instances/codol-3.19.26.22-911c42a0027c`。不得套用3.3.3.3的协议或补丁地址。
- 不修改原游戏、系统、真实玩家钱包和库存；游戏菜单及操作由用户人工验收。没有必要则不使用子智能体。
- 当前工作区还有其他任务的启动器、Rust对局等改动；只暂存本任务文件。其他任务可能继续提交，禁止reset或整体暂存。

## 已完成并提交

`3350ce3 fix(codol319): reject owned item purchases`

根因之一已复现：控制器授予物品ID，原购买代码只检查SKU购买记录；全解锁后SKU历史为空，重复购买仍扣款但不增加物品。修复按SKU映射的全部物品检查永久拥有状态，不伪造SKU历史；部分拥有的礼包维持目录全价。

修改文件：

- `games/codol/versions/v3_19_26_22/server/local_profile319.py`：`PurchaseError`、完整目录/拥有/余额校验；购买前备份，逐文件原子写入，普通写入错误回滚。未实现跨文件断电事务。
- `games/codol/versions/v3_19_26_22/server/lsg_handshake.py`：80/154与93/131均正确回传拒绝原因，连接继续可用。
- `games/codol/versions/v3_19_26_22/tests/test_marketplace319.py`：6个测试方法，覆盖全解锁、相同物品不同SKU、GP/CP、部分礼包、目录缺失、余额不足、免费/无限模式、备份、写入故障、重新加载及加密大厅回环。
- `games/codol/versions/v3_19_26_22/tests/lobby_client319.py`：从原库存测试提取共用的真实大厅握手测试助手。
- `games/codol/versions/v3_19_26_22/tests/test_inventory319.py`：原回环测试使用助手，原断言保留。
- `docs/wiki/v3_19_26_22-console.md`：证据、行为和未验收边界。

TDD过程已完成：先观察重复扣款失败、拒绝异常导致大厅断开失败、保存失败无法回滚失败，再最小实现。最后一次定向回归命令：

```powershell
& 'A:\Coding\Python3.13.7\python.exe' -B -c "import sys,unittest; sys.path.insert(0,'games/codol/versions/v3_19_26_22/tests'); unittest.main(module=None,argv=['unittest','test_marketplace319','test_inventory319','test_console319'],verbosity=1)"
```

20项通过，43.609秒。含已有原生Unicorn库存解析。未跑收尾全套，未重启真实游戏/大厅，未声称运行服务已采用修改。没有未结束的测试或构建进程。

## 用户最新证据

用户发来英文商城卡片截图，并说明“这些我都有”。图中AK-47、MK17-CQC、Famas、CheyTac M200、M16A4、PDW90、AA-12、.50GS仍显示GP/CP价格，未见已拥有标记。

截图已另存`work/codol319-console/user-owned-shop-2026-10-17.png`。这证明显示问题，不证明实际扣款。用户已回答具体商品，不要重复索要同样信息。

**商城卡片显示尚未修复，不能把服务端拒绝重复购买当作整个任务完成。**

## 已保存的原生与Flash证据

主要工作目录`work/codol319-console/`，均已保存到磁盘，暂不将游戏资源/二进制加入Git。

- 原EXE SHA256：`36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537`。
- stage6 text哈希`2894b36077fc6fe07e7235bb532c75895928ce69ac0b46bec15184e077199e0c`；rdata哈希`0e24e7a86acb4a13d851bad92935cef4169865082a3aca3153970b7687f309b2`。快照在实例game目录。
- `analysis-client319.exe`为分析映像，SHA256`4fa4db2b90a3590aea271904096021dcbed28f81dc84b42607e7c9285469cdd3`，不是可启动游戏。
- `IsMarketplaceItemOwned`注册回调`0x696e80`调用`0x5e3760`；`IsPermanentOwnedProduct`回调`0x69b9f0`调用`0x5e8130`。
- 永久拥有链`0x5e8130 → 0x80cd80`取产品物品列表，再`0x5e3760 → 0x5e3620`读取物品状态。普通永久物品离线返回真，缺失物品/不完整礼包返回假；描述符`+0x20`的bit2排除永久产品判断，其业务名尚未确认。
- `0x4a76c0`只把前20,000项资产复制进客户端库存表；存档有21,740项。此上限不能自动解释截图里的全部武器，不能靠任意删库存或重排来掩盖。
- 错误码映射来自本版本`0x806a0f/0x806a18`枚举/名称数组：无效参数`0x1f43`，存储`0x1f45`，余额不足`0x1f47`，已永久拥有`0x1f97`。

本轮新解出的实际UI：

- 输入`game/IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs`，SHA256`ac5e1d194833cbedfe0e9d8b476b2e1d9f93414d01e0e49601a80abfe89ea981`。
- `inspect_shop_ui.py`只读解码当前FF461（0x1cd），FF偏移11188079，名称`ui_mp`；使用当前rdata中的原生资源材料，验证签名、header SHA256及3543个数据块哈希，不跳过校验。
- `ui-zone319.bin`：42,877,241字节，SHA256`0f241cccff29bf171d613b3f5d5da23986e55cd055d94807ec9a1f14333ad470`。
- rawfile名`scaleform/default/codo.gfx`后的zlib正文解为`codo319.gfx`：7,664,688字节，SHA256`314c4abd6936b02955e2f31f781b20ac119ea9878f83698d1a1d6f106558c31c`。该二次解压通过一次性命令完成，文件已保存；`inspect_shop_ui.py`的直接SWF扫描结果为空并不表示没有GFX。
- `inspect_shop_abc.py`解析GFX的DoABC常量池、类/方法及原始字节码，结果`shop-abc-*.json`已保存。该脚本没有执行ActionScript，也未更改资源。

关键ABC索引与下一步：

| 索引 | 类/方法及已知字段 |
| --- | --- |
| 1226 | `codo.objects::ProductObj`；**下一步先读此文件，尚未解读其拥有状态生成逻辑** |
| 931 | `MarketplaceItemCard`；方法10 `setData`（1125字节）；方法5 `withOwnStateHint`（101字节）；常量名93 `isOwnedPermanent`、116 `isOwnedRental`、121 `purchaseUiEnabled`、124 `setItemPurchaseable` |
| 483 | `MarketplaceItem`；方法6 `withOwnStateHint`转给卡片；检查商城调用方是否关闭拥有状态提示 |
| 1295 | `MarketplaceItemCardCallToAction`；方法2 `setItemData`（392字节），按ProductObj动作决定BUY等按钮 |
| 2017 | `MarketplacePurchaseAddToCartPopupView`；方法3 `refreshViewForCurrentItem`调用`IsPermanentOwnedProduct`，还存在`exclusiveProductID`、`ALREADY_HAVE_PERMANENT` |
| 1883 | 对应礼包购买弹窗，也调用永久拥有判断 |

还没有得出“数据错误”或“卡片有意隐藏拥有提示”的最终结论。继续沿ProductObj → 卡片setData/withOwnStateHint → 商城调用方追踪，再决定最小补丁；不要先修改客户端或伪造SKU历史。若需要用户决定实质性的显示行为或客户端资源修改边界，再使用其指定的grill-with-docs。

## 恢复注意

- CodeGraph/GitNexus已用于定位购买/发放调用链；前期GitNexus已刷新，但本轮后续代码和并行任务改动尚未重新索引。恢复时按需要增量更新，不反复全仓扫描。
- REA曾对大型映像分析超时，本轮复用已有证据及Capstone/Unicorn；最后查询时REA无打开的二进制会话。
- UI后续实现仍遵循先失败测试、再最小改动。已有20项通过，只有新增改动或失败才重跑相关部分；最终集中回归一次。
- 保留原生/Flash消费证据与真实画面验收的区别；实际余额和库存从未被本轮测试改写。

## 恢复实施结果

- 显示根因已定位：旧全解锁目录取每个原生槽位首个扫描ID，商城取SKU物品ID。例如AK-47：2208与10009同为槽位803，但客户端拥有哈希按传入ID查找。截图8把均为同类错配，与20,000条上限无关。
- 限定修改`console_store.py`、`local_profile319.py`：按槽位对齐商城ID，库存回包/购买校验/网页与全解锁统一使用；旧存档只读转换，SKU历史保持原始值。
- 新增测试`test_marketplace_ids319.py`与离线原生消费者`client_marketplace319.py`。8项原生判断先全部失败；正确ID对照返回已永久拥有；实施后18项定向测试通过，1.753秒。
- 实际目录只读验证：21,740项仍全部保留，1,291个ID纠正，41,885个SKU均在完整库存中满足拥有条件；玩家数据未回写。20,000条客户端列表上限仍保留，不声称尾部物品逐项可见。
- GFX的ProductObj/卡片逻辑已解析，原版会依据正确拥有状态关闭购买并隐藏价格，无需改资源。分析脚本`disassemble_shop_abc.py`与解码JSON/原始快照可复用，输入说明在脚本头部。
- 详细ID表、原生地址、测试边界见`docs/wiki/v3_19_26_22-console.md`末节。真实游戏尚未重启，用户菜单验收仍待进行。
- 收尾全套仅运行一次：440项，433通过、3跳过、3失败、1错误，264.777秒。未通过项为3.3的两个现有快照字典断言，以及3.19原生构建/加载器缺少兼容x86 MinGW链接库；均不在本修复修改路径内，未扩大范围修理。完整输出：`work/codol319-console/marketplace-full-tests-20261017.log`。文档链接检查463条，缺失0条。
