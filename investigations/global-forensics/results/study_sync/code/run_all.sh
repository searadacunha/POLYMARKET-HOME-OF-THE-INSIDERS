#!/bin/bash
# Entry point after the freeze. Reads only the frozen table.
set -euo pipefail
cd "$(dirname "$0")"
python3 ana_20_primary.py
python3 ana_40_catalog.py
python3 ana_30_null.py
