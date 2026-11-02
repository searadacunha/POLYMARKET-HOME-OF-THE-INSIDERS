# 2026 Ballon d'Or, wallet by wallet

Rebuild, wallet by wallet, the activity and flows of the 11 accounts publicly named around the 2026 Ballon d'Or markets, then test the collective signal under a frozen protocol.

**State:** Report v3, corrected after audit and completed with flow-trace. The study is not closed: `collective/results.md` and the freeze still carry the earlier readings, and the amendment lists the open decisions. An address is not a person: no identity is established or sought here.

## Reproduce

Scripts in `sources/tools/` and `sources/collective/code/`. Raw responses (`state/http_cache/`, `collective/state/`) are not published, so a new run queries the network.

## Contents

Snapshot of November 2, 2026. `sources/` is a verbatim copy of the original working tree, mostly in French, with relative paths kept. `data_manifest.json` lists every original file, published or not, and why. `local_only_hashes.sha256.gz`, when present, holds the hashes of large unpublished sets.

- [Status](STATUS.md)
- [Classified findings](FINDINGS.md)
- [Evidence and hashes](EVIDENCE.md)
