# CODOL 多版本管理器

<a id="chinese"></a>
**中文** · [English](#english)

在网页中选择本机游戏目录，自动核验版本文件与主程序指纹，再调用对应版本的逆向实现和模拟服务器。当前接入 **3.3.3.3**，以及 **3.19.26.22的启动、本地大厅和Seatown测试对局**；2.6.9.7仅收录。版本列表是 [games/codol/versions.json](games/codol/versions.json)，新增版本的规则见 [多版本管理说明](docs/multi-version-manager.md)。

## 当前进度

**2026-10-17 3.19可重建交付**：启动与Seatown对局已移除外部启动包依赖。仓库源码构建代理、回环桥接、碰撞程序和IFS读取器；发布文件与英文资源从匹配原游戏生成，物品/配装表及当前地图由自有游戏进程只读导出。首次准备仍使用隔离副本，保留已有进度。首次部署需Python依赖、x86 MinGW GCC和原游戏，步骤见 [3.19接入说明](docs/wiki/v3_19_26_22-startup.md)。本轮完成构建、资源和协议验证；新组件整套启动后的大厅与游玩仍待人工验收，先前旧组件的实机结果不代表本轮已验收。

**2026-10-16 多版本管理器**：目录选择、版本文件与EXE指纹匹配、操作门控及版本适配器已接入；逆向工具、模拟服务器和测试按版本存放，玩家数据按安装实例隔离。真实3.3.3.3目录识别、存档复制校验及模拟服务器启停已验证；网页新增部分的浏览器截图与原生目录弹窗尚待人工确认，游戏内验收范围不变。

**2026-10-16 Rust独立对局服**：碰撞、移动、AI和UDP协议已迁入独立Rust进程，Python保留网页、认证、大厅和档案，现有启停流程已接入并重载。核弹小镇同输入400帧的整帧P99由91.60ms降至1.62ms，状态在约定精度内一致；这是离线性能结果，Rust版游戏手感待人工验收。仍从“冲锋团队竞技 → 核弹小镇”进入，一名真人、一个AI、固定ACR、自由混战，不新增赛单。构建、证据与验收步骤见 [Rust迁移 Wiki](docs/wiki/12-rust-match-server.md)。9V9等其他玩法未接入。

2026-10-14 12:40 已实际进入游戏大厅，13:03在整理目录并重新启动游戏、服务后再次验证成功，显示用户选择的第二个角色“马库斯”和昵称 johnClient。组合修复包括命令行引导覆盖及本地公开档案读取，详情见 [新手引导与角色资料](docs/wiki/06-onboarding-profile.md)。训练和原版剧情仍未恢复。

已验证：TLS 认证 → 协议210加密大厅 → 发布文件 → 公开档案读取 → 游戏大厅。服务端实现了公开档案保存/读取，21项单元及内存协议测试通过。初次大厅验证使用选角时抓到的原始档案；真实客户端后续修改的保存验收单独记录，不把测试通过当作全部游戏数据持久化完成。

Web 控制器支持引导开关、启动游戏、读取开发 Wiki、3 转生 70 级及分别增加游戏币和点券。商城等级限制已解除；M14 EBR 购买扣款、永久入库和重登保持已确认，点券显示及购买扣款入库也已实测。新增全目录 6772 种物品发放、201 把武器满级经验和手动续期；44 项测试及前端构建通过。浏览器操作已验证，用户确认重登后永久物品、武器满级、配件及皮肤装备正常，点券仍为 99620。详见 [玩家数据与商城](docs/wiki/08-player-progression-marketplace.md)、[点券与全物品](docs/wiki/09-inventory-completion.md)。重复叠加不在本轮实现范围；分辨率任务已按用户要求取消。

## 使用

在本目录打开 PowerShell：

```powershell
.\Start.ps1
```

[Start.ps1](Start.ps1) 先检查并启动网页控制器，再打开 <http://127.0.0.1:8765/>。首次打开点击“选择游戏目录”；匹配成功后启用该版本支持的操作。已有选择会在重启后重新核验；默认入口会启动已匹配的游戏。游戏提权仍需确认 Windows UAC。

```powershell
.\Start.ps1 -CheckOnly            # 只检查管理器环境
.\Start.ps1 -NoGame               # 打开网页，由用户点击启动游戏
.\Start.ps1 -NoGame -NoBrowser    # 只启动后台网页控制器
python -B tools/run-tests.py      # 管理器与版本测试集中运行一次
python -B tools/check-doc-links.py
```

游戏与模拟服务器通过网页一起启停。版本目录内的脚本由管理器传入安装路径及实例目录后调用。详细检查项见 [控制器文档](docs/controller.md)。Python依赖见 [requirements.txt](requirements.txt)，开发约定见 [CONTRIBUTING](CONTRIBUTING.md)。

首次运行或修改Rust源码后，在根目录运行 `powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 build --release`。工具链和构建产物位于项目`runtime/`；运行已构建的对局服不需要临时编译。缺少Rust产物不会回退到Python对局实现。

3.3.3.3首次启动服务会从所选游戏生成核弹小镇包，保存到
`runtime/builds/codol/v3_3_3_3/maps/nuketown/`。该目录是本地生成物，不随Git交付；
235点参考路网和版本注册定义已随仓库提供，不再需要旧服目录或作者的`research/`。
首次提取需要支持32位Windows目标的MinGW GCC；可设置`CODOL_IFS_CC`为其`gcc.exe`路径。
也可先手动准备：

```powershell
$env:CODOL_IFS_CC = 'C:\工具链\mingw32\bin\gcc.exe' # 换成实际路径；已在PATH中可省略
powershell -NoProfile -ExecutionPolicy Bypass -File games/codol/versions/v3_3_3_3/scripts/Prepare-Resources.ps1 -GameRoot 'D:\游戏目录'
```

有效包会复用；提取失败不发布半成品。已有损坏包会报告具体错误并保留，请先将其移出上述目录再重试。
上述手动命令只生成地图。正常从网页启动3.3时，会先检查已安装依赖和构建产物，
再生成地图、准备本实例证书，并备份后配置游戏目录中的`dwauth.ini`、`stun.ini`、`cacert.pem`。
原CA保留；重复启动复用有效地图和证书；失败会在网页显示具体原因。
新电脑先按[开发环境](CONTRIBUTING.md)安装Python依赖、构建前端及Rust对局服，
首次地图提取另需上述32位MinGW工具链。无需复制作者的`runtime/`或`research/`。
备份、证书和恢复步骤见[地址与证书](docs/wiki/03-redirection-tls-auth.md)。

## 目录

```text
src/controller.py                共用控制器HTTP入口
src/manager/                     版本识别、安装选择、数据迁移、原生目录选择
web/                             共用网页控制台
Start.ps1                        管理器入口
scripts/                         管理器启动与Rust构建
games/codol/versions.json        持续维护的版本列表
games/codol/versions/v3_3_3_3/
   adapter.py                    本版本控制接口
   client/                       本版本启动检查
   server/                       Python认证、大厅、档案与对局编排
     native/match-server/        本版本Rust模拟对局服
   resources/definitions/        商城、赛单、快照字段
   reverse/tools/                资源解析、逆向探针、冻结的Python对照实现
   reverse/recovered-code/       已恢复的客户端逻辑及证据
   reverse/experiments/          本版本历史实验脚本与探针
   scripts/                      本版本游戏及模拟服务器启停
   tests/                        本版本测试与受控样本
games/codol/versions/v3_19_26_22/
   adapter.py                    3.19启动入口和能力范围
   client/                       隔离副本、加载器与进程管理
   server/                       3.19认证、大厅、档案和资源服务
   reverse/                      来源与REA证据索引
   scripts/                      3.19启停脚本
   tests/                        3.19准备、隔离、服务与启动测试
config/                          本机所选目录与运行会话，不提交
runtime/instances/<实例ID>/       档案、备份、证书、日志、抓包，不提交
runtime/builds/codol/v3_3_3_3/     本版本Rust产物与地图包，不提交
runtime/instances/*/generated/    本实例从原游戏生成的资源与校验记录，不提交
tests/                           管理器接口与启动测试
docs/                            管理器说明、版本Wiki、历史报告
research/                        历史原始证据、参考资料与实验产物
archive/                         历史基线
```

[文档入口](docs/README.md) · [技术 Wiki 总览](docs/wiki/README.md) · [搬迁清单与校验值](docs/reports/20261014-directory-migration.json)

当前公开角色档案位于 `runtime/instances/<实例ID>/data/public-profiles/`，服务日志位于同一实例的 `logs/server.jsonl`。原 `runtime/data/` 保留为迁移来源，不再承接新进度。研究 JSON、历史归档和旧搬迁清单保留生成时原文；当前源码位置以本页目录为准。外部参考源码的来源清单和许可证归属保留在研究目录。

## 游戏目录例外（3.3.3.3）

客户端必须就地读取 `dwauth.ini`、`stun.ini`、`cacert.pem`，所以这三项仍在游戏目录。证书文件保留原 CA 并追加本实例 CA；首次配置备份位于 `runtime/instances/<实例>/backups/client-config/`。游戏 EXE 未修改，系统根证书、hosts、防火墙未修改。游戏自身产生的日志仍由游戏写入原目录。

---

<a id="english"></a>
# CODOL Multi-Version Manager

[中文](#chinese) · **English**

Select a local game directory in the web console; the manager automatically verifies version files and main-program fingerprints, then invokes the reverse-engineered implementation and simulated servers for the matched version. Currently integrated: **3.3.3.3**, plus **3.19.26.22 startup, local lobby, and the Seatown test match**; 2.6.9.7 is catalogued only. The version list is [games/codol/versions.json](games/codol/versions.json); rules for adding new versions are in the [multi-version manager guide](docs/multi-version-manager.md).

## Current Progress

**2026-10-17 Rebuildable 3.19 delivery**: Startup and the Seatown match no longer depend on the external launch package. The repository source builds the proxy, the loopback bridge, the collision program, and the IFS reader; release files and English-language assets are generated from the matched original game, and the item/loadout tables plus the current map are exported read-only from our own game process. First-run preparation still uses an isolated copy and preserves existing progress. First deployment requires Python dependencies, an x86 MinGW GCC, and the original game; see the [3.19 integration guide](docs/wiki/v3_19_26_22-startup.md). This round completed build, resource, and protocol verification; lobby access and play after starting the full new component set still await manual acceptance, and earlier on-machine results from the old components do not count as acceptance for this round.

**2026-10-16 Multi-version manager**: Directory selection, version-file and EXE fingerprint matching, operation gating, and version adapters are integrated; reverse-engineering tools, simulated servers, and tests are stored per version, and player data is isolated per installation instance. Recognition of a real 3.3.3.3 directory, save-copy verification, and simulated-server start/stop have been verified; browser screenshots of the new web sections and the native directory dialog still await manual confirmation, and the in-game acceptance scope is unchanged.

**2026-10-16 Rust standalone match server**: Collision, movement, AI, and the UDP protocol have been moved into a standalone Rust process; Python keeps the web console, authentication, lobby, and profiles, and the existing start/stop flow is wired in and reloaded. With identical input over 400 Nuketown frames, whole-frame P99 dropped from 91.60 ms to 1.62 ms, with state consistent within the agreed tolerance; this is an offline performance result — game feel for the Rust version awaits manual acceptance. Entry is still via "Team Deathmatch → Nuketown" with one human player, one AI, a fixed ACR, and free-for-all rules; no new playlists. Build steps, evidence, and acceptance are in the [Rust migration wiki](docs/wiki/12-rust-match-server.md). 9v9 and other modes are not integrated.

2026-10-14 12:40: actually entered the game lobby; at 13:03, after reorganizing directories and restarting the game and services, verified again successfully, showing the user's second selected character "Marcus" and nickname johnClient. The combined fix includes command-line bootstrap overrides and local public-profile loading; see [Onboarding & Character Profile](docs/wiki/06-onboarding-profile.md). Training and the original campaign remain unrestored.

Verified chain: TLS authentication → encrypted lobby via protocol 210 → publish files → public-profile loading → game lobby. The server implements public-profile save/load; 21 unit and in-memory protocol tests pass. The first lobby verification used the raw profile captured during character selection; acceptance of saves made later by the real client is recorded separately, and passing tests is not treated as full game-data persistence.

The web controller supports onboarding toggles, launching the game, reading the dev wiki, level 70 with 3 prestiges, and adding game coins and premium points separately. Marketplace level restrictions are lifted; M14 EBR purchase debiting, permanent inventory, and persistence across relogin are confirmed, and premium-point display plus purchase debiting/crediting are also tested on the real client. Full-catalog granting of 6,772 items, max weapon XP for 201 weapons, and manual renewals were added; 44 tests and the frontend build pass. Browser operations are verified; the user confirmed that after relogin permanent items, maxed weapons, attachments, and skins equip correctly, with premium points still at 99,620. See [Player Data & Marketplace](docs/wiki/08-player-progression-marketplace.md) and [Premium Points & Full Inventory](docs/wiki/09-inventory-completion.md). Duplicate stacking is out of scope for this round; the resolution task was cancelled per the user's request.

## Usage

Open PowerShell in this directory:

```powershell
.\Start.ps1
```

[Start.ps1](Start.ps1) first checks and starts the web controller, then opens <http://127.0.0.1:8765/>. On first open, click "Select game directory"; once a version matches, the operations it supports are enabled. An existing selection is re-verified after restart; the default entry launches the matched game. Launching the game still requires Windows UAC confirmation.

```powershell
.\Start.ps1 -CheckOnly            # check the manager environment only
.\Start.ps1 -NoGame               # open the web console; the user launches the game
.\Start.ps1 -NoGame -NoBrowser    # start only the background web controller
python -B tools/run-tests.py      # run manager and version tests once
python -B tools/check-doc-links.py
```

The game and the simulated servers start and stop together through the web console. Scripts inside a version directory are invoked by the manager with the installation path and instance directory. For detailed checks see the [controller documentation](docs/controller.md). Python dependencies are in [requirements.txt](requirements.txt); development conventions are in [CONTRIBUTING](CONTRIBUTING.md).

After the first run, or after modifying Rust sources, run `powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 build --release` from the repository root. Toolchains and build artifacts live under the project's `runtime/`; running the built match server needs no ad-hoc compilation. A missing Rust artifact never falls back to the Python match implementation.

On first start of the 3.3.3.3 services, the Nuketown package is generated from the selected game and saved to
`runtime/builds/codol/v3_3_3_3/maps/nuketown/`. That directory holds local build artifacts and is not delivered via Git;
the 235-point reference navigation mesh and the version-registered definitions ship with the repository, so the old server directory and the author's `research/` are no longer needed.
First-time extraction requires a MinGW GCC that supports 32-bit Windows targets; set `CODOL_IFS_CC` to the path of its `gcc.exe`.
You can also prepare manually first:

```powershell
$env:CODOL_IFS_CC = 'C:\toolchains\mingw32\bin\gcc.exe' # replace with your actual path; omit if it is already in PATH
powershell -NoProfile -ExecutionPolicy Bypass -File games/codol/versions/v3_3_3_3/scripts/Prepare-Resources.ps1 -GameRoot 'D:\YourGameDirectory'
```

Valid packages are reused; a failed extraction publishes nothing partial. A damaged package is reported with the specific error and kept — move it out of the directory above and retry.
The manual command above only generates the map. When 3.3 is started from the web console as usual, the manager first checks installed dependencies and build artifacts,
then generates the map, prepares this instance's certificates, and — after backing up — configures `dwauth.ini`, `stun.ini`, and `cacert.pem` in the game directory.
The original CA is preserved; repeated starts reuse valid maps and certificates; failures surface the specific reason in the web console.
On a new machine, first install the Python dependencies, build the frontend, and build the Rust match server per the [development environment](CONTRIBUTING.md);
first-time map extraction additionally needs the 32-bit MinGW toolchain above. You do not need to copy the author's `runtime/` or `research/`.
Backups, certificates, and recovery steps are in [Redirection & TLS Auth](docs/wiki/03-redirection-tls-auth.md).

## Directory Layout

```text
src/controller.py                shared controller HTTP entry
src/manager/                     version detection, installation selection, data migration, native directory picker
web/                             shared web console
Start.ps1                        manager entry point
scripts/                         manager startup and Rust builds
games/codol/versions.json        continuously maintained version list
games/codol/versions/v3_3_3_3/
   adapter.py                    version control interface
   client/                       launch checks for this version
   server/                       Python auth, lobby, profiles, and match orchestration
     native/match-server/        Rust simulated match server for this version
   resources/definitions/        marketplace, playlists, snapshot fields
   reverse/tools/                resource parsing, reverse probes, frozen Python reference implementation
   reverse/recovered-code/       recovered client logic and evidence
   reverse/experiments/          historical experiment scripts and probes for this version
   scripts/                      game and simulated-server start/stop for this version
   tests/                        tests and controlled samples for this version
games/codol/versions/v3_19_26_22/
   adapter.py                    3.19 launch entry and capability scope
   client/                       isolated copy, loader, and process management
   server/                       3.19 auth, lobby, profile, and asset services
   reverse/                      source and REA evidence index
   scripts/                      3.19 start/stop scripts
   tests/                        3.19 preparation, isolation, service, and startup tests
config/                          locally selected directories and run sessions; not committed
runtime/instances/<instance-id>/ profiles, backups, certificates, logs, captures; not committed
runtime/builds/codol/v3_3_3_3/     Rust artifacts and map packages for this version; not committed
runtime/instances/*/generated/    resources generated from the original game for this instance, with checksum records; not committed
tests/                           manager interface and startup tests
docs/                            manager guides, version wiki, historical reports
research/                        historical raw evidence, reference material, experiment artifacts
archive/                         historical baselines
```

[Documentation index](docs/README.md) · [Technical wiki overview](docs/wiki/README.md) · [Migration checklist & checksums](docs/reports/20261014-directory-migration.json)

Current public character profiles live in `runtime/instances/<instance-id>/data/public-profiles/`, and server logs in `logs/server.jsonl` under the same instance. The old `runtime/data/` is kept as a migration source and no longer receives new progress. Research JSON, historical archives, and the old migration checklist keep the text they were generated with; for current source locations follow the layout on this page. The source list and license attribution for external reference source stay in the research directory.

## Game-directory exceptions (3.3.3.3)

The client must read `dwauth.ini`, `stun.ini`, and `cacert.pem` in place, so these three files remain in the game directory. The certificate file keeps the original CA and appends this instance's CA; first-configuration backups are in `runtime/instances/<instance>/backups/client-config/`. The game EXE is not modified, and system root certificates, hosts, and firewall are untouched. Logs produced by the game itself are still written by the game into its original directory.
