#!/usr/bin/env python3
"""
Tail-читатель: раз в interval секунд берёт всё, что появилось
в файле <pcap_live>, прогоняет через pcap_to_features.parse_pcap,
кладёт в Kafka topic=flows.
"""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from shutil import copyfileobj
from tempfile import NamedTemporaryFile

from src.capture.pcap_to_features import parse_pcap, send_to_kafka

OFFSET_FILE = ".pcap_offset"  # хранит смещение в байтах


def read_new_packets(src: Path, offset_path: Path) -> Path | None:
    """Читает всё, что было добавлено с последнего offset, сохраняет во временный pcap"""
    last = 0
    if offset_path.exists():
        last = int(offset_path.read_text())
    size = src.stat().st_size
    if size <= last:
        return None  # нет новых данных
    with src.open("rb") as f, NamedTemporaryFile("wb", delete=False, suffix=".pcap") as tmp:
        f.seek(last)
        copyfileobj(f, tmp)
        offset_path.write_text(str(size))
        return Path(tmp.name)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pcap_live", required=True, help="Файл, который пишет tcpdump -w")
    p.add_argument("--interval", type=int, default=5, help="секунд между проверками")
    args = p.parse_args()

    pcap_path = Path(args.pcap_live)
    offset_path = pcap_path.parent / OFFSET_FILE
    while True:
        tmp_pcap = read_new_packets(pcap_path, offset_path)
        if tmp_pcap:
            df = parse_pcap(tmp_pcap)
            if not df.empty:
                send_to_kafka(df)
                print(f"[{time.strftime('%X')}] Sent {len(df):,} new flows")
            os.unlink(tmp_pcap)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()