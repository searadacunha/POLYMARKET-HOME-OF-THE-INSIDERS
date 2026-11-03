#!/bin/bash
# Entry point after the freeze. Reads only the frozen table and the outcomes file named by the amendment that closes the holdout.
set -euo pipefail
cd "$(dirname "$0")"
python3 ana_10_primary.py "$1"
