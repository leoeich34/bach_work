import numpy as np
from src.utils.metrics import classification_metrics


def test_classification_metrics_basic() -> None:
    y_true = np.array([0, 1, 0, 1])
    y_pred = np.array([0, 1, 0, 0])
    m = classification_metrics(y_true, y_pred)
    assert m["accuracy"] == 0.75
    assert m["tp"] == 1 and m["fp"] == 0 and m["fn"] == 1 and m["tn"] == 2