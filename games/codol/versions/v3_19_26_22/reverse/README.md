# 3.19 启动链路证据

来源为用户提供的CODOL319-TestBuild；六份移植Python文件的原始SHA256见[source-manifest.json](source-manifest.json)。保留提供包内的来源注释。仅调整服务数据根目录为 `CODOL319_SERVER_ROOT`，主启动编排另行实现，未引入提供包按端口清理其他服务的行为。

原生组件身份在 [preparation.py](../client/preparation.py) 的 `NATIVE_HASHES` 中固定；导入及执行前校验。原始二进制仅在被忽略的本地runtime包中保存。

REA / Ghidra 12.1.4 对加载器 `Client-english-fixed-resources.exe` 的证据：

- SHA256：`bd89f07fd634498f37be10c420915ba0581c6cdd661b8567aecfaac809c70867`，PE x86。
- `0x4106bf`：字符串 `CODOL319_GAME_DIR`，交叉引用 `0x40412f`。
- `0x403fc0`：`_WinMain@16`读取该环境变量，使用260字节ANSI路径缓冲区和 `CreateProcessA`。
- `--local-lobby` 加入 `-s 127.0.0.1:31900`；`--windowed`选用1280×720窗口；`--local-http`与 `--english-resources` 对应提供包的启动参数。
- 游戏命令包含 `-q 1000001`；加载器等待其创建的游戏进程退出。运行时以实际子进程路径确认身份。

证据ID：`ev_db0cca2edd38412d90a3ba715c21d822e54b5daad4cc0a1ba261abcd32efd918`（引用），`ev_3e5c5747bfb338c2868f3ad95713577b13b156bd7bb0d4988d94c926acff457a`（WinMain反编译）。本机完整Evidence包在 `work/codol319-startup/evidence/rea-loader.json`。

REA会话已保存为同目录下的 `rea-loader.snapshot.json` 并关闭；包含3条证据及1项可复用工作流。恢复时以同一加载器和该快照调用 `open_binary`；新查询仍可能需要重新分析，缓存不代表整个Ghidra数据库已保存。

这些结论覆盖加载参数和进程入口，不代表所有原生补丁、认证协议或对局行为均已验证。游戏 EXE 的地址与3.3.3.3不同，没有搬用旧版补丁地址。
