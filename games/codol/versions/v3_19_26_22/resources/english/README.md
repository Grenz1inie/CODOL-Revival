# Rebuildable English resource sources

These UTF-8 texts preserve the established offline English translation from
`CODOL319-TestBuild`. The JSON stores only changed localization strings and
version-specific shared-string relocation deltas; it contains no encrypted
fastfile, archive, executable, key, font or texture. Numbered strings identify
the original fastfile's asset records. Unchanged resources come from the user's
matching original game. Translation quality is retained, not revised here.

`client/localization.py` verifies each original decoded zone's SHA-256, replaces
inline text, relocates the specified material/string-table/localization pointers,
and verifies the complete resulting zone against the established translation.
This deliberately supports only these two known boot resources.

Original 3.19 consumer evidence:

- `0x483a50`: RSA-wrapped AES-192 key/IV in the fastfile.
- `0x483b40`: unsigned fastfiles decrypt only their initial 256 KiB I/O buffer.
- `0x484880`: later unsigned buffers go directly to zlib, without AES.
- IFS `nifs` header: digest table offset at `0x24`, block count at `0x4c`;
  16 KiB blocks have MD5 digests, followed by the MD5 of that digest table.

Verification on the matching original archive: both decoded zones and encoded
fastfiles match the previous translation byte for byte. Rebuilding the complete
40,412,080-byte archive, including its digest table, gives SHA-256
`ac5e1d194833cbedfe0e9d8b476b2e1d9f93414d01e0e49601a80abfe89ea981`.
No old startup package is required to run this transformation. Generated game
resources remain local and ignored by Git. Tests cover shared references,
untouched assets, input/result identity, I/O encryption boundaries, capacity,
block digests and the digest-table checksum.
