# CODOL DW3 reference protocol notes

Research date: 2026-10-14. Public implementation source was inspected at pinned commits below; this is not an official Demonware specification. No REA session, game, service, certificate, or system setting was touched. Downloads and this report stay in this directory. Source files are preserved byte-for-byte; `source-manifest.json` records URLs and SHA-256.

## Immediate CODOL auth result

The saved real request `../../captures/20261014T033809332089-auth-request.bin` contains a 165-byte JSON body: task `10`, title `1002`, seed `1320227669`, identity `356c4bc3`, and stringified `extra_data` with `version` and `user_id`. It has **no token**. Thus S1's Steam-token offset +32 cannot supply CODOL's auth key.

[Auth enums][auth-enums] identify decimal request/reply pairs 10/11 (account/MMP), 28/29 (Steam), and 32/33 (CODO). These are separate flows; 29 is not a universal success task. Parent subsequently reports that CODOL's parser at 0xa598b0 compares decoded ticket magic against data at 0xc07908 and skips decryption on matching magic (0xa59bd6..0xa59c31). Parent reports a successful live login using **plaintext 128-byte ticket, auth_task "11"**, followed by a 28-byte lobby hello. Those binary/runtime findings are parent-supplied, not independently reproduced here. Local TLS already works; no TLS changes are needed for this module.

Auth/lobby share `SESSION_KEY = bytes.fromhex('1337' * 12)`. CODOL's encrypted-ticket key derivation from identity remains **unknown**; successful plaintext mode avoids needing that derivation. Do not describe `Tiger(identity)` or token extraction as established.

## Auth JSON and ticket reference

[S1 auth][s1-auth] / [IW7 auth][iw7-auth] parse string `title_id`, string `iv_seed`, and **string containing JSON** `extra_data`, whose `token` is base64-decoded. IW7 also reads identity without using it. Reference response:

```json
{"auth_task":"29","code":"700","iv_seed":"<decimal seed>","client_ticket":"<base64 128 bytes>","server_ticket":"<base64 128 bytes>","client_id":"","account_type":"steam","crossplay_enabled":false,"loginqueue_enabled":false,"lsg_endpoint":null}
```

For the observed CODOL request the verified parent integration uses task **11**, not this Steam example. Do not assume Steam-specific optional fields are required. S1 misspells `loginqueue_eanbled`; IW7 fixes it and adds stringified `extra_data` with empty `extended_data`. Both emit HTTP 200, JSON content type and byte Content-Length. The source ignores a separate `POST /auth/` header chunk and parses a subsequent body chunk; that is an in-process send-hook shortcut, not a correct TCP/HTTP parser. The captured CODOL request also has `Expect: 100-continue`.

Packed little-endian ticket ([S1 auth][s1-auth], no native alignment):

| Offset | Bytes | Field / reference value |
|---:|---:|---|
| 0 | 4 | magic `0xEFBDADDE`, bytes `DE AD BD EF` |
| 4 | 1 | type, reference 0 |
| 5 | 4 | title ID |
| 9 | 4 | issued Unix seconds |
| 13 | 4 | expiry, reference issued + 30000 |
| 17 | 8 | license ID, reference 0 |
| 25 | 8 | user ID |
| 33 | 64 | username, zero-filled fixed buffer |
| 97 | 24 | lobby session key |
| 121 | 3 | usingHashMagicNumber, zero |
| 124 | 4 | hash, zero |

Encrypted S1 client ticket: `Base64(3DES-EDE-CBC(Kauth24, Tiger(LE32(seed))[0:8], ticket128))`; no PKCS padding, ciphertext remains 128 bytes. Tiger is the raw 24-byte digest, not hex or Tiger2. [Crypto wrappers][s1-crypto] and [independent IV implementation/test][obe-crypto] establish truncation to 8 bytes; upstream vector seed 3223919485 -> IV `f2 19 5a 16 81 89 43 bd` (not executed here).

S1's `Kauth24 = decoded_token[32:56]` is artificial: [Steam ticket producer][s1-token] constructs `"S1" + zero-padding to 32 + caller key24 + userID8 + username64`. The auth consumer wrongly assigns the address `token.data()+56` to the numeric user-ID field rather than loading its bytes. Neither behavior is a CODOL format. S1 server ticket is `sessionKey24 || zero104`, base64 encoded, and session key is also shared in-process. Its opacity to the client is useful to a local auth/lobby pair, but its contents are an emulator convention.

IW7 emits `X-Signature: 1337` while [patching signature validation][iw7-patches]. That is not evidence an unmodified client accepts such a signature. A newer [RyuNET auth implementation][ryu-auth] separately uses plaintext ticket magic and n+1 reply tasks, but its Switch/CTR-specific field interpretations are not CODOL evidence.

## Lobby hello, key derivation, framing

[S1 lobby][s1-lobby] special-cases the initial word `200`/`0xC8`, skips another DWORD and hashes the remaining hello. [Independent handshake source][ryu-handshake] supplies the missing stream boundary: exactly **28 raw bytes**:

```
LE32(200) | LE32(200) | LE32(minVersion) | LE32(maxVersion)
| LE32(maxFrame) | nonce[8]
```

This is not a length-200 frame. Reference versions are 210..220. **The actual CODOL capture** `../../captures/20261014T034553490974-lobby-request.bin` is `c8000000c8000000d2000000d2000000000008006b8b867dafe4229e`: min=max=210, receive limit 0x80000, nonce `6b8b867dafe4229e`. Select 210. S1's exact 26-byte response is:

```
16 00 00 00 AB 81 D2 00 00 00 [13 37 repeated 8 times]
```

After hello, frames are `LE32(L) | AB | type | payload`, with L excluding the four length bytes. Zero-length ping is four zeros and is echoed. Handle fragmentation and multiple frames in a single TCP read. Do not hash recv-chunk boundaries.

On client-auth `AB 82`, transcript is `hello[8:28] || full_server_81_frame || full_client_82_frame_without_last8`. Both full frames include their original length DWORD. The last8 are the client proof; no public S1 parser establishes the opaque 0x82 ticket bitfield layout.

Read-only comparison with parent's saved `../lobby-keys-stun-decompiled.json`, `structuredContent.normalized_result.items[0].pseudocode`, function **0xa61980**, confirms the 210 check, reconstruction of the 20-byte client header plus full 26-byte server header and auth without proof, CLIENTCHAL length16 and BDDATA length72. Stack buffers local_ac[20], local_98[20], local_84[16], local_74[16] match the directional split below. No new REA call was made. Exact inbound encrypted task framing still needs a post-handshake CODOL capture.

[Key derivation][s1-keys] plus [independent direction definitions][ryu-crypto], with HMAC arguments explicitly `(key, message)`:

```
D = SHA1(transcript)
PRK = HMAC_SHA1(D, sessionKey24)
Expand(label, N):
  T1 = HMAC_SHA1(PRK, ASCII(label) || 01)
  Ti = HMAC_SHA1(PRK, T(i-1) || ASCII(label) || byte(i))
  return (T1 || T2 || ...)[0:N]
C = Expand("CLIENTCHAL",16)
B = Expand("BDDATA",72)
clientAuthProof = C[0:8]; serverAuthProof = C[8:16]
c2sHmac = B[0:20]; s2cHmac = B[20:40]
c2sAes = B[40:56]; s2cAes = B[56:72]
server_auth_done = LE32(10) || AB 83 || serverAuthProof
```

S1 only uses the s2c HMAC key; it extracts but does not validate inbound packet MAC/proof. Its char[24] session key is implicitly converted to a C string; the Python module uses exactly 24 bytes. The reference global transcript is also not suitable for reconnects: keep state per connection.

Established-session frame ([S1 reply][s1-reply], [S1 lobby][s1-lobby]):

```
LE32(30 + ciphertextLength) | AB 85 | LE32(sequence)
| IV[16] | AES-128-CBC(ciphertext) | HMAC_SHA1(directionKey, everythingBeforeTag)[0:8]
plaintext = LE32(payloadLength) | innerType | payload | zero padding to 16
```

The MAC includes the outer length DWORD; there is no PKCS#7 padding or extra block when already aligned. Server reply innerType=1 (`TASK_REPLY`). Client innerType=0x86; payload starts raw service-ID then typed task-ID (`03 task`), then typed parameters. S1 reads but ignores the inner length; its server writer excludes innerType from payloadLength. The implementation follows that writer and the independent parser, rejecting inconsistent lengths rather than guessing alternatives. S1's server IV is `5eed` repeated eight times; random 16-byte IVs also fit the explicit IV field.

## Storage and TASK_REPLY

All below service IDs/tasks are decimal. [S1 storage][s1-storage], [IW6 storage][iw6-storage], [IW7 storage][iw7-storage]:

| Reference | Service/task | Request after task ID |
|---|---|---|
| S1 / IW6 | 10/7 getPublisherFile | string filename |
| S1 / IW6 | 10/6 listPublisherFiles | u32 date, u16 maxResults, u16 offset, string filename/filter |
| IW7 | 10/21 getPublisherFile | string unknown/context, string filename |
| IW7 | 10/20 listAllPublisherFiles | extra leading string, then the 10/6 fields |
| IW6 | 10/3 | legacy **user-file** read, not publisher-file retrieval |
| IW6 | 10/1 | legacy user-file write, not publisher-file retrieval |

[Typed byte buffer][s1-buffer]: `u8=03 value`, `bool=01 value`, `u16=06 LE16`, `u32=08 LE32`, `u64=0A LE64`, `string=10 bytes 00`, `blob=13 08 LE32(length) rawBytes`. The nested `08` after `13` is required. These tags are bytes, unlike legacy auth's 5-bit tags.

[S1 TASK_REPLY][s1-taskreply] payload for success with N>0:

```
0A LE64(transactionID) | 08 LE32(0) | 03 taskID
| 08 LE32(N) | 08 LE32(N) | serializedResults
```

For N=0, S1/IW6/IW7 write **one** count `08 00000000`, omitting the second. For error they write `0A LE64(transactionID)` after taskID, with no counts. Transaction IDs are server counters, separate from the transport sequence. `bdFileData` is a single typed blob; it is not bdFileInfo or JSON. Missing publisher file -> error `BD_NO_FILE=1000/0x3E8` in these sources ([error enum][s1-errors]).

**Implemented bring-up exception:** 10/7 parses/logs any typed filename and returns success with **one actual empty bdFileData**, never zero objects. After the typed task ID, bytes are `08 01000000 | 08 01000000 | 13 08 00000000`. This is the source serializer applied to an empty file. Returning an empty file for every name is the requested local policy, not upstream's missing-file policy or evidence of real CODOL file contents. Other service/task pairs receive N=0 with their observed task ID; 10/3 is not aliased to publisher retrieval.

[File serializers][s1-results]: publisher list file info is typed `u32 fileSize, u64 fileID, u32 created, u32 modified, bool private, u64 owner, string filename`; IW7 appends a string checksum. Empty list and missing file differ. S1/IW6 fabricate fileID from the first 8 SHA1(filename) bytes interpreted LE, with times/owner zero for publisher files.

Sanity example: task7, transaction1, file bytes `abc` -> TASK_REPLY payload 35 bytes, AES input48, outer L=78 and total82. **One empty file** -> payload32, AES input48, outer L=78, total82. **Zero objects** -> payload21, AES input32, outer L=62, total66. Focused Python tests decrypt/check these sizes and typed fields; they are not captured game responses.

## STUN and older-protocol distinction

[S1 STUN][s1-stun] is Demonware's small UDP format, not RFC5389: request begins type/version/padding. Type30 -> `1F 02 00 | IPv4 network-order bytes | LE16(port)` (9 bytes). Type20 -> `15 02 00 | same external address | serverIPv4 | LE16(serverPort)` (15 bytes). The source reports localhost:3074 and a registry-derived server address; the Python helper reports the supplied endpoints, defaulting server endpoint to localhost:3074. CODOL version/behavior remains to be observed.

[IW6 transport][iw6-transport] is a different dialect: `LE32(L)|00|messageType|payload` or `LE32(L)|01|LE32(seed)|3DES-CBC(...)`. IV is Tiger(seed)[0:8], plaintext starts a four-byte checksum then message type, padded to 8. IW6 writes `DEADBEEF` as checksum and skips validating it. Do not transplant that transport into the AB/AES dialect. [Open BitDemon checksum][obe-message] uses an actual truncated HMAC, and its task reply emits two counts even for empty/error cases; this disagreement is why the module uses the S1/IW7 reply convention.

## CODOL runtime verification, 2026-10-14

The parent integrated this module and verified the actual client accepted the protocol-210 handshake, encrypted replies, and initial Demonware STUN responses. The client requested eight publisher filenames using service 10 / task 21, with a typed context string before the filename. The implementation now supports both task 7 and this observed task 21 variant. Returning one empty bdFileData per task-21 request reached the actual character-selection UI; a captured-request regression test covers the variant. The full auth/lobby suite passed 16 tests.

After the user selected a character, the client displayed the introductory training page and a server-busy warning. The last non-telemetry request was service 9 / task 16; the current stub returned error 0 and zero results. The connection stayed alive. The exact CODOL operation and warning branch remain unconfirmed; do not assign the IW6 service-21 task-16 name purely from the task number. See `../../docs/20261014-character-selection.md` for packet and screenshot evidence. The pre-integration scope and unknowns below describe the original worker handoff, not this later runtime result.

## Integration boundary, unknowns, and licensing

Only the parent can validate CODOL acceptance beyond hello. Remaining unknowns: encrypted task10 auth key; 0x82 embedded-ticket field structure; actual encrypted task traffic and requested storage task IDs/filenames/content; character/profile/entitlement records needed after lobby login. Header/transcript/KDF layout is now supported by the saved CODOL decompilation as well as public source. There was no literal DW3/internal-2.1.0/CODOL match in the downloaded C++/Rust sources. SDK label/year alone does not establish compatibility.

The authorized `../../src/dw_lobby.py` exposes `handle_lobby(sock, peer, record, save_capture, *, session_key=SESSION_KEY)` and pure helper `stun_reply(packet, peer, server=('127.0.0.1',3074))`. The lobby has per-connection state, shared session key, filename/task-ID logging, one empty file for 10/7 and zero-result stubs otherwise. It neither binds sockets nor starts services on import. Caller owns accepted socket lifecycle, timeouts, localhost binding and capture callbacks. Auth and local_server.py are outside this implementation scope. Unknown wire types, malformed publisher filename or failed proofs/MACs are recorded and stop the handler instead of receiving an invented reply.

Validation: `python -B -m unittest discover -s tests -p test_dw_lobby.py -v` from CODOL-Revival. The tests use an in-memory socket and capture callbacks, actual 28-byte hello, and a synthetic opaque auth payload with independently derived client-side keys (cryptography HKDFExpand versus module stdlib HMAC expansion). They verify fragmentation/coalescing, ordinary post-hello length200, directional proofs/MAC/AES, TASK_REPLY counts/blob/task ID, fresh counters, malformed/truncated input and STUN byte order. No listeners, game launches, service restarts or real-client lobby acceptance are claimed by these tests.

Attribution: AlterWare s1-mod and iw6-mod LICENSE files are GPL-3.0; auroramod/iw7-mod is GPL-3.0; Laupetin/open-bitdemon-emulator is AGPL-3.0. Ryu7w7/ryunet-demonware-ctr LICENSE.md is PolyForm Shield 1.0.0, not a permissive OSS license. Downloaded source retains its upstream license text. The Python module is newly written from the documented wire formats; no C++/Rust/Go source blocks are vendored into it. This note records source provenance without asserting license compatibility for future redistribution.

Pinned repositories:
- https://git.alterware.dev/alterware/s1-mod @ `f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef`
- https://git.alterware.dev/alterware/iw6-mod @ `b54b3f51aff244a27d309bc0775f450aa236c2f3`
- https://github.com/auroramod/iw7-mod @ `37abcb260408ce7cdef0dde831bbfcad594510e3`
- https://github.com/Laupetin/open-bitdemon-emulator @ `e2324e95516210a949a646c6b57fa4df70011442`
- https://github.com/Ryu7w7/ryunet-demonware-ctr @ `9560e81650e40068cf54705127557e66e65ab308`

[auth-enums]: https://github.com/Laupetin/open-bitdemon-emulator/blob/e2324e95516210a949a646c6b57fa4df70011442/libbitdemon/src/auth/auth_handler/mod.rs#L11
[s1-auth]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/demonware/servers/auth3_server.cpp#L13
[iw7-auth]: https://github.com/auroramod/iw7-mod/blob/37abcb260408ce7cdef0dde831bbfcad594510e3/src/client/game/demonware/servers/auth3_server.cpp#L40
[s1-crypto]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/common/utils/cryptography.cpp#L404
[obe-crypto]: https://github.com/Laupetin/open-bitdemon-emulator/blob/e2324e95516210a949a646c6b57fa4df70011442/libbitdemon/src/crypto/mod.rs#L20
[s1-token]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/steam/interfaces/user.cpp#L131
[iw7-patches]: https://github.com/auroramod/iw7-mod/blob/37abcb260408ce7cdef0dde831bbfcad594510e3/src/client/component/demonware.cpp#L543
[ryu-auth]: https://github.com/Ryu7w7/ryunet-demonware-ctr/blob/9560e81650e40068cf54705127557e66e65ab308/server/auth.go#L89
[s1-lobby]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/demonware/servers/lobby_server.cpp#L38
[ryu-handshake]: https://github.com/Ryu7w7/ryunet-demonware-ctr/blob/9560e81650e40068cf54705127557e66e65ab308/server/handshake.go#L7
[s1-keys]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/demonware/keys.cpp#L20
[ryu-crypto]: https://github.com/Ryu7w7/ryunet-demonware-ctr/blob/9560e81650e40068cf54705127557e66e65ab308/server/bdcrypto.go#L62
[s1-reply]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/demonware/reply.cpp#L23
[s1-storage]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/demonware/services/bdStorage.cpp#L22
[iw6-storage]: https://git.alterware.dev/alterware/iw6-mod/src/commit/b54b3f51aff244a27d309bc0775f450aa236c2f3/src/client/game/demonware/services/bdStorage.cpp#L24
[iw7-storage]: https://github.com/auroramod/iw7-mod/blob/37abcb260408ce7cdef0dde831bbfcad594510e3/src/client/game/demonware/services/bdStorage.cpp#L14
[s1-buffer]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/demonware/byte_buffer.cpp#L155
[s1-taskreply]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/demonware/reply.hpp#L114
[s1-results]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/demonware/data_types.hpp#L21
[s1-errors]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/structs.hpp#L409
[s1-stun]: https://git.alterware.dev/alterware/s1-mod/src/commit/f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef/src/client/game/demonware/servers/stun_server.cpp#L8
[iw6-transport]: https://git.alterware.dev/alterware/iw6-mod/src/commit/b54b3f51aff244a27d309bc0775f450aa236c2f3/src/client/game/demonware/service_server.cpp#L22
[obe-message]: https://github.com/Laupetin/open-bitdemon-emulator/blob/e2324e95516210a949a646c6b57fa4df70011442/libbitdemon/src/messaging/bd_message.rs#L19
