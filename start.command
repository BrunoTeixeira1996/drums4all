#!/bin/sh
# drums4all for macOS: double-click this file. The first time macOS may ask for permission:
# right-click it, choose "Open", then "Open" again.
cd "$(dirname "$0")" || exit 1
exec sh ./start.sh "$@"
