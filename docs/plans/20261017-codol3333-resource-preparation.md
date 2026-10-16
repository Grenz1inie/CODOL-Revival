# 3.3.3.3 核弹小镇资源准备修复方案

2026-10-17。当前完成探索、范围界定及交付决策；资源准备功能尚未实施。

## 目标与修复范围

已有项目运行依赖环境及匹配的完整 3.3.3.3 客户端时，新环境应能使用仓库提供的入口完成核弹小镇服务端地图包准备，不需要作者本机的 `research/`、既有 `runtime/` 或仓库外的旧服目录。

保留当前包格式、FF423 签名和哈希检查、NCS 校验、手模54、现有 Rust 对局协议和一名真人加一个AI的 DM 行为。本轮处理资源输入、准备、部署及启动诊断，不开发更多地图或导航算法；不接入正在进行的3.19工作，不覆盖现有完整包或玩家数据。Python、前端和Rust构建依赖继续作为明确的运行/构建前提，不将本轮扩展为完整安装器或发行系统。

## 已核实的断点

- `extract_story_resources.py` 固定使用相邻游戏目录及 `research/.../ifs-read.exe`；地图导出还复制本机已有公共FF。
- `build_match_registration.py` 依赖本机 `live-netconst-registration423.json`。该文件包含运行时采集信息，不能原样作为新环境输入。
- 地图和装备导出复用现有算法，但输出限制在历史实验目录，且装备导出另需已经解码的 `common_mp`。
- AI路网来自仓库外的旧服参考包。用户已确认改变其交付方式，见[ADR](../adr/0001-codol3333-navigation-input.md)。来源核验仍是实施责任，不向用户索取可在现有资料中查到的事实。
- 服务固定读取 `runtime/builds/codol/v3_3_3_3/maps/nuketown/`。启动链没有资源准备调用，版本预检也没有校验该包。
- 现有导出测试使用本机中间产物，部分缺失时跳过，不能证明新环境能够完成准备。
- 新安装的证书及客户端地址配置另有手工步骤；地图包修复完成不自动代表这些前提已经满足，须在预检和文档中明确区分。

## 图辅助探索

CodeGraph 检查结果为最新。GitNexus 原索引落后23个提交，已通过 `gitnexus analyze --index-only --workers 2` 更新；完成后磁盘索引记录的提交与当时 HEAD `526e9dc` 一致。MCP 的新鲜度元数据仍缓存旧值，因此另外通过CLI核对并执行影响分析。

调用链为 `controller.command → Control-Game.ps1 → client/checks.py → Control-Services.ps1 → Start-Services.ps1 → local_server.py → load_matchmaking → NativeMatchProcess`。PowerShell与Python跨进程边界已核对实际源码，不能只凭图中没有调用边断言不存在依赖。

GitNexus 对 `export_loadout` 的两层上游分析报告4个受影响符号、3个直接使用点、LOW；该结论只适用于此符号，不能替代整个首次准备流程的验收。

## 拟影响文件

下列版本相对路径均位于 `games/codol/versions/v3_3_3_3/`。新增文件名为当前拟定名，实施时以最小职责划分为准。

| 文件 | 开发职责 |
|---|---|
| `client/preparation.py`（新增） | 接收显式游戏/项目目录，组织提取、解码、注册表、碰撞和装备导出；校验后发布到正式包目录，重复运行复用有效产物，失败不发布半成品 |
| `scripts/Prepare-Resources.ps1`（新增） | 明确的准备入口；使用指定解释器和已配置的匹配架构C工具链构建IFS读取器，缺工具时报出可执行的准备说明，不使用作者盘符 |
| `reverse/tools/extract_story_resources.py` | 允许显式输入目录和提取器路径；从游戏归档收集全部必需FF，保留旧实验调用边界 |
| `reverse/tools/build_match_registration.py` | 支持经过验证的版本注册定义；不以作者本机采集JSON作为必需输入 |
| `reverse/tools/export_match_map.py`、`export_match_loadout.py` | 允许受调用方限定的新准备目录，复用现有解析及完整性校验；在新流程内生成所需common模型输入 |
| `resources/definitions/network-registration423.json`（拟新增） | 整理与当前EXE哈希绑定的最小注册定义，记录采集来源，保留名称顺序及CRC验证；不携带PID或机器路径 |
| `resources/navigation/mp_nuked_wp.csv`及来源说明（拟新增） | 核清来源后纳入235点参考路网及哈希；大体积游戏资源仍保持本地生成 |
| `client/checks.py` | 只读核对包完整性、构建产物及准备前提，区分资源缺失、损坏、版本错误和其他启动前提 |
| `scripts/Control-Game.ps1`、`Control-Services.ps1` | 在相应启动动作前衔接准备/检查；状态查询保持只读，准备失败时返回具体原因，不继续等待对局端口 |
| `adapter.py` | 仅在实际准备耗时证实有需要时调整本版本命令超时；不全局放宽其他版本 |
| `tests/test_resource_preparation.py`（新增）、现有导出/启动测试 | 新环境输入、中文/空格路径、缺包与损坏、重复准备、失败后重试、旧调用和原游戏不变 |

共用文件限于实际需要的依赖说明和文档：`requirements.txt`（若首次准备需要引入pefile等依赖）、`README.md`、`CONTRIBUTING.md`、`docs/wiki/11-independent-match-server.md`、`docs/wiki/12-rust-match-server.md`。实施时同步 `AGENTS.md` 和 `reverse/tools/reference_match/NOTICE.md` 中对路网交付方式的旧描述。新入口可能需要的最小编译辅助逻辑优先放在上述准备脚本，不新增通用构建框架。

不改共用HTTP响应、现有网页布局、Rust移动/AI算法或对局协议；若实现中发现这些边界无法保持，应先说明具体原因再调整方案。

## 开发顺序与验证

1. 先建立缺少本机研究目录时的失败用例；整理可跟踪的注册定义和路网来源。注册定义须与现有原生消费者回归一致，不靠直接写死最终校验和绕过验证。
2. 实现完整资源准备入口，复用IFS读取、FF解码和现有导出器。必需输入全部来自选定游戏及仓库内已核实的定义/参考路网，不读取作者的历史中间包。
3. 接入启动与只读预检。对已有有效包不重复生成；准备中断不覆盖有效包；包与版本不匹配时明确报错。
4. 在独立测试目录用仓库文件及匹配原游戏验证：初始无 `research/` 和运行时资源；完成准备后验证manifest全部大小/哈希、NCS及装备编号，并实际通过Rust包加载/短生命周期就绪。用第二次准备验证复用，定向回归验证原行为。
5. 核对原游戏资源及现有正式包未被更改，更新新环境使用说明。证书、地址配置、Python和Rust前提分别报告；游戏画面与操作继续由用户人工验收，不以资源生成或端口就绪代替。

## 当前决策

唯一需要用户参与的交付决策已回答：同意235点路网核清来源后随仓库交付。当前没有其他需要用户决定的关键缺口；来源、注册定义和工具构建可复现性的具体核验属于实施工作，不视为已验证完成。
