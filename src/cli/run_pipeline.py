"""
Управление конвейером: download → preprocess → features → train (или любой отдельный этап).
Запуск:
    python src/cli/run_pipeline.py --mode all
"""
from __future__ import annotations

import argparse
import subprocess
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.utils.logger import get_logger

logger = get_logger("pipeline")

BASE = Path(__file__).resolve().parent.parent



def call(script: Path, *args: str) -> None:
    # Получить относительный путь от BASE к скрипту, заменить / на . и убрать .py
    rel = script.relative_to(BASE)
    module_name = ".".join(rel.with_suffix("").parts)  # например, src.data.download_data
    cmd = ["python", "-m", module_name, *args]
    logger.info("Запущен процесс: %s", " ".join(cmd))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE)
    subprocess.check_call(cmd, env=env)

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--mode",
        choices=["download", "preprocess", "features", "train", "all"],
        required=True,
    )
    args = p.parse_args()

    if args.mode in {"download", "all"}:
        call(BASE / "data" / "download_data.py",
             "--url", "https://archive.ics.uci.edu/static/public/1231/cicids2017.zip")
    if args.mode in {"preprocess", "all"}:
        call(BASE / "data" / "preprocess.py")
    if args.mode in {"features", "all"}:
        call(BASE / "features" / "feature_extraction.py")
    if args.mode in {"train", "all"}:
        call(BASE / "models" / "train.py")


if __name__ == "__main__":
    main()