# 大厅配置与握手派生

逻辑包：`codol.client.lobby.connection`

本目录保存 REA/Ghidra 伪代码，业务标签由分析者添加。完整来源、代码哈希和变体见根目录 function-index.json。

| 地址 | 功能标签 | 代码 |
|---|---|---|
| 0x00641e10 | dwauth 与 STUN 配置读取 | [伪代码](FUN_00641e10.c) |
| 0x00a61980 | 协议 210 握手 transcript 与密钥派生 | [伪代码](FUN_00a61980.c) |
