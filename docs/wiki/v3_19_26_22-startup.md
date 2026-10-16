# 3.19.26.22 启动接入

本轮接入游戏副本准备、原生加载器调用、本地认证、大厅与资源服务。网页使用共用的目录选择和启动/停止按钮。等级、货币、库存编辑及对局尚未接入，不调用3.3.3.3的实现。

## 版本身份

本机游戏目录为 `E:\Games\3.19.26.22\CODOL_FINAL\CODOL_FINAL\使命召唤OL_final\使命召唤OL_final`，必须选择这一层包含EXE的目录。

| 标识 | 实测值 |
|---|---|
| TCLS/mmog_data.xml | 3.19.26.22 |
| IIPS/IIPSVersion.ini | V1.2.1.13 |
| EXE SHA256 | 36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537 |

[版本表](../../games/codol/versions.json)记录这组已核实的版本文件值，随后仍验证EXE指纹。未知组合、损坏文件和不匹配的EXE不放行。

## 目录与运行方式

```text
games/codol/versions/v3_19_26_22/
  adapter.py                  共用控制台的版本入口与能力范围
  client/preparation.py       包导入、游戏副本、文件准备
  client/lifecycle.py         自有进程、端口就绪与登录事件
  client/launch.py            管理员启动、会话状态与停止
  server/                    此版本的认证、大厅、档案和HTTP源码
  reverse/                   来源清单与REA证据索引
  scripts/                   管理器调用的PowerShell入口
  tests/                     此版本的准备、服务和启动测试
runtime/packages/codol-3.19.26.22/
  server/                    本地原生组件、资源、初始档案
  patches/                   提供方的英文资源补丁
runtime/instances/codol-3.19.26.22-<路径哈希>/
  game/                      独立游戏副本，约24GB
  game-copy.ready            完整复制成功后才创建
  server/                    本实例服务数据、原生组件及原生日志
  logs/                      本实例服务标准输出
  startup.json               进程身份、启动阶段和错误
```

原生组件复用用户提供的 `CODOL319-TestBuild`，未重新实现加载器。Python源码保留原有协议实现与来源说明，只把数据路径接到实例目录。原生文件、游戏资源、证书和玩家数据不提交Git。

首次部署先在仓库根导入本地启动包：

```powershell
python -B -m games.codol.versions.v3_19_26_22.client.preparation --launcher 'E:\Games\3.19.26.22\CODOL_FINAL\CODOL319-TestBuild' --package 'runtime/packages/codol-3.19.26.22'
.\Start.ps1 -NoGame
```

本机已完成导入。在网页选择上述游戏目录并点击启动，确认Windows UAC。首次创建副本需要额外约24GB；加载器使用ANSI路径，工具及运行目录须为较短的英文路径。再次启动使用同一副本，不重新导入档案。

副本内安装 `version.dll`、系统32位version代理、提供方英文资源和 `codol319-root.txt`；复制时排除Cross。原游戏和原启动包保持原内容。副本中的原资源保留 `.original` 备份。首次出现“Optimize Settings?”时由用户在游戏中确认；创建游戏进程即返回启动结果，后台继续记录大厅连接，不因用户等待此提示而关闭游戏。

## 启停与验收边界

- TCP31900：本地认证；TCP31901：加密大厅；TCP8319：资源HTTP。均绑定回环地址。
- 启动前检查全部端口，有冲突时不停止占用者；部分启动失败则清理本次创建的服务。
- 管理员监督进程持有加载器和服务，停止请求只结束所持进程及加载器子树。状态同时记录PID与进程创建时间，旧PID文件不算运行证明。
- 普通控制器与管理员游戏使用同一实例。实例目录显式授权当前用户继承访问权；既有管理员日志按文件权限处理，避免继承标志在文件上无效。
- `ready`表示三个自有服务端点就绪；`game_running`表示目标游戏进程存活；只有本轮启动时间之后的 `secure_profile_read` 才标记 `lobby_ready`。游戏菜单、移动和射击由用户验收。
- 服务档案在实例的 `server/profile319.json`、`server/local-profiles319/`；原始启动器里的档案不回写。首次复制带入提供包的初始数据，重复启动不覆盖本实例进度。

## 2026-10-16 验证记录

已通过真实目录识别、隔离复制、EXE校验和启动接口。修复Windows目录重命名失败后采用完整复制标记，补测中断恢复；修复跨权限状态文件读取后，新会话状态可被普通控制器读取。网页同一启动接口约6.2秒返回成功，真实游戏显示首次硬件优化确认框，三个自有端点就绪；停止接口成功释放端点。

当前未确认3.19大厅画面，也未验证对局。首次设置确认由用户操作，不能把端口或游戏进程出现当作大厅通过。

集中Python回归一次：352项、241.6秒，349项通过、1项跳过；两项失败均为此前已记录的3.3.3.3初始快照完整字典断言，本轮未修改这些实现或断言。后续首次提示等待和日志权限调整后，3.19专属15项及管理器API/启动9项全部通过。449个本地文档链接检查通过。原游戏2253个文件的大小和修改时间保持一致，移植的6份原启动包源码哈希保持一致。证据在本机 `work/codol319-startup/evidence/`。

启动器CodeGraph索引覆盖19个源码文件；游戏索引覆盖91个可解析文件，不包含EXE反编译。REA的原生加载器分析见[逆向记录](../../games/codol/versions/v3_19_26_22/reverse/README.md)。
