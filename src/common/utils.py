"""Утилиты."""

from pathlib import Path


def check_file(filename: str) -> bool:
    """Проверка наличия файла."""
    if filename is None:
        return False
    # Проверяем наличие файла с настройками
    if not Path(filename).exists():
        return False
    # Проверяем, что передан путь к файлу
    return Path(filename).is_file()
