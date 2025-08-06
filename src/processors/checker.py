"""Алгоритм проверки выходного XML-файла."""

from pathlib import Path

import src.parsers.schedule as schedule


class Checker:
    """Алгоритм проверки."""

    @staticmethod
    def process(src_path: Path):
        """Точка входа в алгоритм проверки.

        :arg src_path: Путь к проверяемому файлу
        """
        # Читаем XML с расписанием
        with Path.open(src_path, 'r', encoding='utf-8') as file:
            src_xml = file.read()
        # Парсим через pydantic_xml

        src_data = schedule.parse_schedule(src_xml)
        if not src_data:
            # !!! TODO - записать в log
            return

        # !!! Пока скопируем исходник - потом напишем алгоритм
