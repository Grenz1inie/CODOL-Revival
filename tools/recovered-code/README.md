# CODOL 客户端恢复代码资料

这里维护账号、大厅、背包和装备相关的 REA/Ghidra 反编译结果。后续分析从 [功能索引](INDEX.md) 查找入口，并沿 [关键调用链](CALL_CHAINS.md) 追踪下游，可直接读取本地伪代码和证据。

当前共 111 个唯一函数、132 份伪代码，分为 13 个层级包；正文、来源关联和本地链接已通过 [导出校验](verification.json)。

目标：`codoMP_client_shipRetail.exe`，PE32 / x86。

SHA-256：`e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。

所有地址为该镜像首选加载地址下的 VA，镜像基址 `0x00400000`。机器索引另列 RVA；分析实际进程时需要用运行基址加 RVA。

## 目录约定

按类似 Java 包名的层级组织，例如 `codol.client.account.profile` 对应 `codol/client/account/profile/`。这是为后续研究设计的业务命名空间，并非恢复出的原厂包名；文件仍是 C 风格伪代码。

```text
recovered-code/
  codol/client/
    account/auth/                 认证响应与票据
    account/profile/              公开和私有档案
    lobby/connection/             配置、协议握手与密钥派生
    lobby/onboarding/             进入大厅前的引导判断
    inventory/assets/             登录资产包
    inventory/items/              仓库物品与刷新
    inventory/currency/           游戏币、点券及界面读取
    inventory/purchase/           购买请求与反馈
    inventory/catalog/            商品目录与解锁条件
    equipment/progression/        武器经验和等级
    equipment/attachments/        配件装备与槽位
    equipment/loadout/            普通武器和指定槽位装备
  evidence/                       原始记录、汇编补充和本次会话
  maintenance/                    选择清单、导出和验证工具
  INDEX.md                        按功能浏览
  function-index.json             按地址、包、标签和来源检索
```

每个函数以 `FUN_地址.c` 命名，地址固定，原始符号和伪代码语句保持。若同一地址有不同反编译结果，额外保留带内容哈希的变体；机器索引记录各自来源。中文功能名是分析标签，不会重命名伪代码内变量或函数。

本批结合两类结果：同哈希历史 REA/Ghidra 默认分析，以及本次独立 Ghidra 定向反编译。REA 全量自动分析超过等待上限后，装备等缺口用 `-noanalysis` 加显式函数反汇编完成。定向分析的类型、函数边界和间接调用恢复较弱，原始指令一并保存在 `evidence/focused/`；这类记录不冒充 REA Evidence，机器索引的 `source_kind` 会区分来源。

## 使用方式

1. 在 [INDEX.md](INDEX.md) 找业务入口；或在 `function-index.json` 搜索地址、任务号、功能名。
2. 阅读对应 `.c` 与 [流程和边界](FINDINGS.md)。查看 `variants[].origins` 可定位完整 Evidence、来源文件哈希和分析配置。
3. 如需确认缺失参数、寄存器输入、虚函数或异常分支，回到保留的汇编或继续用 REA 查询。`textual_call_candidates` 只是从伪代码提取的调用候选，未覆盖间接调用。
4. 客户端升级时先比较 SHA-256。不同版本应另建版本目录，不能将旧地址直接套用。

伪代码是可复用的静态分析材料，不保证可编译，也不等同于原始源码。调用约定、类型和控制流可能被错误恢复，`WARNING`、`in_EAX`、`unaff_ESI` 等信息均保留。这里只覆盖选定关键函数，并未恢复整个客户端或完整 SDK。

本次没有运行客户端、修改存档或验证新的游戏行为。历史运行状态的描述请查原项目 Wiki；本目录的验证针对目标身份、导出完整性和证据可追溯性。

[维护方法](MAINTENANCE.md) · [功能索引](INDEX.md) · [验证结果](verification.json)
