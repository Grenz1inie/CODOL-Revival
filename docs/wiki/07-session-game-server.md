# 07 会话与游戏服务器

[总览](README.md) · 上一阶段：[新手引导与角色资料](06-onboarding-profile.md)

## 症状及当前能确认的事实

用户选第二个角色后停在训练页并报服务器繁忙。12:06 观察时游戏 PID6188、服务 PID13100 均存活且 Responding=True；至12:08:09有大厅心跳，该观察区间无 auth_error/lobby_error。这些是当时的记录，不是现在仍在运行的断言。

最直接的新入口是同一连接 seq51 的 **service9/task16**，参数143字节。真实响应已经独立校验 HMAC 并解密：

```text
transaction=51，error_code=0，task_id=16，result_count=0
payload=0a3300000000000000080000000003100800000000
```

**确认**：服务器返回的是成功码、空结果；UI 仍报繁忙。**推断**：结合训练页，训练会话或游戏服务器查找是候选方向。**未证实**：9/16 的准确操作名称、结果对象布局，以及这个空结果是否直接触发该警告。

## 已做的最小处理与为何还未解决

[dw_lobby.py](../../src/dw_lobby.py)让未知服务返回有正确 TASK_REPLY 包装的 N=0，维持协议推进与证据采集；这并没有创建训练会话，也没有启动实际游戏服务器。

本阶段尚无已验证的修复。不要只向9/16塞一个凭空拼装的 N=1 结果来宣布完成；必须知道客户端如何反序列化和消费结果、是否随后连接另一个端点。

公开 IW6 的 task16 可名为 `find_sessions_two_pass`，但其服务编号为21，而本次是9。**taskID 相同不足以移植操作名和 schema。** 大厅 TCP3074、STUN UDP3074 已应答也不说明对局数据协议已实现。

## 保存的静态调查

原始 EXE 中找到 `MatchMaking_FIND_SERVERS_Query` RTTI。保存的反编译包含 `0x6df690`、`0x702200`，能作为查找对象构造与调用的入口；尚未将它们与本次9/16及 UI 错误分支连接起来。

在当次 REA 已定义字符串范围内搜索 getSessions/findSessions/SERVER_BUSY 返回空，只能描述这次有边界的搜索结果。不能把“没有已定义字符串命中”写成“二进制没有该功能”。

## 证据入口与复核方法

- [实际响应](../../runtime/captures/20261014T040459976482-lobby-response.bin)、[请求51解析](../../research/evidence/character-selection-request-51.json)：`response_mac_valid=true`、事务51、错误码0、N=0。
- [事件摘录](../../runtime/captures/character-selection-events.jsonl)、[完整日志](../../runtime/logs/server.jsonl)、[首次界面警告](../../runtime/captures/screenshots/20261014-after-character-selection-error.png)、[选角记录](../reports/20261014-character-selection.md)。
- [FIND_SERVERS RTTI 引用](../../research/evidence/find-servers-rtti-xrefs.json)：`ev_8b569278cab0af3c80a32c893f7ab67786786693686cf54d4c28412209733af4`。
- [查询相关反编译](../../research/evidence/find-servers-query-decompiled.json)：`ev_f6c40ede7ab6ebdfed42a0e45705fe396e3b37f340b010da4944d764fcbe01fa`；这是候选调用链，不是9/16命名的完成证明。
- [字符串负结果](../../research/evidence/post-selection-session-strings.json)：`ev_a1f1a3456dfa09d23e61b84ccedc86d48a33456ab3a2f8255bc12096d123de5b`。

已有事件可在项目根只读筛选，不需要向正在运行的服务发请求：

```powershell
Get-Content -LiteralPath '.\captures\character-selection-events.jsonl' |
    ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object { $_.event -eq 'lobby_task' -and $_.service_id -eq 9 -and $_.task_id -eq 16 }
```

当前参数日志只截取前128字节，而总参数143字节；完整解析必须从对应原始加密请求及该连接握手重新验证，不把截断的 `parameters_hex` 当完整请求。

## 下一项最小调查与验收

1. 将9/16发送点、参数序列化和结果消费连到同一客户端路径，确认它到底请求什么；保留当前连接时间与 peer，防止重连后的序号误配。
2. 找到返回0个结果时的 UI 分支，与“服务器繁忙”显示建立直接证据；否则仅记为时间相关。
3. 确认所需会话/地址结构后再实现最小对象，观察客户端下一步真实连接，确定游戏服务器协议边界。
4. 以“加载目标地图并进入可交互训练”为本阶段验收；仅去掉弹窗、显示菜单或收到 UDP 均不足。资料写回和重进持久化另验。

12:24 的两参数实验仍停在原界面，详见 [06](06-onboarding-profile.md)；它没有替本阶段提供会话成功证据。本阶段尚未实现游戏服务器。

## 回滚与限制

目前没有真实游戏服务器实现可回滚。后续新增服务/会话响应前保留现有源码和抓包基线；若实验失败，恢复对应服务版本并按授权重启，不改 EXE、系统 CA 或外部网络配置来掩盖未知协议。

当前已完成的链路仍是“本地认证 → 加密大厅 → 发布文件 → 角色选择”。训练/菜单问题、服务器会话和完整对局属于未完成阶段，需分别记录结果。

## 12:40 进入大厅后的补充证据

连接127.0.0.1:64775的seq32仍发送9/16，本地服务仍返回0个结果，但真实客户端已显示游戏大厅和第二角色，没有训练繁忙弹窗。见[大厅截图](../../runtime/captures/screenshots/20261014-main-menu-profile-restore.png)和[事件记录](../../runtime/captures/main-menu-first-events.jsonl)。

因此“任意9/16空结果都会导致当前报错”不成立。训练分支下的具体任务语义和失败条件仍需单独还原；本次通过[引导覆盖和公开档案](06-onboarding-profile.md)避开了此前阻塞，未伪造可用对局服务器。后续对局验收仍需实际会话地址、服务器握手和地图加载证据。
