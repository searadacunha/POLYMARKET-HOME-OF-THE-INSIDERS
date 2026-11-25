# Reproduce

From the repository root, with Python 3.10 or newer and no extra packages:

```bash
python3 -m unittest investigations/fresh-wallet-clusters/tests/test_logic.py
python3 investigations/fresh-wallet-clusters/scripts/fwc/pipeline.py all
python3 investigations/fresh-wallet-clusters/scripts/verify.py
```

`pipeline.py all` is resumable. It writes `investigations/fresh-wallet-clusters/data/cache.sqlite` (gitignored) and the CSV files in `data/`. A market that errors is retried on the next launch. A market that hit the page cap stays `too_deep` and stays out of the rates. If `preregistration.json` changes after the cache exists, the pipeline refuses to continue.

The network steps call the public Gamma API, the public data API, and the public Polygon endpoints listed in `pipeline.py`. They send no key and no order. Profile text fields from the activity API are discarded and are not written to the cache.

`verify.py` reruns the offline tests and checks that `FINDINGS.md` quotes the verdict stored in `data/stats.json`. It does not download the tapes again. The collection cache is gitignored and is not in this commit: a raw SQLite tape of this size is above the repository scan limit. Rebuilding the numbers from a cache, on a machine that still has one, is:

```bash
python3 investigations/fresh-wallet-clusters/scripts/fwc/pipeline.py analyze
```

That command reads the cache only. It still requires the cache, which is local to the machine that collected it.
