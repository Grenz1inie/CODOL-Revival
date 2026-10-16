# Frozen migration reference

Python match implementation at `e3ddc7d`, relocated without algorithm changes.
Used only by differential tests, offline map exporters and protocol research.
Production `games/codol/versions/v3_3_3_3/server/local_server.py` starts the Rust executable; no selector or
fallback starts this Python server.

Do not implement new match behavior here. The benchmark keeps this baseline
until Rust gameplay acceptance. Resource-export helpers still use its collision
queries outside the game loop. Source attribution is in [NOTICE.md](NOTICE.md).
