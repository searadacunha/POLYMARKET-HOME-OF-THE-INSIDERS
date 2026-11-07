#!/bin/sh
# Install n8n for TriAgent as its own per-user launchd service, loopback only, and import the V2 workflow INACTIVE.
#   sh install_n8n.sh            install (refused by the disk guard when space is short), import, start
# Needs about 2.7 GB (2 300 npm packages, measured from the lockfile on 2026-11-07) plus the npm download cache.
# Activation is NOT done here: see README, "n8n orchestration".
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
VERSION="${N8N_VERSION:-2.46.6}"
NODE_BIN="${N8N_NODE_BIN:-/opt/homebrew/opt/node@24/bin}"   # n8n 2.x supports Node 24; Node 26 is not tested
LIB="$HOME/.local/lib/triagent-n8n"
STATE="$HOME/.local/state/triagent-n8n"
CONF="$HOME/.config/triagent"
CACHE="${N8N_NPM_CACHE:-$LIB/.npm-cache-install}"   # removed after a successful install
NEED="${N8N_DISK_NEED:-3.8G}"
PLIST="$HOME/Library/LaunchAgents/com.benjamin.triagent-n8n.plist"
GUARD="$HOME/.local/lib/disk-guard/diskguard.py"
PY=/opt/homebrew/bin/python3.12

"$NODE_BIN/node" -e 'process.exit(+process.versions.node.split(".")[0] >= 24 ? 0 : 1)' || { echo "Node 24+ needed at $NODE_BIN"; exit 1; }
mkdir -p "$LIB" "$STATE/logs"
chmod 700 "$STATE"
if [ ! -x "$LIB/node_modules/.bin/n8n" ] || ! "$LIB/node_modules/.bin/n8n" --version 2>/dev/null | grep -qx "$VERSION"; then
  python3 "$GUARD" check --need "$NEED" || { echo "disk guard refused: n8n needs $NEED and 13.5 GB must stay free"; exit 3; }
  [ -f "$LIB/package.json" ] || printf '{"name":"triagent-n8n","private":true}\n' > "$LIB/package.json"
  PATH="$NODE_BIN:/usr/bin:/bin" python3 "$GUARD" run --need "$NEED" --label n8n-install --path "$LIB" -- \
    "$NODE_BIN/npm" install --prefix "$LIB" --no-audit --no-fund --omit=dev --loglevel=error --cache "$CACHE" "n8n@$VERSION"
  rm -rf "$CACHE"
fi
N8N="$LIB/node_modules/.bin/n8n"
echo "n8n $("$N8N" --version) at $N8N"

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
export N8N_LOG_LEVEL=info N8N_LOG_OUTPUT=console
EOF
chmod 600 "$ENVFILE"

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
  <key>ProgramArguments</key><array><string>/bin/sh</string><string>-c</string><string>. "$ENVFILE" &amp;&amp; exec "$N8N" start</string></array>
  <key>WorkingDirectory</key><string>$STATE</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$STATE/logs/n8n.log</string>
  <key>StandardErrorPath</key><string>$STATE/logs/n8n.log</string>
</dict>
</plist>
EOF
plutil -lint "$PLIST" >/dev/null
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "n8n service com.benjamin.triagent-n8n started on http://127.0.0.1:5678/ (workflow imported INACTIVE)"
