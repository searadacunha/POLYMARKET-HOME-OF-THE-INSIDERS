# 2026 Ballon d'Or, wallet by wallet

Rebuild, wallet by wallet, the activity and flows of the 11 accounts publicly named around the 2026 Ballon d'Or markets, then test the collective signal under a frozen protocol.

**State:** Report v3 is finished, corrected after audit and completed with flow-trace. The frozen study is not closed: `collective/results.md` and the freeze still carry the earlier readings, and the amendment lists the open decisions. An address is not a person: no identity is established or sought here.

## Reproduce

Scripts in `sources/tools/` and `sources/collective/code/`. Raw responses (`state/http_cache/`, `collective/state/`) are not published, so a new run queries the network.

Report v3 rebuilds from the archived version 1, tested from a fresh clone, no network, nothing written without `--ecrire`:

```bash
cd sources && python3 -B tools/appliquer_amendement_20261102.py
# prints the SHA-256 07216e205caaab0d94c38d0337e663b7e7e4b68cd024ecc1c49237cf73f62f8d
```

The counter-verification is in `sources/tools/cv_*.py`, its outputs in `sources/evidence/contre_verification_20261102/`. Scripts that replay the HTTP cache need the original machine. Those that read the chain query public nodes. According to [Relay's official documentation](https://docs.relay.link/references/api/get-requests-v2), checked November 4, 2026, `requests/v2` is deprecated and scheduled for retirement on November 24, 2026; its v3 successor requires authentication.

## Contents

Snapshot of November 2, 2026. `sources/` is a verbatim copy of the original working tree, mostly in French, with relative paths kept. `data_manifest.json` lists every original file, published or not, and why. `local_only_hashes.sha256.gz`, when present, holds the hashes of large unpublished sets.

- [Status](STATUS.md)
- [Classified findings](FINDINGS.md)
- [Evidence and hashes](EVIDENCE.md)
- Corrections, each with its old claim, evidence and reason: `sources/reports/AMENDEMENT_AUDIT_2026-11-02.md`, in French
- Table of conclusions, audit checked point by point, the 17 cut histories: `sources/reports/CONTRE_VERIFICATION.md`, in French
