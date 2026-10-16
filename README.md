# CODOL 多版本管理器

在网页中选择本机游戏目录，自动核验版本文件与主程序指纹，再调用对应版本的逆向实现和模拟服务器。当前接入 **3.3.3.3**，以及 **3.19.26.22的启动、本地大厅和Seatown测试对局**；2.6.9.7仅收录。版本列表是 [games/codol/versions.json](games/codol/versions.json)，新增版本的规则见 [多版本管理说明](docs/multi-version-manager.md)。

## 当前进度

**2026-10-16 3.19工具迁移**：独立代码、模拟服务和游戏副本已接入共用控制台。继续迁入昵称/FOV/帧率设置，以及Ready触发的Seatown对局、配装读取和退出结算；保持单人、无AI、每次启动一场的原工具范围。新增回归、前端32项测试及构建通过；实机已进入地图，用户确认基础可用并要求暂缓细节问题。退出重登后的奖励仍未实测。复用提供包的原生组件，本机原游戏未修改。导入、目录及证据见 [3.19接入说明](docs/wiki/v3_19_26_22-startup.md)。

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
runtime/packages/codol-3.19.26.22/ 本地导入的3.19原生组件及资源，不提交
tests/                           管理器接口与启动测试
docs/                            管理器说明、版本Wiki、历史报告
research/                        历史原始证据、参考资料与实验产物
archive/                         历史基线
```

[文档入口](docs/README.md) · [技术 Wiki 总览](docs/wiki/README.md) · [搬迁清单与校验值](docs/reports/20261014-directory-migration.json)

当前公开角色档案位于 `runtime/instances/<实例ID>/data/public-profiles/`，服务日志位于同一实例的 `logs/server.jsonl`。原 `runtime/data/` 保留为迁移来源，不再承接新进度。研究 JSON、历史归档和旧搬迁清单保留生成时原文；当前源码位置以本页目录为准。外部参考源码的来源清单和许可证归属保留在研究目录。

## 游戏目录例外（3.3.3.3）

客户端必须就地读取 `dwauth.ini`、`stun.ini`、`cacert.pem`，所以这三项仍在游戏目录。证书文件保留原 CA 并追加本实例 CA；首次配置备份位于 `runtime/instances/<实例>/backups/client-config/`。游戏 EXE 未修改，系统根证书、hosts、防火墙未修改。游戏自身产生的日志仍由游戏写入原目录。
