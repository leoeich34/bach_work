from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
from sklearn.base import BaseEstimator

from src.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path("src/models/saved")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def save_model(model: BaseEstimator, name: str) -> Path:
    path = MODEL_DIR / f"{name}.joblib"
    joblib.dump(model, path)
    logger.info("Модель сохранена → %s", path)
    return path


def load_model(name: str) -> BaseEstimator:
    path = MODEL_DIR / f"{name}.joblib"
    if not path.exists():
        raise FileNotFoundError(path)
    logger.info("Загрузка модели: %s", path)
    return joblib.load(path)