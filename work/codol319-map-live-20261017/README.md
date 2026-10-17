# 核弹小镇首帧实机验收准备

固定A盘实验；授权见scope.md。复用已提交1dc9fc3和REA地图消费者快照，未重做逆向。
前置证据、帧类型和地址见docs/wiki/v3_19_26_22-nuketown.md。
本轮状态见preparation.json，真实回环流量保存在session.pcapng，均留本机。

路径：用户Ready → 当前18人房间交接 → Rust connect/stats → gamestate →
客户端加载阶段 → 首帧/确认/连续帧 → 用户确认地图画面。
本次准备不代表路径已完成。游戏菜单和画面验收仍由用户操作。

解码命令：`tshark -r work/codol319-map-live-20261017/session.pcapng -Y "udp.port == 28970" -T fields -e frame.number -e udp.srcport -e udp.payload`。

验收更新：用户截图确认核弹小镇已显示。完整块抓包前缀map-visible.pcapng、
wire-summary.json及只读mapents-comparison.json共同验证加载与首帧消费；
实体文本与原zone逐字节一致。后续移动、武器、小地图和AI未完成。
详细帧号、运行时地址、哈希和覆盖边界见上述Wiki。
