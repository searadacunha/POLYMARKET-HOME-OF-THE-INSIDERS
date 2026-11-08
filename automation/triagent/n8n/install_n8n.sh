#!/bin/sh
# Install n8n for TriAgent as its own per-user launchd service, loopback only, and import the V2 workflow INACTIVE.
#   sh install_n8n.sh                                   code in ~/.local/lib/triagent-n8n (disk guard: ~3.8 GB)
#   N8N_IMAGE=/Volumes/X/TriAgent-n8n.sparsebundle sh install_n8n.sh
#                                                       code inside that disk image, mounted at start if needed
# n8n 2.46.6 is about 2.7 GB on disk (2 300 npm packages, measured from the lockfile on 2026-11-07). Its database
# and logs stay on the internal disk in either case (small, and SQLite stalls on a mechanical disk).
# Activation is NOT done here: see README, "n8n orchestration".
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
VERSION="${N8N_VERSION:-2.46.6}"
NODE_BIN="${N8N_NODE_BIN:-/opt/homebrew/opt/node@24/bin}"   # n8n 2.x supports Node 24; Node 26 is not tested
IMAGE="${N8N_IMAGE:-}"
MNT=/Volumes/TriAgent-n8n
STATE="$HOME/.local/state/triagent-n8n"
CONF="$HOME/.config/triagent"
PLIST="$HOME/Library/LaunchAgents/com.benjamin.triagent-n8n.plist"
GUARD="$HOME/.local/lib/disk-guard/diskguard.py"
PY=/opt/homebrew/bin/python3.12

"$NODE_BIN/node" -e 'process.exit(+process.versions.node.split(".")[0] >= 24 ? 0 : 1)' || { echo "Node 24+ needed at $NODE_BIN"; exit 1; }
mkdir -p "$STATE/logs"
chmod 700 "$STATE"
if [ -n "$IMAGE" ]; then
  [ -d "$MNT" ] || hdiutil attach -nobrowse -owners on "$IMAGE" >/dev/null
  LIB="$MNT/lib"; CACHE="$MNT/npm-cache"; export TMPDIR="$MNT/tmp"
  mkdir -p "$LIB" "$CACHE" "$TMPDIR"
else
  LIB="$HOME/.local/lib/triagent-n8n"; CACHE="$LIB/.npm-cache-install"
  mkdir -p "$LIB"
fi
N8N="$LIB/node_modules/.bin/n8n"
if [ ! -x "$N8N" ] || ! PATH="$NODE_BIN:/usr/bin:/bin" "$N8N" --version 2>/dev/null | grep -qx "$VERSION"; then
  [ -f "$LIB/package.json" ] || printf '{"name":"triagent-n8n","private":true}\n' > "$LIB/package.json"
  set -- "$NODE_BIN/npm" install --prefix "$LIB" --no-audit --no-fund --omit=dev --loglevel=error --cache "$CACHE" "n8n@$VERSION"
  if [ -n "$IMAGE" ]; then
    PATH="$NODE_BIN:/usr/bin:/bin" "$@"          # writes into the image only
  else
    python3 "$GUARD" check --need 3.8G || { echo "disk guard refused: n8n needs 3.8G and 13.5 GB must stay free"; exit 3; }
    PATH="$NODE_BIN:/usr/bin:/bin" python3 "$GUARD" run --need 3.8G --label n8n-install --path "$LIB" -- "$@"
    rm -rf "$CACHE"
  fi
fi
echo "n8n $(PATH="$NODE_BIN:/usr/bin:/bin" "$N8N" --version) at $N8N"

# The same environment for the service and for the import commands below.
ENVFILE="$STATE/env.sh"
cat > "$ENVFILE" <<EOF
export PATH="$NODE_BIN:/usr/bin:/bin"
export N8N_USER_FOLDER="$STATE"
export N8N_HOST=127.0.0.1 N8N_LISTEN_ADDRESS=127.0.0.1 N8N_PORT=5678 N8N_PROTOCOL=http N8N_SECURE_COOKIE=false
export WEBHOOK_URL=http://127.0.0.1:5678/ GENERIC_TIMEZONE=Europe/Lisbon TZ=Europe/Lisbon
export N8N_DIAGNOSTICS_ENABLED=false N8N_VERSION_NOTIFICATIONS_ENABLED=false N8N_TEMPLATES_ENABLED=false
export N8N_PERSONALIZATION_ENABLED=false N8N_HIRING_BANNER_ENABLED=false N8N_PUBLIC_API_DISABLED=true
export N8N_COMMUNITY_PACKAGES_ENABLED=false N8N_BLOCK_ENV_ACCESS_IN_NODE=true N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true
export NODES_EXCLUDE='["n8n-nodes-base.executeCommand","n8n-nodes-base.ssh","n8n-nodes-base.readWriteFile","n8n-nodes-base.localFileTrigger","n8n-nodes-base.git"]'
export EXECUTIONS_DATA_PRUNE=true EXECUTIONS_DATA_MAX_AGE=168 EXECUTIONS_DATA_PRUNE_MAX_COUNT=5000
export N8N_LOG_LEVEL=warn N8N_LOG_OUTPUT=console   # the log is on the internal disk: keep it small
# Measured 2026-11-07 with the code on the external disk: the JS task runner needs more than the default 30 s
# to start, and without it the Code node never runs. mcp-registry calls api.n8n.io: not needed here.
export N8N_RUNNERS_GRANT_TOKEN_TTL=600 N8N_RUNNERS_TASK_TIMEOUT=300 N8N_DISABLED_MODULES=mcp-registry
EOF
chmod 600 "$ENVFILE"

# Launcher: mounts the image when it is not, otherwise fails and launchd retries in 5 minutes.
# Measured 2026-11-08: after a lid-closed hibernate the USB disk came back later than the first attach.
RUN="$STATE/run-n8n.sh"
cat > "$RUN" <<EOF
#!/bin/sh
set -eu
if [ -n "$IMAGE" ] && [ ! -x "$N8N" ]; then
  i=0; until [ -d "$IMAGE" ] || [ \$i -ge 24 ]; do sleep 5; i=\$((i+1)); done
  i=0; until hdiutil attach -nobrowse -owners on "$IMAGE" >/dev/null || [ \$i -ge 5 ]; do sleep 10; i=\$((i+1)); done
  [ -x "$N8N" ] || { echo "n8n code not reachable: $IMAGE (external disk unplugged?)"; exit 1; }
fi
. "$ENVFILE"
exec "$N8N" start
EOF
chmod 700 "$RUN"

launchctl bootout "gui/$(id -u)/com.benjamin.triagent-n8n" 2>/dev/null || true   # the CLI import needs it stopped
TMP="$STATE/import.$$"
trap 'rm -rf "$TMP"' EXIT
"$PY" -I "$HERE/prepare_workflow.py" "$HERE/TRIAGENT_N8N_ADAPTIVE_V2.json" "$TMP" "$CONF/secrets.env"
( . "$ENVFILE"; "$N8N" import:credentials --input="$TMP/credentials.json" && "$N8N" import:workflow --input="$TMP/workflow.json" )
rm -rf "$TMP"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.benjamin.triagent-n8n</string>
  <key>ProgramArguments</key><array><string>/bin/sh</string><string>$RUN</string></array>
  <key>WorkingDirectory</key><string>$STATE</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>ThrottleInterval</key><integer>300</integer>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$STATE/logs/n8n.log</string>
  <key>StandardErrorPath</key><string>$STATE/logs/n8n.log</string>
</dict>
</plist>
EOF
plutil -lint "$PLIST" >/dev/null
[ "${1:-}" = "--no-start" ] || launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "n8n service com.benjamin.triagent-n8n on http://127.0.0.1:5678/ (workflow imported INACTIVE)"
