"""
StandardScaler + сохранение X/y в .npy, scaler в joblib.
Запуск:
    python src/features/feature_extraction.py \
        --input_file src/data/processed/data.parquet --output_dir src/features
"""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input_file", default="src/data/processed/data.parquet")
    p.add_argument("--output_dir", default="src/features")
    args = p.parse_args()

    df = pd.read_parquet(args.input_file)
    if "Label" not in df.columns:
        raise KeyError("Стоблец 'Label' не был найден. Проверьте написание.")

    y = (df["Label"] != 0).astype(int).values  # если 0 – benign
    X = df.drop(columns=["Label"]).values

    scaler = StandardScaler()
    X[~np.isfinite(X)] = 0  # заменяем ±inf и nan на 0
    X_scaled = scaler.fit_transform(X)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "X.npy", X_scaled)
    np.save(out_dir / "y.npy", y)
    joblib.dump(scaler, out_dir / "scaler.joblib")
    logger.info("Признаки успешно сохранены в %s", out_dir)


if __name__ == "__main__":
    main()