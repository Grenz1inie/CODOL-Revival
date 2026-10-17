# 3.19核弹小镇地图载入实验

授权见`scope.md`，结论、地址、哈希和未验证项统一见
`docs/wiki/v3_19_26_22-nuketown.md`。生成证据、游戏资源不入Git。

- `verify_client_crypto.py`：复用本版快照，在Unicorn执行`0x4709e0`，
  对照本次真实加载报文的三个输入。由仓库根目录以`python -B`运行。
- `probe_map.py`：固定A盘实验的有界只读采集；核对PID创建时间、路径、
  EXE哈希及消费者原字节。运行时指针直接读取，不重复加基址。
- 本机REA证据为`rea-map-consumer.evidence.json`及`.analysis.json`。
  完整镜像超时后r2初筛、REA原字节交叉确认；受限镜像伪代码覆盖有限。
- `client-crypto.json`、`udp-loading.json`、`loaded-maps.json`及PCAP保留本机。
  首轮已到阶段6，但用户仍见加载中；新首帧等待人工验收。
