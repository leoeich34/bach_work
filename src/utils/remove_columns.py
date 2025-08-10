#!/usr/bin/env python3
"""
Скрипт для удаления (отсечения) указанных столбцов из CSV или Parquet.

Пример использования:
    python src/utils/remove_columns.py \
        --input_file src/data/processed/data.parquet \
        --output_file src/data/processed/data_trimmed.parquet \
        --columns " Bwd Avg Bytes/Bulk" " Bwd Avg Packets/Bulk" "Bwd Avg Bulk Rate" "Label"

Если ваш вход — CSV:
    python src/utils/remove_columns.py \
        --input_file src/data/raw/flows.csv \
        --output_file src/data/raw/flows_trimmed.csv \
        --columns "col_to_remove1" "col_to_remove2"

После запуска:
 • Из `input_file` будут удалены все колонки, перечисленные через --columns.
 • Результат сохранится в `output_file` (формат совпадает с входным: .csv → .csv, .parquet → .parquet).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Удаляет указанные столбцы из CSV/Parquet и сохраняет результат."
    )
    parser.add_argument(
        "--input_file",
        "-i",
        required=True,
        help="Путь к входному файлу (CSV или Parquet).",
    )
    parser.add_argument(
        "--output_file",
        "-o",
        required=True,
        help=(
            "Путь для сохранения обрезанного файла. "
            "Расширение должен совпадать с входным ('.csv' или '.parquet')."
        ),
    )
    parser.add_argument(
        "--columns",
        "-c",
        nargs="+",
        required=True,
        help=(
            "Список имён колонок, которые нужно удалить (в кавычках, разделяются пробелом). "
            "Имена должны точно совпадать с тем, как они записаны в файле, включая пробелы."
        ),
    )
    return parser.parse_args()


def load_dataframe(path: Path) -> pd.DataFrame:
    """
    Загружает DataFrame из файла .csv или .parquet.
    """
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path, low_memory=False)
    elif suffix in {".parquet", ".parq", ".pq"}:
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Неподдерживаемое расширение файла: {suffix}. Используйте .csv или .parquet.")
    return df


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    """
    Сохраняет DataFrame в файл .csv или .parquet, в зависимости от расширения path.
    """
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix in {".parquet", ".parq", ".pq"}:
        df.to_parquet(path, index=False)
    else:
        raise ValueError(f"Неподдерживаемое расширение сохранения: {suffix}. Используйте .csv или .parquet.")


def main() -> None:
    args = parse_args()
    in_path = Path(args.input_file)
    out_path = Path(args.output_file)
    cols_to_remove = args.columns

    # Проверяем, что входной файл существует
    if not in_path.exists() or not in_path.is_file():
        print(f"[ERROR] Входного файла не существует: {in_path}", file=sys.stderr)
        sys.exit(1)

    # Проверяем, что output_folder существует или может быть создан
    if not out_path.parent.exists():
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Не удалось создать директорию для output_file: {e}", file=sys.stderr)
            sys.exit(1)

    # Загружаем DataFrame
    try:
        print(f"[INFO] Читаем входной файл: {in_path}")
        df = load_dataframe(in_path)
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить DataFrame: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Исходный DataFrame: {df.shape[0]} строк, {df.shape[1]} столбцов")

    # Удаляем указанные колонки
    actually_removed = []
    not_found = []
    for col in cols_to_remove:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)
            actually_removed.append(col)
        else:
            not_found.append(col)

    # Инфо по удалению
    if actually_removed:
        print(f"[INFO] Удалены колонки ({len(actually_removed)}): {actually_removed}")
    if not_found:
        print(f"[WARNING] Не найдены (т. е. не удалены) колонки ({len(not_found)}): {not_found}")

    print(f"[INFO] Результирующий DataFrame: {df.shape[0]} строк, {df.shape[1]} столбцов")

    # Сохраняем результат
    try:
        save_dataframe(df, out_path)
        print(f"[INFO] Обрезанный DataFrame сохранён в: {out_path}")
    except Exception as e:
        print(f"[ERROR] Не удалось сохранить DataFrame: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()