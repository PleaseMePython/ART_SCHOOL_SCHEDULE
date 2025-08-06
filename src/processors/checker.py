"""Алгоритм проверки выходного XML-файла."""

import json
from calendar import Day, day_name
from dataclasses import dataclass
from pathlib import Path
from typing import Set

import src.parsers.schedule as schedule


@dataclass(frozen=True)
class LessonTime:
    """Занятое время урока."""

    day_of_week: Day
    group: str
    npp: int


class Checker:
    """Алгоритм проверки."""

    def __init__(self):
        """Инициализация."""
        self.src_data = schedule.Schedule(teachers=[])
        self.errors = []

    def process(self, src_path: Path) -> str:
        """Точка входа в алгоритм проверки.

        :arg src_path: Путь к проверяемому файлу
        """
        # Читаем XML с расписанием
        with Path.open(src_path, 'r', encoding='utf-8') as file:
            src_xml = file.read()
        # Парсим через pydantic_xml

        self.src_data = schedule.parse_schedule(src_xml)
        if not self.src_data:
            Exception('Исходный файл имеет неверный формат')

        self.check_schedule()

        if self.errors:
            return json.dumps({'Ошибки': self.errors})
        else:
            return json.dumps({'Статус': 'ОК'})

    def check_schedule(self):
        """Проверка расписания на пересечения."""
        morning: Set[LessonTime] = set()
        afternoon: Set[LessonTime] = set()
        for teacher in self.src_data.teachers:
            for day_code in Day:
                attr_name = day_code.name.lower()
                if not hasattr(teacher, attr_name):
                    continue
                day_data = getattr(teacher, attr_name)

                if hasattr(day_data, 'morning') and day_data.morning:
                    for lesson in day_data.morning.lessons:
                        if (
                            LessonTime(
                                day_of_week=day_code, group=lesson.group, npp=lesson.npp
                            )
                            in morning
                        ):
                            self.errors.append(
                                f'Пересечение: группа {lesson.group},'
                                f'{day_name[day_code]}, утро, урок {lesson.npp}'
                            )
                if hasattr(day_data, 'afternoon') and day_data.afternoon:
                    for lesson in day_data.afternoon.lessons:
                        if (
                            LessonTime(
                                day_of_week=day_code, group=lesson.group, npp=lesson.npp
                            )
                            in afternoon
                        ):
                            self.errors.append(
                                f'Пересечение: группа {lesson.group},'
                                f'{day_name[day_code]}, вечер, '
                                f'урок {lesson.npp}'
                            )
