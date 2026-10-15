# Source attribution

Tiger implementation and tables: adapted from Tom St Denis, LibTomCrypt, `sh1x_dedicated/src/tomcrypt/hashes/tiger.c`. Source SHA-256: `1620b851f8c2d968b29391c422d3140dd6669a4fafe350b62a0e2bd7489d0069`.

/* LibTomCrypt, modular cryptographic library -- Tom St Denis
 *
 * LibTomCrypt is a library that provides various cryptographic
 * algorithms in a highly modular and flexible manner.
 *
 * The library is free for all purposes without any express
 * guarantee it works.
 *
 * Tom St Denis, tomstdenis@gmail.com, http://libtom.org
 */

This project's Python port changes the implementation language; it does not load or link the old server.

Handshake and DATA framing are a Python adaptation of the following AGPL-3.0-or-later files from the user-provided `sh1x_dedicated` tree. Original notices are retained in the archive. Protocol behavior is additionally checked against CODOL 3.3.3.3 client code.

- `codol_handshake.c`: SHA-256 `f9be49f76c6d1a66e1ff520cc47c2456ae53b0346b7654a87f6c0a5b2f9702b1`
- `codol_ecdh.c`: SHA-256 `b3a0d1b26b09c78f5d1e0d61eb6a7ac51552b07ff9bce014d7eb082e9569cbf7`
- `codol_crypto.c`: SHA-256 `caad3e3ce1a8f68172c5b99f2fad5b6bb80472d8a568c5852ec4e07f4f406fb8`
- `codol_wire.c`: SHA-256 `516c28d6b237554b4205ae4e652f12c1af24fa94952112b5213f59f7ff59f6f8`

Connection/userinfo parsing follows `codol_connect.c` and the current-client OOB evidence at `0x466790`. Stats assembly follows the current 423 adaptation of `codol_stats.c` in the archived `server3333` source; the fragment format is tested using the shipped client's `0x6d81a0` writer. Reference hashes: connect `4e0de96c02584aa67d3f1797aac010ec61d8cb07b607ab963fec2245d3c2aba9`; stats `ce86943bdc895136b0e75050ca2b13ef1ea1cef4f6152f8e837b7fdde4964c36`.

Input and snapshot algorithms selectively translated from the archived 423 adaptation under the same AGPL-3.0-or-later license. These modules encode independent Python state directly; they do not use the old engine or its layout adapter. Source SHA-256:

- `codol_usercmd.c`: `58e778941162b38179c35a89c03ebc4f7e19f84e54fd17e3e00811406477eb5c`
- `codol_2697_arrays.c`: `465b3bfc9cb0843d0ee3f0c99d32329f32f966fdeed96133454d72e302937351`
- `codol_2697_entities.c`: `306e9c4400b0fc4af9f4448eefffd95e85a33da4ec8bb4ef8c2f544b67df2bac`
- `codol_2697_clients.c`: `8c212c973694e0da7c1d142809e004d182d27b00c2ee92a0e67fdc2269fc8e5d`
- `codol_2697_delta.c`: `74e73807a7349dc9eaa9b3170f9d11c9c4e43f8f08427bd7493b591ba9ce63a5`

The field tables in `data/match-fields423.json` are extracted from the current client, identified by the recorded SHA-256 and addresses. The input writer and snapshot reader tests execute that client code; source portability alone is not a compatibility claim.

Standing movement and waypoint navigation selectively translate the algorithms
in the following AGPL-3.0-or-later reference files. Python owns the player state;
no native player layout, assembly engine or native runtime is used.

- `src/codol/player/codol_pmove_c1_ground.c`: `546ee852eb82bb72523c1db95efc17c7bf7d9326f83f6405c0b7c69e68b70588`
- `src/codol/player/codol_bot_nav.c`: `9e928b94b009f5de45b696b356850881ed6712da39a970948d5f9042a2681518`
- Current weapon offsets, archived `server3333/src/codol/weapon/codol_weapon_2697.c`: `a81de9bfb5039884f860fcb61180034fb489fff68e8141b619f5d8acc8c64909`

The minimal AI reaction, single-rifle damage rules and respawn policy are this
project's implementation. They do not claim to reproduce the original game's
complete bot behavior, perks, penetration, body-part damage or movement modes.
Waypoint and game resource bytes stay in ignored local bundles with input hashes.
