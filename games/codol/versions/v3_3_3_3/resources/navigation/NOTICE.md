# Nuketown reference navigation

`mp_nuked_wp.csv` is the unchanged 235-node reference graph supplied with the
local `sh1x_dedicated/bin/home/main/waypoints` tree. SHA-256:
`dae775b788537a20e64b72524eecf1847f40f02e7a1070a69687441f77d69807`.

That tree's `docs/CODOL_COMBAT_TRAINING_BOTS_20260915.md` records the original
data location as `alpha0022/resources/waypoints` within the 1.1.1.13 server
distribution. Its Git tree has no committed history or configured remote;
the CSV has no author or license header. The server README declares AGPL3
for the server, but no separate license for this data was found. This notice
records the verified provenance without assigning an unverified license.
Repository inclusion was explicitly approved on 2026-10-17; see
`docs/adr/0001-codol3333-navigation-input.md` at the repository root.

This is a reference graph, not navigation extracted from the 3.3.3.3 client.
The runtime checks traversed edges against the current map's collision data.
Map, model, collision and weapon payloads are generated locally from the
selected matching game installation and are not included here.
