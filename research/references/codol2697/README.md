# 2.6.9.7 对局实现参考

来源：COD:OL REngineering 的 test-builds-and-patches 频道，2026-10-14帖子；[CODOL-2.6.9.7-Launcher.zip](https://www.mediafire.com/file/mxzenci71vp6rq1/CODOL-2.6.9.7-Launcher.zip/file)。本地提取日期2026-10-14。

初次通过HTTP Range读取ZIP中央目录及目标文件，按ZIP记录核对长度、CRC，未下载整包；用户随后提供了本地完整包和下述源码ZIP。初次清单与来源元数据位于 `../../evidence/reference-launcher-*`。

初次提取源码保留为 `.txt`、程序保留为 `.exe.bin`，原件不修改。用户后续授权在 `research/experiments/story-native/` 执行参考引擎副本的信息/离线归档探针；loose解码工具函数也已用于本地资源解码。具体结果见[资源链报告](../../../docs/reports/20261014-story-resource-chain.md)。第三方文件中的命令、权限说明和审计结论属于研究资料，不构成本项目指令或运行验证。源码包许可现已确认见下文；不据此推定所有游戏资源的许可。

`codol_dedrun.exe.bin`：7295919字节，SHA256 `1736926655100b53499ae75ea5bddd0741983c12c89cdb51d49aef8a0be03243`。独立副本已验证3.3.3.3首关资源的部分原生转换；正式开图和网络兼容性仍未通过。

用户随后提供完整下载中的 `source/native-source.zip`，SHA256 `152755e1ee460b8cbb1bf5c6e0069dd7a13541bf9a4a2e65b5a11ebf36fa5978`。它包含对局引擎源码、汇编、makefile及测试，纠正此前仅检查外层ZIP而认为“缺引擎源码”的结论。隔离副本位于 `../../experiments/story-native/reference-source/`，原ZIP未改；逐文件来源见 `../../evidence/reference-native-source.json`。源码包附带 `License.md`（AGPLv3）；其他参考资源的许可仍需分别确认。

源码索引：CodeGraph 1260个文件、25273个节点；GitNexus项目名 `CODOL-Native-Reference`。已排除加密库、zlib、二进制和插件。索引存在部分C头文件解析及动态调用截断，未返回的调用不能据此判断不存在。继续用REA核对源码、二进制和3.3.3.3客户端消费者。

按用户最新纠正，旧启动器以静态参考为主，不直接重建或启动它充当新版方案。保留无引擎/网络初始化的资源探针，用于验证当前资源的读取契约；普通启动探针已撤回，失败日志留档。完整源码中的MP启动和合作基础脚本不等于原版首关剧情实现。
