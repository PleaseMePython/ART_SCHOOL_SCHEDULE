"""Структура входного XML-файла."""

from typing import List, Literal, Optional

from pydantic_core import ValidationError
from pydantic_xml import BaseXmlModel, attr, element, wrapped

# Да/Нет
type YesNo = Literal['Да', 'Нет']


def yesno_to_bool(yesno: (YesNo | None)) -> bool:
    """Преобразование в логический тип.

    :arg yesno: Значение Да/Нет
    :return bool: True/False
    """
    return yesno == 'Да'


def bool_to_yesno(logical_value: bool) -> YesNo:
    """Преобразование в Да/Нет.

    :arg logical_value: True/False
    :return YesNo: Значение Да/Нет
    """
    return 'Да' if logical_value else 'Нет'


class Subject(BaseXmlModel, tag='Предмет'):
    """Предметы."""

    name: str = attr('Название')
    no_split: YesNo = attr('НеРазделятьПоДням')
    one_group: YesNo = attr('ОднаГруппаЗаСмену')


class Curriculum(BaseXmlModel, tag='Предмет'):
    """Учебный план."""

    name: str = attr('Название')
    hours: int = attr('ЧасовВНеделю')
    days_of_week: str = attr('ДниНедели')


class Combination(BaseXmlModel, tag='Расстановка'):
    """Расстановка уроков в смене."""

    day_plan: str


class Grade(BaseXmlModel, tag='Класс'):
    """Класс."""

    name: str = attr('Номер')
    curriculum: List[Curriculum] = element(tag='Предмет')


class Occupation(BaseXmlModel, tag='Предмет'):
    """Связь Учитель/Предмет."""

    name: str = attr('Название')
    any_groups: Optional[YesNo] = attr('ЛюбыеГруппы', default=None, nillable=True)
    group_list: Optional[str] = None


class Teacher(BaseXmlModel, tag='Преподаватель'):
    """Учитель."""

    name: str = attr('ФИО')
    morning: Optional[str] = element(tag='ГруппыУтро', default=None)
    afternoon: Optional[str] = element(tag='ГруппыВечер', default=None)
    occupations: List[Occupation] = element(tag='Предмет')


class Settings(BaseXmlModel, tag='Настройки', skip_empty=True):
    """Корневой узел."""

    subjects: List[Subject] = wrapped('Предметы', element(tag='Предмет'))
    combinations: List[Combination] = wrapped('Расстановки', element(tag='Расстановка'))
    grades: List[Grade] = wrapped('Программа', element(tag='Класс'))
    teachers: List[Teacher] = wrapped('Преподаватели', element(tag='Преподаватель'))


def parse_settings(xml: str) -> Settings | None:
    """Инкапсуляция формата файла.

    :arg xml: Текст файла
    :return Settings: Распознанные данные
    """
    try:
        return Settings.from_xml(xml)
    except ValidationError as e:
        #!!! TODO logging
        print(e)
        return None
