#!/usr/bin/env bash
set -euo pipefail
TARGET=${1:-127.0.0.1}
nmap -sS -p1-1000 "$TARGET"
hping3 -S -c 1000 -i u1000 -p 80 "$TARGET"