# CODOL 3.3.3.3 本地复活

面向本机客户端的认证、大厅和公开角色档案协议原型。新增文件集中在本目录，游戏客户端位于相邻的 `CODOL_Experience_V3.3.3.3_FULL.7z/`。

## 当前进度

**2026-10-16 Rust独立对局服**：碰撞、移动、AI和UDP协议已迁入独立Rust进程，Python保留网页、认证、大厅和档案，现有启停流程已接入并重载。核弹小镇同输入400帧的整帧P99由91.60ms降至1.62ms，状态在约定精度内一致；这是离线性能结果，Rust版游戏手感待人工验收。仍从“冲锋团队竞技 → 核弹小镇”进入，一名真人、一个AI、固定ACR、自由混战，不新增赛单。构建、证据与验收步骤见 [Rust迁移 Wiki](docs/wiki/12-rust-match-server.md)。9V9等其他玩法未接入。

2026-10-14 12:40 已实际进入游戏大厅，13:03在整理目录并重新启动游戏、服务后再次验证成功，显示用户选择的第二个角色“马库斯”和昵称 johnClient。组合修复包括命令行引导覆盖及本地公开档案读取，详情见 [新手引导与角色资料](docs/wiki/06-onboarding-profile.md)。训练和原版剧情仍未恢复。

已验证：TLS 认证 → 协议210加密大厅 → 发布文件 → 公开档案读取 → 游戏大厅。服务端实现了公开档案保存/读取，21项单元及内存协议测试通过。初次大厅验证使用选角时抓到的原始档案；真实客户端后续修改的保存验收单独记录，不把测试通过当作全部游戏数据持久化完成。

Web 控制器支持引导开关、启动游戏、读取开发 Wiki、3 转生 70 级及分别增加游戏币和点券。商城等级限制已解除；M14 EBR 购买扣款、永久入库和重登保持已确认，点券显示及购买扣款入库也已实测。新增全目录 6772 种物品发放、201 把武器满级经验和手动续期；44 项测试及前端构建通过。浏览器操作已验证，用户确认重登后永久物品、武器满级、配件及皮肤装备正常，点券仍为 99620。详见 [玩家数据与商城](docs/wiki/08-player-progression-marketplace.md)、[点券与全物品](docs/wiki/09-inventory-completion.md)。重复叠加不在本轮实现范围；分辨率任务已按用户要求取消。

## 使用

在本目录打开 PowerShell：

```powershell
.\Start.ps1
```

[Start.ps1](Start.ps1) 先检查环境，再依次启动本地认证/大厅/STUN 服务、Web 控制器，打开 <http://127.0.0.1:8765/> 并启动游戏。游戏提权仍需确认 Windows UAC；已运行的服务和游戏会复用。首次环境准备、参数和排错见 [控制器文档](docs/controller.md)。

```powershell
.\Start.ps1 -CheckOnly            # 只检查，不启动或修改配置
.\Start.ps1 -NoGame               # 启动服务并打开控制器，暂不进入游戏
.\Start.ps1 -NoGame -NoBrowser    # 只启动后台服务和控制器
```

如果系统阻止执行脚本，可使用 `powershell -NoProfile -ExecutionPolicy Bypass -File .\Start.ps1`，仅对本次进程生效。单独的启停入口仍可使用：

```powershell
.\scripts\Launch-Game.ps1
.\scripts\Stop-Game.ps1
```

启动入口先启动本地服务，再请求管理员身份运行游戏；Windows UAC 由操作者确认。停止脚本只匹配相邻游戏目录的完整 EXE 路径。

```powershell
.\scripts\Start-Services.ps1
.\scripts\Stop-Services.ps1
python -B -m unittest discover -s tests -v
python -B tools/check-doc-links.py
```

Python 依赖见 [requirements.txt](requirements.txt)。启动脚本优先使用 `.venv`，否则使用 PATH；也可给 `Start-Services.ps1` 传 `-PythonPath`。新环境安装、协作和验收规则见 [CONTRIBUTING](CONTRIBUTING.md)。本机已有依赖和本地证书，整理目录没有重新安装依赖或替换证书。

首次运行或修改Rust源码后，在根目录运行 `powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 build --release`。工具链和构建产物位于项目`runtime/`；运行已构建的对局服不需要临时编译。缺少Rust产物不会回退到Python对局实现。

## 目录

```text
src/                         认证、大厅、档案、货币与控制器 HTTP 服务
native/match-server/          Rust对局服、协议、碰撞、移动与AI
data/                        有来源哈希的商城静态目录，不参与代码索引
web/                         控制器前端源码、构建配置与依赖锁文件
scripts/                     游戏和服务的启动/停止入口
Start.ps1                    一键预检查、启动服务、控制器和游戏
tests/fixtures/               独立测试及受控样本
tools/                       REA、证书、文档校验工具
  reference_match/           冻结的Python离线对照与资源导出依赖
docs/wiki/                   按游戏流程组织的技术 Wiki
docs/reports/                带日期的验证、目录搬迁记录
research/evidence/           本机反编译、快照、原始档案样本
research/reference-protocol/ 外部协议资料、来源与许可证
runtime/                     不进入版本控制的本机运行文件
  captures/ logs/ certs/ data/ backups/
archive/                     保留原始内容的历史基线
```

[文档入口](docs/README.md) · [技术 Wiki 总览](docs/wiki/README.md) · [搬迁清单与校验值](docs/reports/20261014-directory-migration.json)

`runtime/data/public-profiles/` 保存公开角色档案；`runtime/logs/server.jsonl` 记录服务事件。研究 JSON 和历史归档中的绝对路径保留生成时原文，查找新位置使用搬迁清单。外部参考源码不作为本项目源码参与测试，其来源清单和许可证归属保留在研究目录。

## 游戏目录例外

客户端必须就地读取 `dwauth.ini`、`stun.ini`、`cacert.pem`，所以这三项仍在游戏目录。证书文件保留原 CA 并追加本地 CA；对应原始配置位于 `runtime/backups/`。游戏 EXE 未修改，系统根证书、hosts、防火墙未修改。游戏自身产生的日志仍由游戏写入原目录。
