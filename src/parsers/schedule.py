"""Структура выходного xml-файла."""

from typing import List, Optional

from pydantic_xml import BaseXmlModel, attr, element


class ScheduleBaseModel(BaseXmlModel):
    """Просто обертка над BaseXMLModel, чтобы изолировать технологию."""

    pass


class Lesson(ScheduleBaseModel, tag='Урок'):
    """Урок."""

    npp: int = attr('Номер')
    subject: str = attr('Предмет')
    group: str = attr('Группа')


class PartOfDay(ScheduleBaseModel):
    """Уроки в одной смене."""

    lessons: List[Lesson] = element(tag='Урок')


class DayOfWeek(ScheduleBaseModel):
    """День с двумя сменами."""

    morning: Optional[PartOfDay] = element(tag='Утро', default=None)
    afternoon: Optional[PartOfDay] = element(tag='Вечер', default=None)


class Teacher(ScheduleBaseModel, tag='Преподаватель'):
    """Расписание учителя."""

    name: str = attr('ФИО')
    monday: DayOfWeek = element(tag='Понедельник', default=None)
    tuesday: DayOfWeek = element(tag='Вторник', default=None)
    wednesday: DayOfWeek = element(tag='Среда', default=None)
    thursday: DayOfWeek = element(tag='Четверг', default=None)
    friday: DayOfWeek = element(tag='Пятница', default=None)
    saturday: DayOfWeek = element(tag='Суббота', default=None)
    sunday: DayOfWeek = element(tag='Воскресенье', default=None)


class Schedule(ScheduleBaseModel, tag='Расписание', skip_empty=True):
    """Расписание учителей."""

    teachers: List[Teacher] = element(tag='Преподаватель')


def parse_schedule(xml: str) -> Schedule:
    """Разбор XML-файла."""
    return Schedule.from_xml(xml)
