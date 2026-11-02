#!/bin/bash
# Rebuild the research on any Mac, from the external disk or from GitHub.
#   restore_all.sh --dest DIR [--source disk|github] [--identity FILE] [--root NAME]
# From the disk, clear packs need no key. Secrets and the GitHub copy need the age identity file.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SOURCE=disk; DEST=""; IDENTITY=""; ROOT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dest) DEST="$2"; shift 2;;
    --source) SOURCE="$2"; shift 2;;
    --identity) IDENTITY="$2"; shift 2;;
    --root) ROOT="$2"; shift 2;;
    *) echo "unknown option $1"; exit 2;;
  esac
done
[ -n "$DEST" ] || { echo "usage: restore_all.sh --dest DIR [--source disk|github] [--identity FILE] [--root NAME]"; exit 2; }
[ ! -e "$DEST" ] || [ -z "$(ls -A "$DEST")" ] || { echo "refusing: $DEST is not empty"; exit 2; }
mkdir -p "$DEST"
AGE="$(command -v age || echo "$HERE/age-darwin-arm64")"
[ -x "$AGE" ] || chmod +x "$AGE" 2>/dev/null || true
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
REPO="$(python3 -c "import json;print(json.load(open('$HERE/public-config.json'))['repo'])")"
printf '{"repo": "%s", "gh_bin": "%s", "age_bin": "%s", "identity": "%s"}\n' "$REPO" "$(command -v gh || echo gh)" "$AGE" "$IDENTITY" > "$WORK/config.json"
export PHI_CONFIG="$WORK/config.json" PHI_STATE="$WORK/state"
ARGS=(--source "$SOURCE" --dest "$DEST")
[ -z "$IDENTITY" ] || ARGS+=(--identity "$IDENTITY")
[ -z "$ROOT" ] || ARGS+=(--root "$ROOT")
if [ "$SOURCE" = disk ]; then
  DISK="$(dirname "$HERE")"
  python3 "$HERE/phi_backup.py" restore "${ARGS[@]}" --disk "$DISK" --manifests "$DISK/manifests"
else
  [ -n "$IDENTITY" ] || { echo "GitHub archives are encrypted: --identity is required"; exit 2; }
  command -v gh >/dev/null || { echo "gh is required, and gh auth login"; exit 2; }
  TAG_ASSET="$(gh api --paginate "repos/$REPO/releases" --jq '.[] | .tag_name as $t | .assets[] | select(.name|startswith("index-")) | "\(.name) \($t)"' | sort | tail -1)"
  gh release download "${TAG_ASSET#* }" --repo "$REPO" --pattern "${TAG_ASSET% *}" --dir "$WORK"
  mkdir -p "$WORK/manifests"
  "$AGE" -d -i "$IDENTITY" "$WORK/${TAG_ASSET% *}" | tar -x -C "$WORK/manifests"
  python3 "$HERE/phi_backup.py" restore "${ARGS[@]}" --manifests "$WORK/manifests"
fi
