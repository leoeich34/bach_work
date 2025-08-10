import numpy as np
import json

# Загрузка объекта X.npy, который мы создали ранее:
X = np.load("/Users/leo/PycharmProjects/anomaly-detector/src/features/X.npy")  # размерность (N, 70)

# Берём первый пример:
first_row = X[0].tolist()

# Формируем JSON:
payload = {"features": first_row}
print(json.dumps(payload, separators=(",", ":")))