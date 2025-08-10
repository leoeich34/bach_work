from __future__ import annotations

from pathlib import Path
from typing import Callable

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from starlette.middleware import Middleware

from src.api.middleware import TimingMiddleware
from src.api.schemas import Prediction, TrafficSample
from src.utils.logger import get_logger

logger = get_logger(__name__)

middleware = [Middleware(TimingMiddleware)]
app = FastAPI(title="Anomaly-Detector API",
              version="0.1.0",
              middleware=middleware)

# -------------------------- конфигурация --------------------------------
MODEL_NAME = "random_forest"
MODEL_PATH = Path("src/models/saved") / f"{MODEL_NAME}.joblib"
SCALER_PATH = Path("src/features") / "scaler.joblib"
THRESHOLD = 0.80
# ------------------------------------------------------------------------


def lazy_load(path: Path, loader: Callable):
    _cache: dict[Path, object] = {}

    def _inner():
        if path not in _cache:
            _cache[path] = loader(path)
            logger.info("Loaded %s", path)
        return _cache[path]

    return _inner


load_model = lazy_load(MODEL_PATH, joblib.load)
load_scaler = lazy_load(SCALER_PATH, joblib.load)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=Prediction)
def predict(sample: TrafficSample):
    model = load_model()
    scaler = load_scaler()

    X = np.asarray(sample.features, dtype=float).reshape(1, -1)
    X_scaled = scaler.transform(X)

    if not hasattr(model, "predict_proba"):
        raise HTTPException(500, "Модель недостает predict_proba")

    prob = float(model.predict_proba(X_scaled)[0, 1])
    label = "anomaly" if prob >= THRESHOLD else "benign"
    return {"label": label, "score": prob}