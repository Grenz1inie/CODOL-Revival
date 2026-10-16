# Tiger source attribution

`tiger_tables.py` contains the standard Tiger S-boxes from Tom St Denis,
LibTomCrypt (`src/hashes/tiger.c`). The existing repository table is reused;
its reference source SHA-256 is
`1620b851f8c2d968b29391c422d3140dd6669a4fafe350b62a0e2bd7489d0069`.
It contains no game-specific addresses or extracted client bytes.

The Tiger implementation in `local_auth_ticket.py` retains its original
LibTomCrypt attribution. It no longer reads a game memory dump for constants.

> LibTomCrypt, modular cryptographic library -- Tom St Denis
>
> LibTomCrypt is a library that provides various cryptographic
> algorithms in a highly modular and flexible manner.
>
> The library is free for all purposes without any express
> guarantee it works.
>
> Tom St Denis, tomstdenis@gmail.com, http://libtom.org
