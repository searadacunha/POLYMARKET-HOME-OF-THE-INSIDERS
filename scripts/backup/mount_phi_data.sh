#!/bin/bash
# Keep the research image attached: live data sits on it, and FAT32 cannot hold it directly (4 GiB per file, no links).
# Without it the link to the data dangles and the collector stops on an error, so it can never start an empty database elsewhere.
IMAGE="/Volumes/VERBATIM HD/PHI-Data.sparsebundle"
/sbin/mount | /usr/bin/grep -q ' on /Volumes/PHI-Data ' && exit 0
[ -d "$IMAGE" ] || exit 0
exec /usr/bin/hdiutil attach -nobrowse -owners on "$IMAGE"
