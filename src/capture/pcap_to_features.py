#!/usr/bin/env python3
"""
Читает .pcap, агрегирует flow-статистики, формирует DataFrame
с ровно теми 70 признаками, что ожидала модель (список в columns.txt),
а недостающие колонки заполняет нулями. После формирования —
или записывает Parquet, или пробрасывает батч в Kafka-producer.

Использование офлайн:
  python -m src.capture.pcap_to_features \
      --pcap dump.pcap \
      --output parquet

Использование он-лайн (как prod-процессор):
  python -m src.capture.pcap_to_features \
      --pcap live.pcap \
      --kafka
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from scapy.utils import PcapReader
from scapy.layers.inet import IP, TCP, UDP
from kafka import KafkaProducer

# ---- настроечные константы -------------------------------------------------
COLUMNS_FILE = Path("src/features/columns.txt")     # 70 признаков
KAFKA_BROKER = "localhost:29092"
TOPIC = "flows"
BATCH_SIZE = 5_000                                 # строк в одном сообщении
# ----------------------------------------------------------------------------


def load_expected_columns() -> List[str]:
    with open(COLUMNS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def parse_pcap(pcap_path: Path) -> pd.DataFrame:
    """
    Very-light flow агрегатор: ключ = (proto, srcIP, sport, dstIP, dport)
    собираем duration, packets, bytes (fwd/bwd). Под 70 признаков не
    претендуем — недостающие заполним нулями.
    """
    flows: Dict[Tuple, Dict[str, float]] = defaultdict(
        lambda: {
            "flow_start": np.inf,
            "flow_end": -np.inf,
            "fwd_pkts": 0,
            "bwd_pkts": 0,
            "fwd_bytes": 0,
            "bwd_bytes": 0,
        }
    )

    with PcapReader(str(pcap_path)) as pcap:
        for pkt in pcap:
            if not pkt.haslayer(IP):
                continue
            ip = pkt[IP]
            proto = ip.proto
            ts = pkt.time
            size = len(pkt)
            if proto == 6 and pkt.haslayer(TCP):
                sport = pkt[TCP].sport
                dport = pkt[TCP].dport
            elif proto == 17 and pkt.haslayer(UDP):
                sport = pkt[UDP].sport
                dport = pkt[UDP].dport
            else:
                sport = dport = 0

            key_fwd = (proto, ip.src, sport, ip.dst, dport)
            key_bwd = (proto, ip.dst, dport, ip.src, sport)

            if key_fwd in flows:
                flow = flows[key_fwd]
                flow["fwd_pkts"] += 1
                flow["fwd_bytes"] += size
            elif key_bwd in flows:
                flow = flows[key_bwd]
                flow["bwd_pkts"] += 1
                flow["bwd_bytes"] += size
            else:
                flow = flows[key_fwd]  # создаём
                flow["fwd_pkts"] = 1
                flow["fwd_bytes"] = size
                flow["bwd_pkts"] = flow["bwd_bytes"] = 0

            flow["flow_start"] = min(flow["flow_start"], ts)
            flow["flow_end"] = max(flow["flow_end"], ts)

    rows = []
    for (_proto, _sip, _sport, _dip, _dport), data in flows.items():
        duration = max(data["flow_end"] - data["flow_start"], 1e-6)
        rows.append(
            {
                # минимальный набор «осмысленных» фич
                "Flow Duration": duration,
                "Total Fwd Packets": data["fwd_pkts"],
                "Total Length of Fwd Packets": data["fwd_bytes"],
                "Total Bwd Packets": data["bwd_pkts"],
                "Total Length of Bwd Packets": data["bwd_bytes"],
                # заполняем остальные на нули (добавим позже)
            }
        )

    df = pd.DataFrame(rows)
    # --- доводим до 70 признаков ---
    expected = load_expected_columns()
    for col in expected:
        if col not in df.columns:
            df[col] = 0.0
    df = df[expected]  # сортировка и «лишние» выбросить
    return df


def send_to_kafka(df: pd.DataFrame) -> None:
    prod = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda x: json.dumps(x).encode(),
    )
    for i in range(0, len(df), BATCH_SIZE):
        chunk = df.iloc[i : i + BATCH_SIZE].values.tolist()
        prod.send(TOPIC, chunk)
    prod.flush()
    prod.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pcap", required=True, help="Файл .pcap либо fifo-труба")
    p.add_argument("--output", choices=["parquet"], default=None)
    p.add_argument("--kafka", action="store_true", help="Отправлять в Kafka")
    args = p.parse_args()

    df = parse_pcap(Path(args.pcap))
    if args.output == "parquet":
        out_path = Path(args.pcap).with_suffix(".parquet")
        df.to_parquet(out_path, index=False)
        print(f"[+] Saved {len(df):,} flows → {out_path}")

    if args.kafka:
        send_to_kafka(df)
        print(f"[+] Pushed {len(df):,} flows → Kafka topic={TOPIC}")


if __name__ == "__main__":
    main()