# Third-party notices

PolySentinel's own code imports the packages below. No third-party source code is copied into this repository. Exact versions are pinned in `requirements.lock`.

| Package | Version | License | Why it is here |
|---|---|---|---|
| httpx | 0.28.1 | BSD-3-Clause | HTTP client |
| networkx | 3.4.2 | BSD-3-Clause | Funding graph |
| anyio | 4.15.1 | MIT | Dependency of httpx |
| certifi | 2026.10.23 | MPL-2.0 | Dependency of httpx |
| h11 | 0.16.0 | MIT | Dependency of httpx |
| httpcore | 1.0.9 | BSD-3-Clause | Dependency of httpx |
| idna | 3.20 | BSD-3-Clause | Dependency of httpx |
| typing-extensions | 4.16.0 | PSF-2.0 | Dependency of anyio |

Each package keeps its own license, shipped with the package when installed.

Exchange event signatures and contract addresses in `config/contracts.json` come from public contracts and their published interfaces.

`signal_engine/fund_flow/wallets.py` rebuilds Polymarket's proxy deployment bytes to check addresses by CREATE2. The layout comes from Polymarket's published `proxy-factories` (LGPL-3.0) and is used as a fact about deployed contracts; no source file is copied. `signal_engine/fund_flow/labels.json` holds addresses published by Polymarket and Relay, each with its source.
