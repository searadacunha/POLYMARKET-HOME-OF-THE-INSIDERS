#!/bin/bash
# Install or refresh the backup service: code in ~/.local/lib, three LaunchAgents, no network service.
# launchd never reads under Documents, Desktop or Downloads for its own code. Config: ~/.config/phi-backup/config.json
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
LIB="$HOME/.local/lib/phi-backup"; STATE="$HOME/.local/state/phi-backup"
PY=/opt/homebrew/bin/python3.12
mkdir -p "$LIB" "$STATE" "$HOME/Library/LaunchAgents"
cp "$HERE/phi_backup.py" "$HERE/phi_repo.py" "$HERE/phi_audit.py" "$HERE/restore_all.sh" "$HERE/RECOVERY.md" "$HERE/../phi_lib.py" "$LIB/"
for spec in backup:60 upload:120 repo:300; do
  which="${spec%:*}"; every="${spec#*:}"; label="com.benjamin.phi-$which"; plist="$HOME/Library/LaunchAgents/$label.plist"
  cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>$label</string>
<key>ProgramArguments</key><array><string>$PY</string><string>$LIB/phi_backup.py</string><string>run</string><string>$which</string></array>
<key>StartInterval</key><integer>$every</integer>
<key>RunAtLoad</key><true/>
<key>ProcessType</key><string>Background</string>
<key>LowPriorityIO</key><true/>
<key>Nice</key><integer>15</integer>
<key>EnvironmentVariables</key><dict>
  <key>PATH</key><string>/opt/homebrew/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin</string>
  <key>PHI_KNOWN_DIGESTS</key><string>$HOME/.config/phi-backup/known_digests.json</string>
</dict>
<key>StandardOutPath</key><string>$STATE/launchd-$which.out</string>
<key>StandardErrorPath</key><string>$STATE/launchd-$which.err</string>
</dict></plist>
PLIST
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$plist"
done
launchctl list | grep com.benjamin.phi- || true
