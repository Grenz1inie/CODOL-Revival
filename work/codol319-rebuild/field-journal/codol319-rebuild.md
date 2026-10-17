# 3.19 rebuild: resource generation and runtime export

Scope: original 3.19 x86 game, authorized offline resource reconstruction and
bounded read-only observation. Original EXE SHA256:
36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537.
Route: reverse-skill-router -> ghidra-reverse; case manifest and route output
are in the parent directory. Ghidra 12.1.4/Capstone were used; no automation of
game menus or gameplay, no restart of the existing game/services.

Findings incorporated into source:
- Original IFS2 matches the existing source reader's supported ABI.
- Unsigned FF decrypts only the first 256 KiB I/O buffer, not later buffers.
- IFS integrity includes per-16 KiB MD5 and an MD5 of the digest table.
- Public DDL offsets include both bits and bytes. Validate only selected typed
  byte offsets and their widths, not the entire offset array as byte addresses.
- Publish loaded common resources before inventory requests; extract the current
  map after gamestateupdate 6 and before the initial snapshot. Fixed-PID maps
  and historical full-memory dumps are not runtime inputs.

Evidence: fresh-prepare-result.json, live-export-result.json, final-tests.log,
marketplace-followup.log, ifs-native/ and the source-controlled boundary tests.
Full English archive rebuilt exactly (SHA256 ac5e1d194833cbedfe0e9d8b476b2e1d9f93414d01e0e49601a80abfe89ea981).
Live common export: 40635 item mappings and dependent tables, 1.31 seconds.
Full suite ran once: 473 tests / 358.2 s; 2 existing 3.3 snapshot assertions,
1 marketplace fixture omitted readiness; fixture corrected, 6 focused tests pass.
Fresh-prepare script first stopped after successful copy because its synthetic
nickname exceeded the existing 15-character limit; corrected the fixture and
verified cache reuse, progress preservation and unchanged original inputs.

Remaining acceptance: a user-initiated new session with the rebuilt components,
manual lobby and Seatown play. Existing live process remains on its prior build.
Skill package referenced RULES.md and tool-index.md that were absent; generated
tool inventory and this journal were kept within the authorized task workspace.
