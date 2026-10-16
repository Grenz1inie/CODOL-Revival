# 03 地址重定向、TLS 与认证

[总览](README.md) · [上一阶段](02-process-iips-admin.md) · [下一阶段](04-lobby-stun.md)

## 症状与已确认原因

管理员启动后错误 100 并不能区分缺服务、TLS、认证或大厅失败。早期本机没有对应 auth/master 服务；后续即使认证已被接受，大厅仅抓包不响应，30 秒后仍显示错误 100。

真实 `POST /auth/` 使用 TLSv1 / AES256-SHA、`Expect: 100-continue`，165 字节 JSON 为字符串字段：

```json
{"auth_task":"10","iv_seed":"1320227669","title_id":"1002","identity":"356c4bc3","extra_data":"{\"version\":\"0\",\"user_id\":\"16810275000640848443\"}"}
```

**确认**：无 Steam/Tencent token，不能套 S1 的 `decoded_token[32:56]`。**未知**：task10 加密票据模式下 identity/auth-key 的推导。实现采用本客户端已有的明文票据解析路径，没有猜造密钥算法。

## 实际最小解决办法

客户端根目录 `dwauth.ini` 指向本机：

```text
127.0.0.1 3074
127.0.0.1 443
0x03EA
```

`stun.ini` 为 `127.0.0.1`。服务只监听回环：TCP 443 认证、TCP 3074 大厅、UDP 3074 STUN。`0x03EA=1002`，与实际 title_id 对应；不额外推定第三字段的所有内部用途。

3.3服务启动通过[准备入口](../../games/codol/versions/v3_3_3_3/scripts/Prepare-Client.ps1)先生成缺失地图，再准备实例证书和上述三个客户端文件，最后完整预检。有效证书复用；证书缺件、损坏或失效时，原证书目录保留到本实例`backups/certs-<时间>/`后重建。检查系统时钟可避免错误时间导致证书失效。

CA和含`127.0.0.1`/`localhost` SAN的服务证书放在`runtime/instances/<实例>/certs/`。CA只追加到游戏自己的`cacert.pem`，保留原内容并去重；**没有安装OS根证书，也没有修改hosts、防火墙或EXE**。首次配置原始字节保存在同实例`backups/client-config/`；`missing.json`记录首次准备时不存在的文件。配置发布失败恢复本次修改，重复准备不覆盖首次备份。

[本地证书工具](../../tools/create-local-cert.py)保留为手动维护入口，须明确指定`--runtime 'runtime/instances/<实例>'`，不再写未被实例使用的根`runtime/certs`。正常启动无需先手动调用该工具。

[local_server.py](../../games/codol/versions/v3_3_3_3/server/local_server.py)对该本地服务启用 TLSv1 兼容和 `ALL:@SECLEVEL=0`，先回复 HTTP `100 Continue`，按 Content-Length 收完整 JSON，再发最终响应。这是本地兼容配置，不是系统 TLS 策略修改。

[dw_auth.py](../../games/codol/versions/v3_3_3_3/server/dw_auth.py)仅处理观察到的 task10，返回 `auth_task="11"`、`code="700"`，两个 base64 编码的 128 字节票据。客户端票据以 LE32 `0xEFBDADDE` 开头，字节为 `DE AD BD EF`；服务票据是本地约定 `sessionKey24 + zero104`。

| 明文 client_ticket 偏移 | 内容 |
|---|---|
| 0 / 4 / 5 | magic u32 / type u8 / title u32 |
| 9 / 13 / 17 / 25 | issued u32 / expiry u32 / license u64 / userID u64 |
| 33 | 固定 64 字节用户名 `LocalPlayer`，零填充 |
| 97 | 24 字节 `bytes.fromhex('1337' * 12)`，与大厅一致 |
| 121 / 124 | 3 字节标记 / 4 字节 hash，当前均为零 |

当前实现票据有效期为签发时间加 86400 秒。它与公开 S1 示例值不同，以项目源码为准。

**静态证据**：`0xa598b0` base64 解码后检查 magic；匹配时 `0xa59bd6..0xa59c31` 跳过虚函数票据解密。`0xa678c0` 读取 128 字节结构，`0xa595c0` 在该客户端中直接返回 true。没有 EXE patch，也不需要伪造 Steam task29 流程。

## 运行验收

11:38:09 收到真实 TLS 请求；11:45:53 返回 task11 后，客户端主动连接 TCP 3074 并发 28 字节 hello。**“客户端继续进入大厅协议”才是本阶段通过点，HTTP 200 本身不够。**

- [原请求](../../runtime/captures/20261014T033809332089-auth-request.bin)、[被接受的响应](../../runtime/captures/20261014T034553362522-auth-reply.bin)、[紧随其后的大厅 hello](../../runtime/captures/20261014T034553490974-lobby-request.bin)。
- [认证验证记录](../reports/20261014-auth-verification.md)、[认证测试](../../games/codol/versions/v3_3_3_3/tests/test_dw_auth.py)。
- [认证 REA JSON](../../research/evidence/auth-parser-decompiled.json)，`ev_806f8b8a073991ad1b8b2ed6e34540407266a15ab204346b21850a5fbc77728d`。
- [配置读取/大厅 REA JSON](../../research/evidence/lobby-keys-stun-decompiled.json)，`ev_88a82b73182cc47932137af41a0471451f32e98cb986bebdcb5fa10822f80bb1`；`0x641e10` 读取 dwauth/stun 配置。

## 复现、限制与回滚

在 [02](02-process-iips-admin.md) 的授权启动流程后，先查 `auth_request` 的 TLS、字段和 capture，再查 `auth_reply`，最后关联同次启动的大堂 hello。认证和大厅固定 key 必须一致；测试本地用户不代表在线帐号可用。

回滚需停止相关进程后，从当前实例`backups/client-config/`恢复三个文件；`missing.json`列出的文件恢复为不存在状态。历史手动配置的旧备份仍在`runtime/backups/`，不要混用不同时间点的备份。无需卸载系统CA，因为没有安装过。

明文路径通过仅针对该哈希客户端，不证明其他版本接受。下一检查是 [04](04-lobby-stun.md) 的 `AB81 → AB82 → AB83`，不因后续错误 100 就重写已通过的认证。
