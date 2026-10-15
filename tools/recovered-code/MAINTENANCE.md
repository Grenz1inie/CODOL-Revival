# 维护与复用

当前目录是本任务唯一的项目写入范围。维护脚本只写入此目录。根目录的 `AGENTS.md`、现有源码、原游戏与既有证据均作为只读输入。

## 离线重新导出

在 CODOL-Revival 根目录执行：

```powershell
python tools/recovered-code/maintenance/export.py
python tools/recovered-code/maintenance/verify.py
```

导出器同时生成 `call-chains.json`，并在函数索引中记录已取证的直接调用者和被调用者。`ExportFocusedFunctions.java` 的 `call_sites` 保留每个 CALL 地址、原始指令及 computed 标志；验证器逐项核对来源记录和指令，不把伪代码中的名字匹配当作调用证据。已有主文件的内容哈希优先保留，新结果作为变体。

临时 Ghidra 项目放在本目录 `work-projects/`（Git 忽略），不要用以点开头的目录名；Ghidra 的项目路径检查会拒绝它。仍使用 `-readOnly -deleteProject -noanalysis`，结果写入 `evidence/focused/`，日志写入对应轮次目录。

`catalog.json` 显式列出需要维护的地址、包和业务标签。导出器从现有 REA 单次反编译证据、本目录 `evidence/fresh` 和 `evidence/focused` 收集匹配目标哈希的结果；只做换行规范化，并为代码正文、文件和来源记录 SHA-256。首次任务基线在 `evidence/baseline.json`。

新增函数时先通过 REA 定位真实入口，获得反编译结果，再加入清单。不要把任意内部指令地址当新函数，不要用手写逻辑替换 Ghidra 正文。补充解释放在文档中；有不同恢复结果时保留来源和变体。离线导出不会启动 REA/Ghidra。

## 新的 REA/Ghidra 查询

`maintenance/rea-session.mjs` 使用已安装的 REA 和隔离 Node，给 Ghidra 首次分析留出 20 分钟，并顺序处理 JSON 行命令。环境变量只传给本次子进程，没有改系统配置。

```powershell
& "$env:LOCALAPPDATA/Programs/rea/node_modules/node/bin/node.exe" tools/recovered-code/maintenance/rea-session.mjs
```

输入格式：`{"name":"工具名","arguments":{...},"output":"文件名.json"}`。输出文件保存在 `evidence/fresh/`，使用新的文件名避免覆盖旧批次。工具参数以实际 REA 版本的 schema 为准。

先 `open_binary` 指定原 EXE、`provider_id: "ghidra"` 和匹配版本的 `snapshot_path`，再调用 `batch_decompile`、`xrefs`、`procedure_callees` 等。收尾调用 `export_evidence_bundle`，随后 `close_binary` 同时保存到新的 `snapshot_path`，最后输入 `quit`。

REA 快照保存已查询结果及绑定，并非完整 Ghidra 数据库。本次快照导入和 Evidence 导出成功，但重复历史组合查询也未及时返回，所以没有确认在线查询缓存命中。新查询可能触发 Ghidra 对整个二进制的自动分析。后续读取已恢复函数优先直接使用本目录的代码和记录；不要为读取同一份结果重复启动扫描。

## 独立 Ghidra 定向补充

本次缺口使用 `ExportFocusedFunctions.java`，通过现有 Ghidra `support/analyzeHeadless.bat` 导入原 EXE，传入 `-readOnly -deleteProject -noanalysis` 和 `-postScript ExportFocusedFunctions.java 输出JSON 地址1 地址2 ...`。项目、日志和结果均指向本目录。脚本对明确入口执行反汇编和函数创建，保留原始指令、直接调用目标及伪代码。

导出器保留两类来源和全部不同代码变体，优先选择完整 REA 默认分析结果为已有函数的主文件。独立结果使用 `source_kind: standalone-ghidra`，不制造 REA Evidence ID。不能把定向结果的类型恢复能力当作默认全程序分析。

本次结束的会话、快照与来源统计见 [会话说明](SESSION.md)。`evidence/fresh/*.timing.json` 记录调用起止时间和输入。历史来源仍保留其原始 Evidence ID，不能重新标注为本次新观察。
