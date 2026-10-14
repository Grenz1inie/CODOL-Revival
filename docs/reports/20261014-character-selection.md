# 角色选择与选角后报错记录

时间：2026-10-14，以下为北京时间（UTC+8）。

## 实际结果

原版客户端已通过本地认证和大厅初始化，显示五个人物的角色选择界面。
自动点击第二个角色后画面没有变化；用户手动完成选择，并报告出现错误。
随后实际截图显示新手训练引导页，文字为“很好 johnClient！接下来我们将前往核弹小镇开始训练。点击继续开始。”，前方弹出：

> 警告：服务器繁忙中，请稍候重试

第二个角色的选择由用户报告确认；没有进一步验证角色数据重启后的持久化。
12:06 的进程检查中，游戏 PID 6188 和本地服务 PID 13100 均存活且 Responding=True。
截至 12:08:09，大厅仍有心跳请求与响应；本次选角观察区间没有 auth_error 或 lobby_error。
本轮未关闭、重启游戏，也未改动服务协议处理。

## 请求证据

| 时间 | 客户端序号 | 服务/任务 | 观察 |
|---|---:|---|---|
| 12:04:50 | 47、48 | 8/3 | 两次含压缩内容的数据提交，未解释为已持久化 |
| 12:04:52 | 49 | 21/5 | 新的大厅任务 |
| 12:04:55 | 50 | 71/3 | 解密后包含 OnBoarding 和 LoadoutChangeEvent |
| 12:04:59 | 51 | 9/16 | 参数 143 字节；当前服务尚未实现，返回零个结果 |
| 12:05:09 | 52 | 71/15 | 解密并解压后包含 UIPage 事件 |

已独立验证请求 51 的实际响应 HMAC，并解密实际响应：

```text
transaction = 51
error_code  = 0
task_id     = 16
result_count = 0
payload = 0a3300000000000000080000000003100800000000
```

响应捕获：`../captures/20261014T040459976482-lobby-response.bin`。
结构化解析：`../research/character-selection-request-51.json`。
观察区间事件：`../captures/character-selection-events.jsonl`；完整持续日志为 `../logs/server.jsonl`。

## 结论边界和下一步

“本地认证 → 加密大厅 → 发布文件 → 角色选择”已由真实界面验证。
选角后的错误发生在新手训练引导阶段，当前最直接的调查入口是 `9/16` 的零结果响应。
结合画面，训练会话/服务器查找是候选方向；尚未追到客户端错误分支，不能将该请求名称或因果关系当作已证实。
公开 IW6 代码的 task 16 对应 find_sessions_two_pass，但它的服务编号为 21，与本次 9 不同，不能直接套用。
REA 对 getSessions/findSessions/SERVER_BUSY 的已定义字符串搜索为空；空结果不能证明相关逻辑不存在。
原始 EXE 中可找到 `MatchMaking_FIND_SERVERS_Query` RTTI，后续可从该类型和请求发送点继续定位。
没有证据证明错误与第二个角色本身有关；也没有验证其他角色是否同样报错。

后续应先定位 `9/16` 的请求序列化和结果消费，再确定需要怎样的训练服务器信息及实际游戏协议；仅增加一个伪造结果不能证明可进入训练。

## 截图与归档

- 角色界面：`../captures/screenshots/20261014-character-selection.png`
- 选角后警告：`../captures/screenshots/20261014-after-character-selection-error.png`
- REA 字符串搜索：`../research/post-selection-session-strings.json`
- REA FIND_SERVERS RTTI 引用：`../research/find-servers-rtti-xrefs.json`
- 此前主程序分析证据包：`../research/rea-main-evidence-20261014.json`

服务继续写入本地日志；本轮人工观察已完成，不代表会话结束后仍有自动分析或通知。
