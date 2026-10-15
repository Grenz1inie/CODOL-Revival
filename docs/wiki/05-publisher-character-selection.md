# 05 发布文件与角色选择

[总览](README.md) · [上一阶段](04-lobby-stun.md) · [下一阶段](06-onboarding-profile.md)

## 症状与问题定位

“所有调用都返回成功、零个结果”的桩不等于“下载到一个空文件”。GetPublisherFile 要返回文件对象。公开 S1 的 10/7 是初期实现候选；真实 CODOL 发的是 **service10/task21**，带额外的 context 字符串。只实现 10/7 会让真实请求落入普通零结果分支。

**确认**：当前源码同时接受 10/7、10/21，真实日志的八类发布文件下载均为 10/21、N=1。**运行结论**：采用该初始化实现后真实界面已到选角。没有逐一禁用八种文件作对照，因此不能断言每一种文件都独立决定能否进入选角。

## 实际最小解决办法

初期在 [dw_lobby.py](../../src/dw_lobby.py) 对发布文件请求记录文件名，合法文件名返回一个内容为空的 `bdFileData`。2026-10-15开始为确切的赛单文件名提供本地适配内容；其他文件继续使用原响应，见本文末尾。

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

初期选角阶段没有创建真实 publisher 文件；回滚点是服务端任务处理分支，须按授权恢复对应版本并重启。若恢复成 N=0，预计会失去当前文件对象语义，但不将这种预期写成已执行的回归实验。

下一检查转入 [06](06-onboarding-profile.md)；需要补真实文件内容时，先找客户端消费结构及缺项证据，不从其他 COD 项目直接搬 playlist。

## 赛单恢复与界面复审（2026-10-15）

用户截图中，精简发布文件只显示一个 `KILLHOUSE DM` 分类，中间列表及匹配按钮缺失。用户随后明确当前先恢复界面供人工复审，暂停对局能力扩展。文件传输成功和分类可见不足以证明完整菜单可用。

参考为用户提供的相邻 `Server/mp_playlists_shipRetail_release.info`（version796，SHA256 `43ec9add79e69a6439d2de3e04a953a2f562d71e3d1e89d78b03b00e3b58c3ca`）。它包含完整目录，但格式不是当前客户端可直接照搬的格式。适配结果保存在 [data/match-playlist.info](../../data/match-playlist.info)，发布version798，运行不依赖Server目录。

- 保留97个带release标记的赛单及原ID、地图行、玩法规则；只保留这些赛单使用的30种玩法。当前解析器 `0x6111d0` 最多接受32种，参考文件43种导致后面的狼人、勇者游戏、无畏护送等地图行被丢弃。
- 当前 `catinfo` 只读取ID、Group、Flag及两种语言名称（`0x611537..0x611625`），没有参考文件的空Unlock_Item字段。去掉该列，补齐中文分类名。
- 参考文件将英文放在chinese槽、乱码中文放在english槽。将可逆的Latin-1/GB18030乱码恢复为中文，两槽一致；分类名按模式语义整理，不声称逐字复原全部历史文案。
- 名称/说明的原生缓冲区为64/256字节（`0x611925`、`0x611af7`）。13条过长说明缩至标点边界并加省略号，避免UTF-8字符被截断。去掉15行旧活动时间、日期和星期限制；不搬入参考文件开头的全局引擎调参。
- 只发布赛单文件；没有修改游戏EXE、UI资源、正式档案或额外开放新对局。客户端本身的顶部标签、版式仍由3.3.3.3原资源决定，参考截图不能证明它们与当前版本一致。

定向TDD先复现目录缺失，再验证当前EXE的真实解析器能得到PVP/PVE分类、中文名称与说明，以及“战术团竞6V6”的34张地图（含Killhouse）。[原生探针](../../tests/client_playlist423.py)只替换下载元数据查询及已捕获的unlockFlags表查询，不替换赛单解析、地图行校验或分类归属；[回归用例](../../tests/test_client_playlist.py)覆盖全部非空分类下的文本和地图，发布接口测试核对完整字节。未执行Flash绘制或按钮点击。

```powershell
$env:PYTHONPATH='src;tests;tools'
python -m unittest test_client_playlist test_dw_lobby.LobbyTests.test_local_lobby_serves_the_restored_playlist -q
```

REA复用并保存 `research/evidence/client423-independent-server-baseline.rea.json`（93个workflow条目、184条Evidence）。本轮新增字符串查询超时；以上新增解析器结论来自同一哈希EXE的定址汇编和机器码执行，未冒充新的REA反编译结果。

项目服务已重启为PID47304。实际加密大厅请求已读回version798完整内容（86446字节，SHA256 `a3fcd248e2725246eec429f5cefbb91d17891a6daedf2d40dcc3d96eedf943d5`），与项目文件逐字节一致；检查未上传玩家档案，也未启动游戏或消费对局握手。

人工复审步骤：

1. 从Web控制器重新启动游戏，进入“玩 → 多人竞技(PVP)”，检查多个分类和中间赛单是否出现。
2. 选择“战术团队竞技 → 战术团竞6V6”，检查中文说明、地图预览/列表，以及“开始匹配”按钮是否显示；先不进行对局验收。
3. 切到PVE，检查生存、机械僵尸、僵尸猎场等分类和子赛单。记录缺项或乱码截图。

实际界面、地图图片和按钮仍以本次人工复审为准。菜单中列出模式只表示恢复目录，不表示独立服已实现其匹配或战斗。

### 人工复审：中文编码修正（version799）

用户截图确认分类、子赛单和“开始匹配”按钮已出现，但中文乱码。例如UTF-8的“狼人行动”按GBK读取会得到“鐙间汉琛屽姩”，与截图吻合。前述原生探针只确认解析器保留文本字节，却错误地用UTF-8解码结果，没有覆盖菜单使用GBK/CP936的边界。

修正位于 `local_server.py` 的赛单发布入口：UTF-8源文件读取后严格转GBK发送，并将版本升至799。同时恢复勇者游戏及联赛的4条旧乱码覆盖文案，两语言槽保持一致。分类归属、赛单ID、地图、规则均不变。发布接口回归先按GBK读取旧响应失败，再验证修正后的中文及固定CP936字节；原生解析探针同步按GBK消费。实际中文显示由用户重启游戏后复审；本轮不处理截图中地图数量或预览问题。
