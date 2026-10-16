# Source attribution

This Rust implementation translates CODOL-Revival's independent Python match
server under AGPL-3.0-or-later. The algorithms selectively adapted from
`sh1x_dedicated` and their original source notices are recorded in
[the match-server notice](../../tools/reference_match/NOTICE.md).

It does not link or launch the old engine. Game assets stay in ignored local
map packages. Synthetic collision fixtures contain no game resources. The
protocol field tables describe the currently verified 3.3.3.3 wire contract.

The DATA protocol uses SHA-1, AES-128-CTR and HMAC as required by the current
client; it does not inherit the reference engine's Tiger192 DATA mode.
