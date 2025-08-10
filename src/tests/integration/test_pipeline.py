"""Лёгкая проверка, что CLI-пайплайн импортируется и
имеет функцию main — без скачивания гигабайтного датасета."""
from importlib import import_module


def test_pipeline_entrypoint_exists():
    module = import_module("src.cli.run_pipeline")
    assert hasattr(module, "main"), "run_pipeline.main() отсутствует"