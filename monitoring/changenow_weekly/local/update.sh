#!/bin/sh
# Refresh the weekly ChangeNOW report from a local checkout. Reads new settled blocks, rebuilds the files, pushes nothing.
#   CHANGENOW_RAW       folder for raw rows and checkpoints (default: ~/.local/state/changenow-weekly/raw)
#   CHANGENOW_ENV_FILE  optional file holding a line ETHERSCAN_API_KEY=... ; the key is exported, never printed
set -eu
cd "$(dirname "$0")/../.."
RAW="${CHANGENOW_RAW:-$HOME/.local/state/changenow-weekly/raw}"
mkdir -p "$RAW"
if [ -z "${ETHERSCAN_API_KEY:-}" ] && [ -n "${CHANGENOW_ENV_FILE:-}" ] && [ -r "$CHANGENOW_ENV_FILE" ]; then
  ETHERSCAN_API_KEY=$(sed -n 's/^ETHERSCAN_API_KEY=//p' "$CHANGENOW_ENV_FILE" | head -n 1 | tr -d "\"'")
  export ETHERSCAN_API_KEY
fi
python3 -m changenow_weekly update --raw "$RAW"
python3 -m changenow_weekly verify
