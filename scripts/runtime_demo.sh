#!/usr/bin/env bash
set -euo pipefail
PCAP=live.pcap
tcpdump -i any -w "$PCAP" &
PID_TCP=$!
python -m src.capture.pcap_tail_reader --pcap_live "$PCAP"
kill "$PID_TCP"