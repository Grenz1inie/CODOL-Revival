# 开发协作

先读 [项目状态](README.md) 和 [技术 Wiki](docs/wiki/README.md)。本项目仍是单机协议原型，验收点是具体游戏流程，不能以端口监听或成功响应替代界面验收。

## 环境与验证

当前验证环境是 Windows、Python 3.13.7。新环境可使用虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B tools/run-tests.py
.\.venv\Scripts\python.exe -B tools/check-doc-links.py
```

当前电脑已有依赖，可直接用 `python` 运行测试。启动脚本优先使用 `.venv`，否则使用 PATH 中的 Python。`games/codol/versions/v3_3_3_3/scripts/Start-Services.ps1 -PythonPath <解释器路径>` 可指定解释器。REA/Ghidra 是独立研究工具链，不属于游戏服务依赖；配置见 [工具链](docs/wiki/01-baseline-toolchain.md)。

`python -B tools/check-startup.py` 只读检查管理器Python依赖、启动文件和前端产物；选中版本的游戏地址和证书在启动游戏时检查，失败返回非零退出码。缺少依赖或前端产物时按输出命令补齐；证书与游戏配置的准备见 [地址重定向与 TLS](docs/wiki/03-redirection-tls-auth.md)。该检查不会安装依赖或修改配置。

Rust对局服使用项目内1.99.1 GNU工具链；`scripts/Invoke-MatchCargo.ps1`设置本次进程环境，
构建产物写入`runtime/builds/codol/v3_3_3_3/rust-match/`，不更改系统PATH。依赖已经缓存时可加`--offline`：

```powershell
powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 build --release
powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 test --offline --release
$env:PYTHONPATH='src;tests;games/codol/versions/v3_3_3_3/tests;games/codol/versions/v3_3_3_3/reverse/tools'
python -B -m unittest test_match_process test_rust_match_runtime test_independent_matchmaking test_controller_services
```

当前生产只运行Rust对局服；`games/codol/versions/v3_3_3_3/reverse/tools/reference_match/`是冻结的迁移对照和资源导出依赖。
不要在其中继续开发对局行为或增加生产回退。基准、浮点容差和人工验收边界见
[Rust迁移](docs/wiki/12-rust-match-server.md)。原生UDP集成`test_rust_match_server`另需本机
3.3.3.3客户端、核弹小镇隔离资源包与已构建Rust程序，只读资源并使用临时端口，
不操作正式游戏或存档。

## 文件归属

- `src/`：共用管理器；版本源码、逆向工具、模拟服和测试归入 `games/codol/versions/<版本>/`。导入模块不得启动监听器。
- `games/codol/versions/v3_3_3_3/server/native/match-server/`：本版本Rust独立对局进程、Cargo锁文件与合成测试；游戏资源和生成二进制不入Git。
- 版本目录的 `resources/definitions/`：客户端静态定义，保留来源哈希，不参与代码索引。`games/codol/versions/v3_3_3_3/reverse/tools/export-marketplace.py` 从本地只读证据重建，运行服务无需管理员读取。
- `web/`：控制器前端；`npm ci` 安装锁定依赖，`npm run build` 同时做 TypeScript 检查和生产构建。`node_modules/`、`dist/` 不进入版本控制。
- `scripts/`：面向操作者的 PowerShell 启停入口，路径从项目位置推导。
- `tools/`：证书、REA 与文档检查等开发工具。
- 版本目录的 `tests/fixtures/`：测试专用输入；测试不得依赖正在运行的游戏或修改正式玩家数据。
- `docs/wiki/`：按游戏流程记录原理、问题、解决办法和证据；当前状态维护在总览及对应分章。
- `docs/reports/`：带日期的验证、搬迁记录。保留当时失败结果。
- `research/evidence/`：本地反编译、快照和原始样本；`research/reference-protocol/` 保留外部来源及许可证归属。
- `runtime/`：日志、抓包、证书、角色数据、备份。全部不进入版本控制。
- `archive/`：历史基线，保留原始内容；归档中的旧路径通过搬迁清单查找。

## 代码索引

游戏侧另有 [客户端逆向代码索引](research/client-code-index/README.md)，注册名 `CODOL-Client-RE`。它索引随包脚本和已有 REA 伪代码，独立于下面的自研服务索引。

索引根目录是 `CODOL-Revival`，不是相邻的游戏目录。GitNexus 的 `.gitnexusignore` 放行 `src/`、`games/`、`tests/`、`tools/`、`scripts/`、`web/`，排除前端依赖、原始证据、静态数据和产物；CodeGraph 的 `codegraph.json` 同样排除运行数据、归档、研究材料、文档及测试二进制样本。新增顶层目录时检查这两份配置，避免引入第三方源码或数据。

索引数据库位于 `.gitnexus/` 和 `.codegraph/`，已加入 `.gitignore`；保留配置文件即可在其他机器重建。项目已初始化Git并分阶段提交，可按当前提交刷新索引；索引未更新时以当前源码为准。

在项目根目录执行：

```powershell
# 首次建立或源码修改后重建；不生成 AGENTS.md、CLAUDE.md 或技能文件
gitnexus analyze . --skip-git --index-only --name CODOL-Revival
# 首次建立 CodeGraph
codegraph init . --yes
# 后续更新 CodeGraph
codegraph sync .

# 查询时明确指定项目，避免命中其他工作区
gitnexus context handle_lobby --repo CODOL-Revival --file games/codol/versions/v3_3_3_3/server/dw_lobby.py
codegraph explore 'lobby_client handle_lobby ProfileStore validate_profile'
codegraph files
```

2026-10-14 15:51 更新：GitNexus 1.6.12 纳入 32 个文件，267 个节点、686 条关系；CodeGraph 1.6.2 解析 21 个文件，377 个节点、859 条关系。MCP 已检索到 `MarketplaceStore.purchase` 及测试、存储调用。GitNexus 自动流程有预算截断，未列出调用者不代表没有调用；运行时分派仍需读源码。PowerShell 脚本仅确认出现在 GitNexus 文件清单中，不能据此声称具备完整语义分析；CodeGraph 未解析这些脚本。代码图用于定位和影响分析，游戏 EXE 逆向仍使用 REA/Ghidra。

## 变更完成条件

1. 明确涉及哪一阶段、改变哪种响应或状态，只修改该范围。
2. 协议修改保留一个能复现问题的样本，运行相关测试；使用真实用户样本前检查其数据内容，不提交认证凭证或私钥。
3. 需要运行验收时，记录源码版本/改动、是否重启服务、游戏 PID、连接、请求和界面。存档验收包含退出再进。
4. 更新对应 Wiki 和总览，区分静态确认、运行确认及未完成部分。若移动文件，同步代码路径与 Markdown 链接。
5. 用户未要求时不提交、不推送、不改游戏 EXE。第三方参考实现的许可证独立保留，本项目尚未选定整体发布许可证。

文档链接检查包含本机证据链接；缺少 `runtime/` 或研究证据归档的协作者应先取得对应证据包。协议单元测试使用受控 fixtures 与 `games/codol/versions/v3_3_3_3/resources/definitions/marketplace-catalog.json`，不需要游戏或网络服务，可以独立运行。

## 原生资源实验测试

`test_story_*` 使用本机固定哈希客户端、参考引擎和已提取的 `research/experiments/story-native/` 样本，额外需要 `pefile`（当前电脑已安装）。这部分是离线集成测试，不监听端口、不启动正式游戏，也不替代可玩性验收。新协作者先按[资源链报告](docs/reports/20261014-story-resource-chain.md)准备授权样本；不能把缺少本地研究材料的失败解释为大厅协议回归。
