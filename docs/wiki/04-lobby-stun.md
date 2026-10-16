# 04 加密大厅与 STUN

[总览](README.md) · [上一阶段](03-redirection-tls-auth.md) · [下一阶段](05-publisher-character-selection.md)

## 症状和原因

认证通过后，客户端连接 3074 并发 28 字节，原抓包桩只收不答，超时后错误 100。第一 DWORD 为 `0xC8`；若把它当普通包长度等待 200 字节，会在最早阶段等待不存在的后续内容。

**静态及抓包确认**：CODOL 只协商版本 210，hello 不是普通长度帧。完整收发必须处理 TCP 拆包/粘包，不能把一次 `recv()` 当一包。每次连接独立维护 transcript、key 和计数器。

## 实际最小协议实现

[dw_lobby.py](../../games/codol/versions/v3_3_3_3/server/dw_lobby.py)提供 `handle_lobby(sock, peer, record, save_capture)`；[local_server.py](../../games/codol/versions/v3_3_3_3/server/local_server.py)持有已接受 socket、120 秒超时及关闭职责。没有把解析模块本身做成监听器。

### 握手与 KDF

以下整数是 little-endian；长度不含最前面的四字节长度字段。

```text
hello 28字节：LE32(200) | LE32(200) | LE32(210) | LE32(210)
              | LE32(0x80000) | clientNonce[8]
server81：16 00 00 00 AB 81 D2 00 00 00 | (13 37 × 8)
client82：LE32(L) | AB 82 | opaqueAuth | clientProof[8]
server83：0A 00 00 00 AB 83 | serverProof[8]

transcript = hello[8:28] + fullServer81 + fullClient82[:-8]
D = SHA1(transcript)
PRK = HMAC-SHA1(key=D, message=sessionKey24)
T1 = HMAC-SHA1(PRK, label + 01)
Ti = HMAC-SHA1(PRK, T(i-1) + label + byte(i))
C = Expand("CLIENTCHAL", 16)
B = Expand("BDDATA", 72)
clientProof=C[0:8]，serverProof=C[8:16]
c2sHMAC=B[0:20]，s2cHMAC=B[20:40]
c2sAES=B[40:56]，s2cAES=B[56:72]
```

双方 sessionKey 都是 `bytes.fromhex('1337' * 12)`。fullServer81 与 fullClient82 都包含自己的长度字段；排除的是 hello 前八字节和 client82 最后八字节。初始 C8 特例只用于 hello，后续长度为 200 的普通帧不能再按 hello 解释。

客户端函数 `0xa61980` 重建上述 transcript，校验 210 并生成 16/72 字节输出。保存的伪代码证明这个流程；opaqueAuth 内票据位布局并未因此完整解释。

### 任务帧与响应

```text
LE32(30+ciphertextLength) | AB 85 | LE32(sequence) | IV[16]
| AES-128-CBC(ciphertext) | HMAC-SHA1(directionKey, 前面全部字节)[0:8]
明文：LE32(payloadLength) | innerType | payload | 零填充到16字节
客户端 innerType=86，payload=serviceID | 03 taskID | typedParameters
服务端 innerType=01，即 TASK_REPLY
```

MAC 包含外层长度 DWORD，padding 不是 PKCS#7，payloadLength 不含 innerType。未知服务的当前桩回显实际 taskID，成功码 0、结果数 0；发布文件例外见 [05](05-publisher-character-selection.md)。不合法 proof/MAC/内层类型会记录 `lobby_error` 并结束处理，不猜另一种格式继续回复。四字节全零心跳原样应答。

### STUN 的已知范围

这是 Demonware UDP 格式，不是 RFC5389。地址四字节为网络顺序，端口两字节为 LE：

| 实际输入/类型 | 当前响应 | 证据边界 |
|---|---|---|
| `1e 03 00`，十进制 30 | `1f 02 00 + peerIPv4 + LE16(peerPort)`，9 字节 | 本地真实请求与应答已抓到；请求版本3、响应版本2是本次实测 |
| `14 02 00 00`，十进制 20 | `15 02 00 + peerEndpoint + serverEndpoint`，15 字节 | server 为 127.0.0.1:3074；本次 peer 端口30001 |
| 29 字节、开头 `0e 02 00`，十进制 14 | 当前 helper 返回 None，仅记录请求 | 用途及是否需响应未知，不能宣布所有 UDP 协议完成 |

## 运行验收与证据

11:57:12 出现真实 `lobby_authenticated`，随后客户端发出加密任务。握手首轮抓包：

- [28 字节 hello](../../runtime/captures/20261014T035712050613-lobby-request.bin)、[26 字节 server81](../../runtime/captures/20261014T035712053638-lobby-response.bin)。
- [153 字节 client82](../../runtime/captures/20261014T035712084364-lobby-request.bin)、[14 字节 server83](../../runtime/captures/20261014T035712087339-lobby-response.bin)。对应 transcript SHA1 为 `ac02562009a2aa7dab424eb4fcb836a3a3e70399`。
- [首个已处理加密请求](../../runtime/captures/20261014T035712118848-lobby-request.bin)、[响应](../../runtime/captures/20261014T035712126301-lobby-response.bin)。
- [类型30请求](../../runtime/captures/20261014T035713460832-stun-request.bin)、[应答](../../runtime/captures/20261014T035713463581-stun-reply.bin)；[类型20请求](../../runtime/captures/20261014T035713465777-stun-request.bin)、[应答](../../runtime/captures/20261014T035713468224-stun-reply.bin)；[尚未解释的0x0e](../../runtime/captures/20261014T035949825070-stun-request.bin)。
- [REA JSON](../../research/evidence/lobby-keys-stun-decompiled.json)，ID `ev_88a82b73182cc47932137af41a0471451f32e98cb986bebdcb5fa10822f80bb1`；[可读伪代码](../../research/evidence/0xa61980.c)。
- [协议测试](../../games/codol/versions/v3_3_3_3/tests/test_dw_lobby.py)覆盖拆包/粘包、KDF、方向密钥、MAC 拒绝、重连状态、TASK_REPLY/STUN；当前源码含后续补充的 CODOL 10/21 测试，最新测试结论见[项目总览](../../README.md)。

## 回滚和下一检查

服务协议变更必须经授权重启服务，记录新启动区间；回滚时恢复对应服务版本与 auth/lobby 一致的 key，不能只改单边密钥。无需改 EXE 或系统证书。旧文档中“尚待大厅验证”是早期状态，不能覆盖上述后续抓包。

下一关是 [05](05-publisher-character-selection.md) 的非零发布文件结果。持续心跳只能证明连接仍活着，不能证明角色保存、会话查找或训练成功。
