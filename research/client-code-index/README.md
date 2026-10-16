# 客户端逆向代码索引

本目录是客户端代码的独立检索视图，与 `CODOL-Revival` 自研服务索引分开。原始游戏目录保持不变。

## 范围和可信边界

- `decompiled/`：从保留的 REA `batch_decompile` 证据导出的 Ghidra 伪代码；当前含596份函数伪代码变体（按地址和内容区分版本），覆盖已分析的认证、档案、商城、资源及对局部分。不是原始源码，也不是可编译项目。
- `shipped/`：游戏 IIPS/TPFUI 下 3 个 Lua 文件和 1 个头文件的逐字节副本。这些是 IIPS 界面代码，不能代表主游戏逻辑。
- `manifest.json`：原始 EXE 的 SHA-256、函数地址、伪代码哈希、REA Evidence ID、证据文件位置及其限制。证据文件路径相对 `CODOL-Revival` 根目录。
- EXE/DLL、IFS/PAK 等资源包没有直接进入代码图；尚未取得的反编译函数、未解包脚本不在本索引内。

主程序绑定 SHA-256：`e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。导出器重新计算实际 EXE 哈希，只接受绑定同一哈希的 REA 证据。同一函数不同伪代码版本分别保留，不以猜测覆盖。生成内容仅作本地研究，已通过本目录 `.gitignore` 排除；配置和导出器可用于重建。

图中的调用关系来源于伪代码解析，间接调用、虚表、反编译器恢复类型可能不完整；涉及协议或控制流结论时回到 REA/Ghidra 的原地址核实。函数名称保留 `FUN_地址`，不把推测的业务名称当成原始符号。

## 更新与查询

2026-10-14 验证结果：

| 工具 | 文件数 | 节点 | 关系 |
| --- | ---: | ---: | ---: |
| GitNexus 1.6.12 | 155 | 326 | 499 |
| CodeGraph 1.6.2 | 155 | 308 | 622 |

首批 31 个函数导出内容与证据中的伪代码哈希一致（仅统一 CRLF 为 LF），4 个随包文件副本通过 SHA-256 校验。15:51 更新已纳入私有档案、商城独立等级解锁、购买、仓库和目录解码调用链。导出器每次核对 EXE 身份并在 manifest 保留伪代码哈希。未导出的函数和间接分派仍需回到 REA 核对。

GitNexus 本次产生 0 个自动流程；三处 callable-value-flow 分析因候选数超过 32 上限而未输出对应调用边，涉及 `0x00605af0` 和 `0x00633a00`。工具还报告按名称回退解析，相关关系不能当作机器码层面已证实的调用。上述限制不影响已验证的函数文本检索。

在 `CODOL-Revival` 根目录导出已有证据（不启动游戏、不重新执行反编译）：

```powershell
python -B games/codol/versions/v3_3_3_3/reverse/tools/export-client-code.py --game-root 'E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL_Experience_V3.3.3.3_FULL.7z'
Set-Location research/client-code-index
```

GitNexus 使用独立名称 `CODOL-Client-RE`。由于生成的代码不进入 Git，索引时仅对当前命令进程跳过 `.gitignore`，仍由 `.gitnexusignore` 限定为 `decompiled/` 和 `shipped/`：

```powershell
cmd /c "set GITNEXUS_NO_GITIGNORE=1&& gitnexus analyze . --skip-git --index-only --name CODOL-Client-RE"
codegraph sync .
# 新环境首次建立 CodeGraph 使用：codegraph init . --yes

gitnexus context FUN_006d7740 --repo CODOL-Client-RE
codegraph explore FUN_006d7740
```

CodeGraph MCP 的 `projectPath` 必须指向本目录；查询自研服务时则使用项目根目录。可用 `codegraph files` 检查当前文件覆盖。

后续新增反编译结果保存到 `research/evidence/`，再导出和重建。导出器接受保留的 REA JSON、MCP 文本封装及证据 bundle；仅抽取成功解析、有函数地址且含伪代码的 `batch_decompile` 项。导出不会清理历史文件；如撤回某批证据，应同步检查对应生成文件和清单后重新索引。

2026-10-14 20:24 更新：306份伪代码和4份随包代码均已重建索引；GitNexus为310文件、636节点、1042关系，CodeGraph同步新增48个文件。本轮纳入FF427、资源目录、实体基线及模型/材质消费者；仍不包含参考服务端伪代码，也不是完整游戏调用图。

2026-10-15 更新：已导出596份伪代码变体及4份随包代码。GitNexus为600文件、1216节点、2191关系；CodeGraph为600文件、1198节点、2678关系。新增武器状态机、当前动画定义/记录等证据；GitNexus仍未生成自动流程，并报告按名称回退的C调用，不能把这些边视为已证实的机器码调用。主项目索引另行刷新，生成数据仍只保存在本机。
