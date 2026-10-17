# Offline publisher sources

`configs_s.ini` and `market_ui.ini` are the readable configuration behind the
previous local 3.19 server's publisher downloads. They contain service settings
and item labels, not a player's inventory or game executables. Keep their text
as source; do not distribute encrypted downloads or keys.

`client/publisher.py` generates the other offline responses explicitly. The
playlist comes from the user's original signed `mp_playlists.ff`: only the NAT
requirement, minimum player count and lobby delay are changed. Local advertising
and NotForSale endpoints return empty lists; no external image bundle is needed.

The matching original EXE supplies the wrapped configuration key. Native
functions `0x66d0d0` and `0x66d1f0` establish RSA-OAEP/SHA256 and AES-192 CTR
(big endian counter, IV = little endian payload length followed by twelve 01
bytes). Fastfile encryption uses a different counter convention. The original
EXE fingerprint is checked before either key is read.
