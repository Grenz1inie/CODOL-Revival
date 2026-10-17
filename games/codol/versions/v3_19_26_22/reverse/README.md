# 3.19 启动链路证据

2026-10-17可重建交付：生产启动已移除旧包依赖。输入为仓库源码、匹配原游戏、Python依赖和公开x86 MinGW工具链。认证Tiger常量、私有档案定义、快照字段和NCS范围均有版本来源；启动资源从原归档生成，运行时数据从已核验的自有客户端只读导出。新部署步骤与实机验收边界见[启动说明](../../../../../docs/wiki/v3_19_26_22-startup.md)。

来源为用户提供的CODOL319-TestBuild；18份选择性移植Python文件的原始SHA256见[source-manifest.json](source-manifest.json)。保留提供包内的来源注释。服务数据根目录统一为 `CODOL319_SERVER_ROOT`，主启动和对局编排另行实现，未引入提供包按端口清理其他服务的行为。对局移植还包含正常停止、原生子进程清理和结算写入失败回滚；原始源码保持不变。

源码及生成路径：

| 旧输入 | 生产替代 |
| --- | --- |
| `Client-english-fixed-resources.exe` | [loader.py](../client/loader.py)：创建自有客户端、命名映射、原字节验证后的内存配置 |
| `version.dll`、`client_loopback319.dll` | [native/](../client/native/)：版本代理、主线程回环、资源注册采集；由[native_build.py](../client/native_build.py)构建和校验 |
| `collision319.exe` | 同目录`collision.cpp`；刷子/三角形、胶囊及翻越碰撞，受控几何与140条Seatown原生对照轨迹一致 |
| `snapshot319_live.exe`、`test_native_ncs319.exe`及旧转储 | [snapshot_codec319.py](../server/match_host/snapshot_codec319.py)、[reconstruct_ncs319.py](../server/match_host/reconstruct_ncs319.py)与仓库字段定义 |
| 英文IFS、发布文件 | [boot_assets.py](../client/boot_assets.py)：原游戏IFS2与源码IFS读取器提取；[英文来源](../resources/english/README.md)、[配置来源](../resources/publisher/README.md) |
| 物品、SKU、武器、配装、地图及梯子 | [resource_export.py](../client/resource_export.py)：PID/创建时间/路径/EXE指纹校验，`OpenProcess(0x410)`只读提取，完整发布后写标记 |

构建记录包含源码和输出哈希；旧包二进制指纹不再是生产依赖。IFS读取器复用仓库中已有源码，因为3.3和3.19原游戏的`IFS2.dll`哈希相同；没有复用3.3的游戏地址或注册编号。Ghidra 12.1.4和Capstone辅助确认3.19原生消费者：无签名FF只解密首个256KiB读取块，IFS尾部为16KiB块MD5表及表摘要。重建完整英文归档与原有效补丁逐字节一致，SHA256见英文来源文档。

公共DDL包含字节偏移和位偏移。导出只验证所消费的配装字段及其宽度，不能将其他位字段当作越界字节偏移；真实v233表已用于复现并建立回归。地图数据在客户端完成加载后提取，错误地图和部分读取不会生成可用地图；提取失败先于首帧发送。

2026-10-17加载器阶段：[loader.py](../client/loader.py) 替代旧 `Client-english-fixed-resources.exe`，生产入口直接运行仓库Python源码。按下述反编译证据生成TCLS共享内存，等待原客户端解包后，仅在原字节匹配时配置HTTP认证、关闭远程NAT探测并隔离UDP端口；英文分支保留原有资源入口选择。读取与写入限于新建的游戏子进程，文件EXE不变。18项准备/启停/协议测试通过，另一个受控32位子进程实际消费命名映射并验证三处修改、页面保护恢复和磁盘EXE不变（6.99秒）。这不替代真实客户端大厅和对局验收；代理、桥接和资产生成仍在后续阶段。

以下分阶段记录描述当时进度；最终生产依赖以上表为准。已有组件的人工游戏验收不能代替源码替换后的整套启动验收。

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

提供目录的`binary-source-map.md`当时列出6个缺源码的原生组件；上述C#源码只对应图形启动器。2026-10-17按上表恢复或替代这些组件需要的行为，未将现成二进制随仓库分发。第三方恢复源码保留在原目录，未整包复制或提交。
