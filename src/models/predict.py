"""
Инференс готовой модели по матрице X.npy.
Запуск:
    python src/models/predict.py --model random_forest --input_file src/features/X.npy
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from src.models.model_utils import load_model
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="random_forest")
    p.add_argument("--input_file", required=True, help="npy с признаками (X)")
    p.add_argument(
        "--threshold", default=0.8, type=float, help="Soft-anomaly порог [0..1]"
    )
    args = p.parse_args()

    model = load_model(args.model)
    X = np.load(Path(args.input_file))

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[:, 1]
        preds = (probs >= args.threshold).astype(int)
    else:
        preds = model.predict(X)
        probs = np.full_like(preds, np.nan, dtype=float)

    for i, (p_label, p_prob) in enumerate(zip(preds, probs)):
        tag = "ANOMALY" if p_label else "BENIGN "
        logger.info("Образец %04d → %s | оценка=%.4f", i, tag, p_prob)


if __name__ == "__main__":
    main()