from __future__ import annotations
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd


def load_model_and_scaler(
    model_path: Path, scaler_path: Path
) -> Tuple[object, object]:
    """
    Загружает и возвращает модель и StandardScaler из joblib-файлов.
    """
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    return model, scaler


def prepare_dataframe(
    df_raw: pd.DataFrame, columns_file: Path
) -> pd.DataFrame:
    """
    Очищает и готовит DataFrame к inference:
    - убирает пробелы в названиях
    - дропает столбец 'Label' если есть
    - оставляет только ожидаемые колонки из columns_file
    - заменяет inf и -inf на NaN, затем заполняет NaN нулями
    """
    df = df_raw.copy()
    # очистка названий колонок
    df.columns = df.columns.str.strip()
    # удаляем Label if present
    if "Label" in df.columns:
        df = df.drop(columns=["Label"])
    # читаем ожидаемые признаки
    expected = [line.strip() for line in columns_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    # проверяем отсутствие
    missing = set(expected) - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")
    # выбираем в порядке expected
    df = df[expected].copy()
    # заменяем бесконечности и заполняем
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.fillna(0)
    return df


def predict_batch(
    model: object, scaler: object, X: np.ndarray, threshold: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Делает inference:
    - X: numpy-массив размерности (N, n_features)
    - threshold: порог для метки аномалии
    Возвращает: (preds, probs)
    """
    X_scaled = scaler.transform(X)
    probs = model.predict_proba(X_scaled)[:, 1]
    preds = (probs >= threshold).astype(int)
    return preds, probs
