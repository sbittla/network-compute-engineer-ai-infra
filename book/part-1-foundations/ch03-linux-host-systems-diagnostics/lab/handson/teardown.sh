#!/usr/bin/env bash
# Chapter 3 hands-on lab: remove everything the lab created. Safe to run repeatedly.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

# Load generators are tagged "ch03-" on their command line and also run under timeout, so they end anyway.
pkill -f 'ch03-(spin|hog|bench)' 2>/dev/null || true
rm -f /var/tmp/ch03-pagecache.bin
rm -rf /tmp/ch03-nonroot.*
left="$(pgrep -fa 'ch03-(spin|hog|bench)' | grep -v pgrep || true)"
[ -z "$left" ] || { echo "teardown: processes still running:"; echo "$left"; exit 1; }
[ ! -e /var/tmp/ch03-pagecache.bin ] || die "teardown: /var/tmp/ch03-pagecache.bin still present"
echo "ch03 teardown: clean"
