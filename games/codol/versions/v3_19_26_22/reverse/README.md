# 3.19 启动链路证据

2026-10-17可重建交付第一阶段：认证的Tiger常量改用带来源说明的仓库源码，私有档案读取仓库内版本定义；HTTP认证不再要求旧包中的证书和私钥。空实例的真实HTTP认证、已固定时间的票据、档案CRC/字段及进度保护已验证，26项相关测试通过。此阶段仅解除上述数据依赖，加载器、桥接及对局辅助程序仍待替换，不代表整个启动包已移除。

来源为用户提供的CODOL319-TestBuild；18份选择性移植Python文件的原始SHA256见[source-manifest.json](source-manifest.json)。保留提供包内的来源注释。服务数据根目录统一为 `CODOL319_SERVER_ROOT`，主启动和对局编排另行实现，未引入提供包按端口清理其他服务的行为。对局移植还包含正常停止、原生子进程清理和结算写入失败回滚；原始源码保持不变。

原生组件身份在 [preparation.py](../client/preparation.py) 的 `NATIVE_HASHES` 中固定；导入及执行前校验。原始二进制仅在被忽略的本地runtime包中保存。

对局使用的两个原生组件身份另固定于 [match.py](../client/match.py)：`collision319.exe`、`snapshot319_live.exe`。迁入的 [match_host](../server/match_host/) 调用这些组件处理本版本的碰撞和快照，没有混入3.3.3.3地址。原生快照、配装读取及碰撞进程生命周期已通过离线测试；游戏内效果仍需人工验收。

2026-10-17 NCS阶段：运行时配置表改由仓库Python算法重建，移除 `test_native_ncs319.exe`、`config-reader-relocated.bin` 和旧rdata转储依赖。23项范围定义直接从原版客户端 `0x00da9808` 提取，来源与客户端SHA256见 [ncs319.json](../resources/definitions/ncs319.json)。[固定对照样本](../tests/fixtures/ncs319-reference.json) 保存旧原生程序的校验值、注册表摘要和地图消息摘要；测试覆盖跨列表去重、列表内重复、排序、跳过类型及不完整采集拒绝。删除这三个旧文件的真实服务启动与相关用例共8项通过；客户端自身的地图校验继续生效。

REA / Ghidra 12.1.4 对加载器 `Client-english-fixed-resources.exe` 的证据：

- SHA256：`bd89f07fd634498f37be10c420915ba0581c6cdd661b8567aecfaac809c70867`，PE x86。
- `0x4106bf`：字符串 `CODOL319_GAME_DIR`，交叉引用 `0x40412f`。
- `0x403fc0`：`_WinMain@16`读取该环境变量，使用260字节ANSI路径缓冲区和 `CreateProcessA`。
- `--local-lobby` 加入 `-s 127.0.0.1:31900`；`--windowed`选用1280×720窗口；`--local-http`与 `--english-resources` 对应提供包的启动参数。
- 游戏命令包含 `-q 1000001`；加载器等待其创建的游戏进程退出。运行时以实际子进程路径确认身份。

证据ID：`ev_db0cca2edd38412d90a3ba715c21d822e54b5daad4cc0a1ba261abcd32efd918`（引用），`ev_3e5c5747bfb338c2868f3ad95713577b13b156bd7bb0d4988d94c926acff457a`（WinMain反编译）。本机完整Evidence包在 `work/codol319-startup/evidence/rea-loader.json`。

REA会话已保存为同目录下的 `rea-loader.snapshot.json` 并关闭；包含3条证据及1项可复用工作流。恢复时以同一加载器和该快照调用 `open_binary`；新查询仍可能需要重新分析，缓存不代表整个Ghidra数据库已保存。

这些结论覆盖加载参数和进程入口，不代表所有原生补丁、认证协议或对局行为均已验证。游戏 EXE 的地址与3.3.3.3不同，没有搬用旧版补丁地址。

## 用户提供的图形启动器恢复源码

2026-10-16用户提供 `E:\Games\3.19.26.22\CODOL_FINAL\CODOL319-TestBuild\recovered-source\`，其中 `launcher-exe/Launcher.cs` 对应 `CODOL 3.19 Launcher.exe`。CodeGraph已可查询 `StartGame`（267行）；308至314行构造 `runtime/python/python.exe -B -X utf8 -u server/start319.py --gui --game ... --mode copy|inplace --name ... --fov ... --max-fps ...` 并重定向输出。该层负责界面、参数校验、设置保存和日志转发，共用网页及本版本启动编排已接管启动职责。

REA静态核验原EXE：20480字节，SHA256 `a3af8a5d79420757acb5f63978a589ecdca87029373e5266c884354c01371f11`，PE/CLI托管CIL，程序集版本 `3.19.26.22`。证据ID：`ev_a109d7d3436ae37f003e681e28608fde2e4cf5382904c898cdb6a1d52337e258`。此次读取现成恢复源码和程序集元数据，未重编译，也未验证恢复源码与原EXE的完整行为等价性。

提供目录的 `binary-source-map.md` 另列6个尚未恢复源码的原生组件，包括启动所用 `Client-english-fixed-resources.exe`、`version.dll` 和 `client_loopback319.dll`。上述C#源码不能替代这些组件；本轮保留已通过大厅人工验收的启动方式，后续原生迁移分别以对应二进制证据为准。第三方恢复源码保留在原目录，未整包复制或提交。
