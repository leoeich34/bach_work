from __future__ import annotations
import logging
from pathlib import Path


def get_logger(name: str = "anomaly_detector", level: str = "INFO") -> logging.Logger:
    """
    Программа-логгер пишет одновременно в консоль и в файл ./logs/<name>.log
    """
    logger = logging.getLogger(name)
    if logger.handlers:                         # уже сконфигурирован
        return logger

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    formatter = logging.Formatter(fmt)

    # stdout
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # file
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    fh = logging.FileHandler(log_dir / f"{name}.log", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.debug("Logger %s инициализирован на уровне %s", name, level)
    return logger