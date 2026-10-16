# 2026-10-17 电量不足暂停点

用户要求暂停并把工作区应跟踪内容分批提交本地，不推送。本轮不继续开发或实机实验。

## 当前状态

- 3.19等待厅已出现17个人机，用户确认Bot01～Bot17名字正常；房间内存18人、双方各9人。
- `49ea5c7`的Ready修正实机失败：用户仍反馈进房即倒计时。启动参数收到3291=0，
  但PID76284只读快照中该值与房间自动模式均为1，18名成员ready均为0。
- 用户已选择真人Ready后才开始；不再询问这项行为决定。进程写入未获授权，
  `ready_gate_proposal.py`只在Unicorn内验证8项，尚无生产安装器、实机补丁或授权询问。
- Rust UDP基础已实现，transport 7项、packet 3项、udp 1项、room_cli 2项定向通过。
  原生测试启用`CODOL319_NATIVE_PYTHON=A:/Coding/Python3.13.7/python.exe`。
  尚未接入管理器核弹小镇启动，也没有gamestate/快照/输入/碰撞/AI互射与计分。
- 最新release程序尚未包含UDP serve增量，不能把源代码提交当作生产采用。

## 已落盘证据

- 原游戏SHA-256：`36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537`。
- `room-results319.exe`：`97d4f44d56ff86b8f3c09f6e42cde205de9df6941eef3a1e5eb423120708644c`。
  最新`room-results-rea.evidence.json`为357915字节、40条记录；
  `room-results-rea.snapshot.json`为646280字节、23项workflow、40条证据。
  REA已成功保存并关闭目标。恢复时open_binary指定本镜像和snapshot_path，
  参数以当时工具schema为准；缓存可复用，新查询可能仍需重新初始化Ghidra。
- `udp319.exe`及`udp-rea.evidence.json`、`udp-rea.snapshot.json`保留；哈希和地址见Wiki。
- `room-policy-76284.json`为当前失败的限定只读证据。
- `room-human-ready.pcapng`已停止；最终SHA-256
  `2e91d87487d627009edc8644a3d227c8f9a263ce806158589f0514c1c43f7013`。
  现有解码是停止前的279条消息前缀，需用`decode_admission_capture.py`按客户端
  端口49374重新解码最终文件。不能混用前缀哈希与最终文件哈希。
- Bot原版名字和配装证据在`bot-names-17208.json`、`bot-assets-waitroom-15592.json`；
  已定位但未接入。`resources/`下是本地提取的游戏资源，不提交Git。

## 下次顺序

1. 查看当前Git状态与其他任务最新提交，遵守版本隔离，先复用上述REA缓存。
2. 优先解决实机自动倒计时：核对原生自动分支与服务器可控入口。若采用现有门控
   提案，先展示`ready-gate-proposal.md`并请求限定隔离实例的进程写入授权；当前
   AGENTS只读授权明确不覆盖此类操作。不要自行启用，也不要再重复失败启动方案。
3. 继续Rust真实核弹小镇链路：当前3.19代理UDP契约、gamestate/快照、地图真实消费、
   输入、原版人机配装及9V9队伍计分。不要移植3.3地址、资源编号或网络布局。
4. 新可测行为准备好后，用户操作游戏；同一次抓包对应同一次验收。
5. 最后审计原工具遗漏功能。3.3资源和首次部署任务另有方案，避免重复开发。

源码、测试、回环服务、客户端兼容、实机可玩分别报告。已通过的定向验证不重复，
低电量保存阶段只检查提交范围与diff格式。游戏和控制器没有因本次保存而重启。
