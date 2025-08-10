"""
Тренировка RandomForest по готовым признакам.
Запуск:
    python src/models/train.py --features_dir src/features --model random_forest
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from src.models.model_utils import save_model
from src.utils.logger import get_logger
from src.utils.metrics import classification_metrics

logger = get_logger(__name__)


def train_rf(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestClassifier:
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=20, n_jobs=-1, random_state=42
    )
    rf.fit(X_train, y_train)
    return rf


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--features_dir", default="src/features")
    p.add_argument("--model", default="random_forest")
    args = p.parse_args()

    fd = Path(args.features_dir)
    X = np.load(fd / "X.npy")
    y = np.load(fd / "y.npy")

    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info("Размер таблицы: train %s | val %s", X_tr.shape, X_val.shape)

    if args.model != "random_forest":
        raise ValueError("В готовой оффлайн-MVP реализован только Random_forest.")

    model = train_rf(X_tr, y_tr)

    # Валидация
    y_pred = model.predict(X_val)
    y_prob = model.predict_proba(X_val)[:, 1]
    metrics = classification_metrics(y_val, y_pred, y_prob)
    logger.info("Validation metrics: %s", metrics)
    print(classification_report(y_val, y_pred, digits=4))

    save_model(model, args.model)


if __name__ == "__main__":
    main()