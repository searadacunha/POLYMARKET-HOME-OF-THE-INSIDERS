# PolySentinel, prospective monitoring of Polymarket

Watch public Polymarket activity locally and read-only, flag unusual behaviour, seal each decision in a hash chain, and produce files an analyst can verify on chain. An alert is a reason to look, never a finding of wrongdoing.

**State:** Collector and prospective registry running at snapshot time. The pipeline replay is unfinished: only scenario S_A is sealed. The signal engine runs in shadow mode. No ground truth exists.

## Reproduce

From `sources/`, with Python 3.12 and `requirements.lock`: `python -m unittest discover -s tests` (see `sources/README.md`). The SQLite database, generated reports and sealed journals are not published: see the manifest.

## Contents

Snapshot of November 2, 2026. `sources/` is a verbatim copy of the original working tree, mostly in French, with relative paths kept. `data_manifest.json` lists every original file, published or not, and why. `local_only_hashes.sha256.gz`, when present, holds the hashes of large unpublished sets.

- [Status](STATUS.md)
- [Classified findings](FINDINGS.md)
- [Evidence and hashes](EVIDENCE.md)
