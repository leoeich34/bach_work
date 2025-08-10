from __future__ import annotations
import argparse
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from shutil import copyfileobj
from src.capture.pcap_to_features import parse_pcap, send_to_kafka

OFFSET_FILE = ".pcap_offset"

def read_new(src: Path) -> Path|None:
    last = int(src.parent.joinpath(OFFSET_FILE).read_text()) if src.parent.joinpath(OFFSET_FILE).exists() else 0
    size = src.stat().st_size
    if size <= last:
        return None
    with src.open("rb") as f, NamedTemporaryFile("wb", delete=False, suffix=".pcap") as tmp:
        f.seek(last)
        copyfileobj(f, tmp)
        src.parent.joinpath(OFFSET_FILE).write_text(str(size))
        return Path(tmp.name)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pcap_live", required=True)
    p.add_argument("--interval", type=int, default=5)
    args = p.parse_args()
    pcap = Path(args.pcap_live)
    while True:
        tmp = read_new(pcap)
        if tmp:
            df = parse_pcap(tmp)
            send_to_kafka(df)
            tmp.unlink()
        time.sleep(args.interval)

if __name__ == "__main__":
    main()