# Backup of mission 5 on the VERBATIM disk (verified 2026-11-17, 15:00–15:10 UTC)

Destination: `/Volumes/VERBATIM HD/phi-x/investigations/collective-exposure-shifts/falsification-final-20261117/`
(FAT32 USB disk, mechanical). Each file was copied, then its bytes were read back from the disk and compared by
SHA-256 with the source. Directories of many small files are stored as one uncompressed tar, and every member
inside the tar was hashed and compared with its source file. Script: a session-scratch copy of
`copy_verify.py` (not kept in the study); the hashes are in each destination's `MANIFEST.sha256.json`.

| Copy | Source | Files | Verified | Mismatch | Notes |
|---|---|---:|---:|---:|---|
| `raw/` | `~/Projects/Polymarket-collective-falsification-raw-20261117/` | 7,030 | 7,030 | 0 | the 3 tape databases (8.3 GB) copied as files; `funding_cache/` and `funding_cache_first100/` as `.tar` |
| `study/` | `~/Projects/Polymarket-collective-falsification-20261117/` | 22,337 | 22,337 | 0 | see below for `out/phase_a_cache.tar` |

`out/phase_a_cache` (21,948 regenerable detector-cache files, 846 MB):
1. First attempt (Python `tarfile` written straight to the disk): the 881 MB archive read back with only 11,906
   members, so 10,043 files failed verification. The archive is kept as
   `study/out/phase_a_cache.tar.failed-readback-20261117`. It is not a valid copy.
2. Second attempt: the archive was built on the internal disk (sha256 `4bdd4379…63232e2`, 21,948 `.pkl` members)
   and copied to the disk, where it read back with the same SHA-256. All 21,948 members were then hashed inside
   the copy and compared with the source files: 0 mismatch, 0 missing. (The archive also holds 21,950 macOS
   AppleDouble `._*` metadata entries, ignored.)

Files changed after the study copy (this file and the final report) were copied and checked one by one. Their
hashes are in `BACKUP_VERBATIM.sha256`, both in the study and on the disk.

**Not covered.**
- The continuous backup `phi-backup` (external disk pack + GitHub Releases) still holds none of this study. Every
  `backup` pass fails with `KeyError: 'Polymarket-early-detection-raw-20261113'`: 729 `pass_failed` events, the last
  at 14:57 UTC.
- Its status (14:28 UTC) shows 22,229 of 22,232 study files and 5,982 of 5,982 raw files still waiting.
- There is therefore **one** verified copy (this disk) besides the Mac, and no off-site copy. phi-backup was not
  modified by this mission.

The folder `…/collective-exposure-shifts/falsification/` on the same disk is **not** a copy of this study. It holds
only the first, pre-audit population scripts and files written before macOS revoked access to the disk at
12:13 UTC.
