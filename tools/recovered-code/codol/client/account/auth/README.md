# 账号认证与票据

逻辑包：`codol.client.account.auth`

本目录保存 REA/Ghidra 伪代码，业务标签由分析者添加。完整来源、代码哈希和变体见根目录 function-index.json。

| 地址 | 功能标签 | 代码 |
|---|---|---|
| 0x00a598b0 | 认证响应与 client_ticket 解码入口 | [伪代码](FUN_00a598b0.c) |
| 0x00a678c0 | 128 字节认证票据字段读取 | [伪代码](FUN_00a678c0.c) |
| 0x00a595c0 | 当前版本票据校验回调 | [伪代码](FUN_00a595c0.c) |
