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
Ready bots are a local implementation policy, not a recovered original-server
rule. Actual host admission, channel routing and UI remain unverified.
