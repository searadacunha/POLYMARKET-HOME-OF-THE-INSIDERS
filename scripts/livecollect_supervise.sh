#!/bin/sh
# Restart the collector when it exits. This is not a system service.
# Usage: scripts/livecollect_supervise.sh markets.json /var/phi
set -u
markets=$1
out=$2
mkdir -p "$out"
seconds=${PHI_SECONDS:-3600}
while true; do
  python3 -m monitoring.livecollect collect --markets "$markets" --out "$out" --seconds "$seconds"
  printf '%s restart\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$out/restarts.log"
  sleep 2
done
