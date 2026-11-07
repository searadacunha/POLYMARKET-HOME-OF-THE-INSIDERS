#!/bin/sh
# Install TriAgent as a per-user launchd service. Idempotent; never overwrites config or secrets.
#   sh install.sh            install or update code, config templates, research checkout, launchd agent
#   sh install.sh --start    same, then load and start the agent
set -eu
SRC="$(cd "$(dirname "$0")" && pwd)"
REPO_SRC="$(git -C "$SRC" rev-parse --show-toplevel)"
PY="${TRIAGENT_PYTHON:-/opt/homebrew/bin/python3.12}"
LIB="$HOME/.local/lib/triagent"
STATE="$HOME/.local/state/triagent"
CONF="$HOME/.config/triagent"
PLIST="$HOME/Library/LaunchAgents/com.benjamin.triagent.plist"

"$PY" -c 'import sys; assert sys.version_info >= (3, 11), sys.version' || { echo "Python 3.11+ required at $PY"; exit 1; }
mkdir -p "$LIB" "$STATE/logs" "$CONF"
chmod 700 "$STATE" "$CONF"

# Code: a copy, so the service keeps running when the source worktree changes branch or is removed.
rsync -a --delete --exclude '__pycache__' --exclude '*.pyc' "$SRC/" "$LIB/"
for f in "$LIB/bin/triagent" "$LIB/bin/tg-fetch"; do
  sed -i '' "s|/opt/homebrew/bin/python3.12|$PY|" "$f"
done

[ -f "$CONF/config.env" ] || cp "$SRC/config.example.env" "$CONF/config.env"
if [ ! -f "$CONF/secrets.env" ]; then
  cp "$SRC/secrets.example.env" "$CONF/secrets.env"
fi
chmod 600 "$CONF/secrets.env" "$CONF/config.env"
# Local header tokens for the n8n broker (127.0.0.1:8791) and the n8n wake webhook: generated once, never printed.
for k in BROKER_TOKEN N8N_WAKE_TOKEN; do
  grep -q "^$k=..*" "$CONF/secrets.env" || printf '%s=%s\n' "$k" "$("$PY" -c 'import secrets; print(secrets.token_urlsafe(32))')" >> "$CONF/secrets.env"
done

# Research context: detached checkout of origin/main, read-only for missions.
# Sparse: reports, code and manifests (about 15 MB) instead of the 0.5 GB of raw investigation data.
if [ ! -e "$STATE/research-repo/.git" ]; then
  git -C "$REPO_SRC" fetch -q origin main
  git -C "$REPO_SRC" worktree add --no-checkout --detach "$STATE/research-repo" origin/main
  git -C "$STATE/research-repo" sparse-checkout set --no-cone '/*' '!/investigations/**' \
    '/investigations/**/*.md' '/investigations/**/*.py' '/investigations/**/data_manifest.json'
  git -C "$STATE/research-repo" checkout -q --detach origin/main
fi

mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/triagent" <<EOF
#!/bin/sh
exec "$LIB/bin/triagent" "\$@"
EOF
chmod 755 "$HOME/.local/bin/triagent"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.benjamin.triagent</string>
  <key>ProgramArguments</key><array><string>$LIB/bin/triagent</string><string>run</string></array>
  <key>EnvironmentVariables</key><dict>
    <key>TRIAGENT_PYTHON</key><string>$PY</string>
    <key>PATH</key><string>/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string>
    <key>PYTHONDONTWRITEBYTECODE</key><string>1</string>
  </dict>
  <key>WorkingDirectory</key><string>$STATE</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>ProcessType</key><string>Background</string>
  <key>LowPriorityIO</key><true/>
  <key>Nice</key><integer>5</integer>
  <key>StandardOutPath</key><string>$STATE/logs/service.log</string>
  <key>StandardErrorPath</key><string>$STATE/logs/service.log</string>
</dict>
</plist>
EOF
plutil -lint "$PLIST" >/dev/null

echo "installed: code $LIB, state $STATE, config $CONF, agent $PLIST"
echo "secrets: edit $CONF/secrets.env (chmod 600). Mode: RUN_MODE in $CONF/config.env"
if [ "${1:-}" = "--start" ]; then
  "$HOME/.local/bin/triagent" start
fi
