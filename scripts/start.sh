#!/usr/bin/env bash
set -euo pipefail

echo "=== Пайплайн обучения модели (только при первом запуске) ==="
if [ ! -f src/models/saved/random_forest.joblib ]; then
  anomaly-pipeline --mode all
else
  echo "Модель уже присутствует — пропуск обучения"
fi

echo "=== Запуск API ==="
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 2