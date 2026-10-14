# 05 发布文件与角色选择

[总览](README.md) · [上一阶段](04-lobby-stun.md) · [下一阶段](06-onboarding-profile.md)

## 症状与问题定位

“所有调用都返回成功、零个结果”的桩不等于“下载到一个空文件”。GetPublisherFile 要返回文件对象。公开 S1 的 10/7 是初期实现候选；真实 CODOL 发的是 **service10/task21**，带额外的 context 字符串。只实现 10/7 会让真实请求落入普通零结果分支。

**确认**：当前源码同时接受 10/7、10/21，真实日志的八类发布文件下载均为 10/21、N=1。**运行结论**：采用该初始化实现后真实界面已到选角。没有逐一禁用八种文件作对照，因此不能断言每一种文件都独立决定能否进入选角。

## 实际最小解决办法

在 [dw_lobby.py](../../src/dw_lobby.py) 对发布文件请求记录文件名，任意合法文件名返回一个内容为空的 `bdFileData`，不在磁盘伪造官方文件内容。

| 服务/任务（十进制） | typedParameters | 来源/用途 |
|---|---|---|
| 10/7 | `10 filename 00` | S1/IW6 公开源候选；本地兼容分支 |
| 10/21 | `10 context 00 | 10 filename 00` | CODOL 实际请求，符合 IW7 对照结构；本次 context 为空 |
| 10/3、10/1 | 不是上述发布文件读取 | IW6 对照为旧用户文件读/写；不能把这些编号改名成 getPublisherFile |

实际 10/21 文件名后还有一字节 `00`，抓包保留但当前解析不消费；该尾部字段含义未确定。不要把已有参数解析范围描述为完整 schema。

一个空文件的 TASK_REPLY payload 是 32 字节：

```text
0A LE64(transactionID) | 08 00000000 | 03 taskID
| 08 01000000 | 08 01000000 | 13 08 00000000
```

两个计数都为1；`13` 是 blob 类型、`08` 是嵌套长度类型、长度为0。加内层长度/type 后零填充为48字节 AES 输入，外层 L=78，总帧82字节。

其他未知任务仍为成功码0、N=0，仅写一个 `08 00000000` 计数，payload21、总帧66字节。这是推进初始化的桩，不代表已完成相应后端功能。公开源对缺失文件可返回 `BD_NO_FILE=1000`；“任何名称都返回空文件”是本地复现策略。

## 实际请求与验收

11:59:34，同一连接 `127.0.0.1:49162` 的客户端序号9–16请求：

| 序号 | 文件名 |
|---:|---|
| 9 | `mp_playlists_shipRetail_release.info` |
| 10 | `broadcast.info` |
| 11 | `tlogconfig.info` |
| 12 | `sku_tags.info` |
| 13 | `activities_v1.info` |
| 14 | `configs_s.info` |
| 15 | `market-down.info` |
| 16 | `whitelist_tester.info` |

后续真实界面出现五个可选人物。[角色选择截图](../../runtime/captures/screenshots/20261014-character-selection.png)与[选角记录](../reports/20261014-character-selection.md)是界面验收依据；服务返回 N=1 本身不代替界面验收。

第一份文件的可复现证据链：

- [请求](../../runtime/captures/20261014T035934848139-lobby-request.bin) → [响应](../../runtime/captures/20261014T035934850889-lobby-response.bin)，对应[日志](../../runtime/logs/server.jsonl)中时间、peer、seq9 的 `lobby_task`。
- 日志 `parameters_hex` 开头为 `10 00 10`：空 context 后跟文件名；不能当单字符串任务解析。
- [测试](../../tests/test_dw_lobby.py)的 `test_codol_task21_publisher_request_with_context` 检查 21 号任务分支；[协议笔记](../../research/reference-protocol/protocol-notes.md)记录 serializer 和公开源提交。
- 此任务 ID/参数判断来自真实流量与当前源码，没有单独的“CODOL GetPublisherFile 已命名反编译”Evidence ID；不借用 KDF 的证据 ID 冒充服务语义证据。

## 限制、回滚与下一检查

空文件够到选角，不代表 playlist、活动、商城数据完备。角色选择后仍需资料、引导和会话功能；“第二个角色报错”不能推成该角色资源有问题。自动点击未见画面变化，第二个角色的实际选择由用户手动完成并确认。

本阶段没有创建真实 publisher 文件；回滚点是服务端任务处理分支，须按授权恢复对应版本并重启。若恢复成 N=0，预计会失去当前文件对象语义，但不将这种预期写成已执行的回归实验。

下一检查转入 [06](06-onboarding-profile.md)；需要补真实文件内容时，先找客户端消费结构及缺项证据，不从其他 COD 项目直接搬 playlist。
