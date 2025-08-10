#!/usr/bin/env bash
set -euo pipefail

# ждём, пока обучится модель (если контейнер стартует с нуля)
if [ ! -f src/models/saved/random_forest.joblib ]; then
  echo "Модель не найдена – сначала запускаем обучение pipeline…"
  anomaly-pipeline --mode all
fi

echo "=== Запуск Streamlit UI ==="
exec streamlit run src/ui/main.py --server.port 8501 --server.headless true