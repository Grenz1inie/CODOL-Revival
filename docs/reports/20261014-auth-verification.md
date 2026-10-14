# 本机认证验证记录

目标文件：`codoMP_client_shipRetail.exe`，SHA256：
`e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b`。

2026-10-14 11:38:09，客户端通过 `TLSv1 / AES256-SHA` 向本机 443 发送
`POST /auth/`。请求使用 `Expect: 100-continue`，JSON 长度 165。
字段为 `auth_task=10`、`title_id=1002`、`iv_seed`、`identity` 和字符串形式的 `extra_data`。
捕获：`../captures/20261014T033809332089-auth-request.bin`。

2026-10-14 11:45:53，服务端返回 `auth_task=11`、`code=700`，两个 128 字节 base64 票据。
客户端随后主动连接本机 TCP 3074，发送 28 字节大厅 hello：
`c8000000c8000000d2000000d2000000000008006b8b867dafe4229e`。
这证明客户端接受了认证响应，而不只是本地服务返回 HTTP 200。
捕获：`../captures/20261014T034553362522-auth-reply.bin`、
`../captures/20261014T034553490974-lobby-request.bin`。
当时大厅仍为抓包桩，30 秒后超时，界面仍报错误 100；尚不能算角色选择成功。

## REA / Ghidra 证据

REA 6.4.0、Ghidra 12.1.4，使用隔离的常驻 stdio 会话。
主程序默认分析耗时 642.66 秒；该进程的启动等待设为 1,200,000 毫秒。
环境覆盖只属于 `tools/rea-session.mjs` 启动的分析进程，未更改全局 REA 配置。

- `../research/auth-parser-decompiled.json`：
  `ev_806f8b8a073991ad1b8b2ed6e34540407266a15ab204346b21850a5fbc77728d`。
  `0xa598b0` 解析认证响应，base64 解码后检查 `0xefbdadde`；匹配时跳过加密票据解密分支。
  `0xa678c0` 反序列化 128 字节票据；`0xa595c0` 在本客户端中直接返回 true。
- `../research/lobby-keys-stun-decompiled.json`：
  `ev_88a82b73182cc47932137af41a0471451f32e98cb986bebdcb5fa10822f80bb1`。
  `0xa61980` 处理 server hello，校验协议 210，计算 `CLIENTCHAL` 16 字节、`BDDATA` 72 字节。
  `0x641e10` 读取游戏根目录的 `dwauth.ini` 和 `stun.ini`。

可读伪代码同时保存为 `research/0x*.c`。地址均为静态首选映像地址，不直接作为运行时地址。

## 边界

没有修改原 EXE，没有使用真实在线帐号登录，没有连接官方认证服务。
认证用户名为本地 `LocalPlayer`，会话密钥是仅用于本机复现的固定测试值。
加密票据模式的 task-10 密钥推导仍未确定；本客户端现有明文票据路径已经通过实际启动验证。
