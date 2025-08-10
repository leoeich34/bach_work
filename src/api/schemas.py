from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class TrafficSample(BaseModel):
    """Принимаем уже собранный числовой вектор признаков
    (порядок обязан совпадать с обучающим)."""

    features: List[float] = Field(..., min_items=1,description="Массив float признаков")


class Prediction(BaseModel):
    label: str = Field("benign", description="'anomaly' или 'benign'")
    score: float = Field(..., ge=0, le=1, description="Вероятность аномалии")