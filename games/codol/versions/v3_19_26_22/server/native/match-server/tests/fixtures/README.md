# Synthetic native room fixture

`roster-native.bin` is generated from synthetic room members, not game resources.
3.19.26.22 original EXE SHA-256:
`36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537`.
Native constructor `0x623770`, writer `0x627d80 -> 0x623880`, reader
`0x627e00 -> 0x623de0`, executed in Unicorn with the hash-checked snapshots
used by `tests/client_inventory319.py`.

Inputs: human UID 1000001, bot UIDs 0x600000001 through 0x600000011;
first nine members team 1, last nine team 2; all ready; remaining fields use
native constructor defaults. Names do not appear in this message.
Message 14 contains 9851 bits / 1232 bytes, SHA-256
`484fcfd562143fa1ffaf6d4538a210f94440457fdf61ec6b96e2b68469ef2520`.

REA member schema evidence:
`ev_3b691284ae848e8f5423e623f021d2051084ef3f72b7ef4e6ce59b210de10538`.
Writer evidence:
`ev_805ec1699a24f81ab2301998997c30e94940bfd2d2526fea73e47b15cabd6f0c`.
Coverage is native serialization/deserialization only. Live channel routing,
waiting-room UI, map loading and gameplay remain separate acceptance steps.

`join-native.bin` is a synthetic single-bot admission request, message 6.
Native writer `0x6270d0`, reader `0x627230`; 722 bits / 91 bytes, SHA-256
`4a44e521a3982b2fcaa4fcd66e0a690096db97578d482b041ce3d2f3a1a6fa25`.
Input: UID 0x600000001, team 1, ready 1, skill 1000, compatibility byte
at member +0x1b0 equal to 1, remaining member fields from `0x623770`;
party count 1, empty password/clan, content version 797, other trailers 0.
The content version is checked by `0x634870` against `0x7b25a38`; a bounded
read of PID81072 confirmed 797, without modifying the client.
REA evidence `ev_5f69d4787bea7c73fabbb407d2d15c82fc297a2c3e2174b3a8c18b6f2f5448f8`.
The Rust test also replays all 17 requests through both native functions.
These historical fixtures retain ready=1. The local human-Ready policy clears
only the documented ready bits in expected bytes; the native writer/reader
replay independently verifies ready=0. Host admission and Bot01-Bot17 names
have since been confirmed in the real waiting room; the new start policy and
gameplay still require separate live acceptance.

## Synthetic UDP stats fixtures

The three `stats-*-zlib.bin` files contain Python `zlib.compress` output from
`bytes(i % 251 for i in range(length))`, with lengths 32768 (`stats-zlib.bin`),
32767 (`stats-short-zlib.bin`) and 32769 (`stats-long-zlib.bin`). They contain
no player data or game assets. SHA-256, in that order:

- `40a07178ba94810350c389c5571f9c639e2dff20c36101b8076d1ae994f3fa20`
- `63a4aa500da7846e20e4755c20f303da559f73a9bc2034807406f0aed1acb239`
- `14d9b4db1975a01024bc4897fc94a920e91e876458c514de87c45b77fe3ba513`

`tests/client_transport319.py` executes native `0x7f6ec0` to generate raw and
compressed upload fragments; the compressed input is precomputed by Python,
so this does not validate the game's compression routine. It also executes
native `0x470a60` to consume Rust server envelopes with four command cases.
The original EXE identity is the hash above. REA analysis image `udp319.exe`
SHA-256 is `f4f06040b1c6fe03b3e24c9aeb927a4fcbc581c37edc3ada6d941564fbd3fc68`;
local evidence and snapshot are `work/codol319-nuketown/udp-rea.evidence.json`
and `udp-rea.snapshot.json`. Set `CODOL319_NATIVE_PYTHON` to run these replays;
without that variable native checks are skipped. Live Nuketown UDP, game
state, movement and AI remain unverified.

## Real move packet fixtures (2026-10-17 Nuketown session)

`move319-head.json` (frames 676..735), `move319-moving.json` (frames
3420..3500, the window where the user held LEFT) and `move319-tail.json`
(frames 322643..322664) are real client datagrams from
`work/codol319-map-live-20261017/session.pcapng` (client port 58436, Rust
UDP 28970, challenge 0, no server commands published). Each record carries
the raw packet plus the usercmds decoded by the verified parser
`match_host/client_message319.py` (inverse of native writer `0x66f410`;
usercmd key from `0x5b2e96` is the packet's server ack here), with the
baseline chained from the session's first move packet and conditional byte
fields materialized. `move319-trajectory.json` is the reference movement
output of `work/codol319-move-input/move_reference319.py`: per-command
origin/velocity/angles through the live_sim319 no-collision integrator with
C1 wish scaling and 16-unit reconcile, plus four snapshot byte references
from `snapshot_codec319.py`. No game assets or player data beyond the
loopback capture are included.

The same capture shows the client's own predicted origin never moved while
LEFT was held for ~1.3 s (buttons bit 0x8000000 held, fire bit pressed
early): client-side prediction was frozen in that run. The fixtures
therefore verify decode and server-side movement only, not that the client
moves itself; see the Nuketown wiki's movement section.
