# 2026-10-15 导出会话

执行范围：只读原客户端和既有证据，在 `tools/recovered-code/` 内新增恢复资料。未执行游戏、运行时注入、存档修改或 Git 提交。

工具：已安装的 REA 6.4.0，通过其官方 MCP 启动入口使用 Ghidra 12.1.4；本次子进程使用隔离 Node 24.21.0 和现有 JDK 21。没有安装软件或修改全局配置。

恢复输入：`research/evidence/expansion-complete.rea.json`。该快照包含 144 条历史 Evidence 和 71 个组合查询绑定，没有完整 Ghidra 数据库。它匹配本次 EXE 的 SHA-256 和 Ghidra 分析配置。

既有认证、档案、资产和武器成长伪代码从同哈希的原始 REA 记录导出；本次新增查询单独保存在 `evidence/fresh/`，每次调用有独立的输入和起止时间记录。

首个新增反编译于北京时间 13:30 发起，要求 Ghidra 完成默认自动分析后才返回结果。20 分钟启动等待超时后终止本任务拥有的独立 REA 进程，未取得该批结果。`evidence/fresh/rea-session.log` 保留 MCP 操作日志。没有将失败请求记为成功反编译。

随后用独立 Ghidra 12.1.4 定向脚本成功补充装备入口、注册函数、槽位写入和公开档案保存等。输出在 `evidence/focused/`，默认全程序分析被禁用，所有成功函数均保留指令和伪代码。其来源明确标为独立 Ghidra，不使用 REA Evidence ID。

通过 REA 的 `export_evidence_bundle` 导出 [144 条历史 Evidence](evidence/rea-session-bundle.json)，1053619 字节。该记录数来自已恢复快照，未宣称为 144 条新观察。

已原样保留可复用的 [历史快照副本](evidence/reuse-history.rea.json) 及 [来源哈希](evidence/reuse-history-origin.json)。这不是本次完整 Ghidra 自动分析的新快照。本次 REA 会话最终通过 `close_binary` 成功关闭；独立 Ghidra 三个批次均正常退出，并以 `readOnly` 丢弃导入项目。

最终覆盖：12 个包、79 个唯一函数、82 份伪代码变体。其中 66 个函数有历史 REA 结果，本次独立 Ghidra 对 15 个唯一函数成功定向反编译（与历史重合 2 个，新增 13 个）；三个批次共 16 次成功输出，其中配件入口重复一次并保留两份变体。选中的 REA 原始记录共 48 条，另保留完整 144 条历史证据包。

工作区核对：首次基线记录了 148 个既有跟踪文件。在分析等待期间观察到其他工作继续改动 `tools/native/server3333.patch`、`tools/probe_native_connection.py`、`web/src/App.tsx`、`web/tests/App.test.tsx` 等文件。本任务未向这些路径写入，也未撤销它们；最终报告列出与基线不同的路径，不将整个共享工作区描述为未变化。

最终函数数量、代码/来源/链接校验及 EXE 哈希结果以 [verification.json](verification.json) 为准。
