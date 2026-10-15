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
