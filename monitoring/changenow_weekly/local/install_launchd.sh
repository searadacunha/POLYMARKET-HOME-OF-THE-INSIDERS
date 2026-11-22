#!/bin/sh
# Installs a macOS LaunchAgent that runs update.sh every six hours. Run it yourself: it registers a background service.
#   sh install_launchd.sh [path of an env file holding ETHERSCAN_API_KEY=...]
# Remove with: launchctl bootout gui/$(id -u)/org.polymarket-insiders.changenow-weekly
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
LABEL=org.polymarket-insiders.changenow-weekly
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
STATE="$HOME/.local/state/changenow-weekly"
mkdir -p "$STATE" "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>/bin/sh</string><string>$HERE/update.sh</string></array>
  <key>EnvironmentVariables</key><dict>
    <key>CHANGENOW_RAW</key><string>$STATE/raw</string>
    <key>CHANGENOW_ENV_FILE</key><string>${1:-}</string>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>StartInterval</key><integer>21600</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$STATE/update.log</string>
  <key>StandardErrorPath</key><string>$STATE/update.log</string>
</dict></plist>
PLIST
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "installed: $PLIST, log: $STATE/update.log"
