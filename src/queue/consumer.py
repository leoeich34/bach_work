#!/usr/bin/env python3
"""
Подписывается на Kafka topic=flows, получает батчи фичей (list[list[float]]),
делает predict_proba, пишет алерт в syslog и вызывает firewall.block_ip()
если score ≥ HARD_THRESHOLD.
"""
from __future__ import annotations

import json
import logging
import sys
from ipaddress import ip_address
from pathlib import Path
from typing import List

import joblib
import numpy as np
from kafka import KafkaConsumer
from tabulate import tabulate

from src.actions.firewall import block_ip

# ---- config ---------------------------------------------------------------
MODEL_PATH = Path("src/models/saved/random_forest.joblib")
SCALER_PATH = Path("src/features/scaler.joblib")
THRESHOLD = 0.95
KAFKA_BROKER = "localhost:29092"
TOPIC = "flows"
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("consumer")


def load_assets():
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler


def handle_batch(batch: List[List[float]], model, scaler):
    X_scaled = scaler.transform(batch)
    scores = model.predict_proba(X_scaled)[:, 1]
    suspects = np.where(scores >= THRESHOLD)[0]
    if len(suspects) == 0:
        return
    log.warning("⚠  Found %s suspicious flows", len(suspects))
    table = [
        [idx, f"{score:.3f}"] for idx, score in zip(suspects, scores[suspects])
    ]
    print(tabulate(table, headers=["idx", "score"], tablefmt="pretty"))

    # пример блокировки: здесь нет IP, потому что в batch нет колонок SrcIP/DstIP.
    # Ниже иллюстрация, как вызвать:
    # for row in suspects:
    #     ip = batch[row][SRC_IP_IDX]          # если колонка есть
    #     block_ip(ip)
    # log.info("Blocked %d IP via firewall", len(suspects))


def main() -> None:
    model, scaler = load_assets()
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda b: json.loads(b.decode()),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    log.info("Consumer started, waiting for messages…")
    try:
        for msg in consumer:
            batch = msg.value  # list[list[float]]
            if not batch:
                continue
            handle_batch(batch, model, scaler)
    except KeyboardInterrupt:
        log.info("Stopped by Ctrl-C")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()