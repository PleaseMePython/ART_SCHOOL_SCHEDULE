"""Структуры данных для генерации расписания."""

from calendar import Day
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Set

import src.parsers.schedule as dst
import src.parsers.settings as src

# Номер группы (может включать букву)
type GroupId = str

# Номер класса
type GradeId = str

# Идентификатор учителя
type TeacherId = int

# Идентификатор предмета
type SubjectId = int

# День недели
DayOfWeek = Day


@dataclass
class DayOfWeekInfo:
    """Дни недели."""

    day_name: str  # Наименование поля модели
    day_description: str  # Наименование дня по-русски


# Справочник дней недели
days_of_week: Dict[DayOfWeek, DayOfWeekInfo] = {
    DayOfWeek.MONDAY: DayOfWeekInfo(day_name='monday', day_description='Понедельник'),
    DayOfWeek.TUESDAY: DayOfWeekInfo(day_name='tuesday', day_description='Вторник'),
    DayOfWeek.WEDNESDAY: DayOfWeekInfo(day_name='wednesday', day_description='Среда'),
    DayOfWeek.THURSDAY: DayOfWeekInfo(day_name='thursday', day_description='Четверг'),
    DayOfWeek.FRIDAY: DayOfWeekInfo(day_name='friday', day_description='Пятница'),
    DayOfWeek.SATURDAY: DayOfWeekInfo(day_name='saturday', day_description='Суббота'),
    DayOfWeek.SUNDAY: DayOfWeekInfo(day_name='sunday', day_description='Воскресенье'),
}


# Смена
class TimeOfDay(IntEnum):
    """Смена."""

    MORNING = 1  # Первая смена (утро)
    AFTERNOON = 2  # Вторая смена (вечер)


@dataclass(frozen=True)
class TimeTableKey:
    """Ключ для расписания."""

    day: DayOfWeek  # День недели
    time_of_day: TimeOfDay  # Смена
    npp: int  # Номер урока


@dataclass
class TimeTableInfo:
    """Урок(предмет/группа)."""

    subject_id: SubjectId  # Предмет
    group: GroupId  # Группа


@dataclass
class GroupTimeTableInfo:
    """Урок(предмет/группа)."""

    subject_id: SubjectId  # Предмет
    teacher_id: TeacherId  # Учитель


# Расписание на день
type TimeTable = dict[TimeTableKey, TimeTableInfo]

# Расписание для групп
type GroupTimeTable = dict[TimeTableKey, GroupTimeTableInfo]


@dataclass
class SubjectInfo:
    """Настройки предметов."""

    subject_name: str  # Название предмета
    no_split: bool  # Не разделять по дням
    one_group: bool  # Одна группа за смену у преподавателя


@dataclass
class GroupInfo:
    """Параметры группы."""

    grade: GradeId  # Класс
    time_of_day: TimeOfDay  # Смена
    class_master: TeacherId  # Классный руководитель
    processed: bool  # Группа обработана
    time_table: GroupTimeTable  # Расписание


@dataclass(frozen=True)
class CurriculumKey:
    """Ключевые поля программы."""

    grade: GradeId  # Класс
    subject: SubjectId  # Предмет


@dataclass
class CurriculumInfo:
    """Программа."""

    hours: int  # Часов в неделю
    days_of_week: set[DayOfWeek]  # Дни недели


@dataclass
class TeacherSubjectInfo:
    """Предметы, которые ведет учитель."""

    autoselect_groups: bool  # Автоподбор групп
    groups: set[GroupId]  # Список групп


@dataclass
class TeacherInfo:
    """Данные учителя."""

    teacher_name: str  # ФИО учителя
    subjects: dict[SubjectId, TeacherSubjectInfo]  # Предметы
    time_table: TimeTable  # Расписание


@dataclass(frozen=True)
class SubjectAssignmentKey:
    """Ключ для закрепления учителя за предметом."""

    group: GroupId  # Группа
    subject: SubjectId  # Предмет


# Предметы
type Subjects = dict[SubjectId, SubjectInfo]
# Группы
type Groups = dict[GroupId, GroupInfo]
# Программа для каждого класса
type Curriculum = dict[CurriculumKey, CurriculumInfo]
# Справочник учителей
type Teachers = dict[TeacherId, TeacherInfo]
# Закрепление учителя за предметом
type SubjectAssignment = dict[SubjectAssignmentKey, TeacherId]
type UnassignedTeachers = dict[SubjectId, List[TeacherId]]
# Допустимый порядок уроков в смене
type Combination = list[SubjectId]
type CombinationList = list[Combination]


def split_days_of_week(days_string: str) -> Set[DayOfWeek]:
    """Определение дней недели.

    :arg days_string: Дни недели в виде ПнВтСрЧтПтСбВс
    :return: Множество дней недели
    """
    days_set: Set[DayOfWeek] = set()
    uppercase = days_string.upper()
    if 'ПН' in uppercase:
        days_set.add(DayOfWeek.MONDAY)
    if 'ВТ' in uppercase:
        days_set.add(DayOfWeek.TUESDAY)
    if 'СР' in uppercase:
        days_set.add(DayOfWeek.WEDNESDAY)
    if 'ЧТ' in uppercase:
        days_set.add(DayOfWeek.THURSDAY)
    if 'ПТ' in uppercase:
        days_set.add(DayOfWeek.FRIDAY)
    if 'СБ' in uppercase:
        days_set.add(DayOfWeek.SATURDAY)
    if 'ВС' in uppercase:
        days_set.add(DayOfWeek.SUNDAY)
    return days_set


class GeneratorData:
    """Данные для генератора."""

    def __init__(self):
        """Инициализация."""
        self.subjects: Subjects = {}  # Предметы
        self.groups: Groups = {}  # Группы
        self.curriculum: Curriculum = {}  # Учебный план
        self.teachers: Teachers = {}  # Учителя
        self.subject_assignment: SubjectAssignment = {}  # Закрепление учителя
        self.unassigned_teachers: UnassignedTeachers = {}  # Свободные учителя
        self.combinations: CombinationList = []  # Порядок уроков в смене

        # Поиск идентификаторов по имени
        self.subjects_names_unique: Dict[str, SubjectId] = {}
        self.teachers_names_unique: Dict[str, TeacherId] = {}

    def fill_from_source(self, source: src.Settings):
        """Заполнение из файла.

        :arg source: Данные из файла
        """
        # Предметы
        self.fill_subjects(source)

        # Порядок уроков в смене
        self.fill_combinations(source)

        # Учебный план
        self.fill_curriculum(source)

        # Учителя
        self.fill_teachers(source)

    def fill_subjects(self, source: src.Settings):
        """Заполнение предметов из файла.

        :arg source: Данные из файла
        """
        subject_id: SubjectId = 0
        for subject in source.subjects:
            if subject.name in self.subjects_names_unique:
                # !!! TODO logging
                continue
            subject_id += 1
            self.subjects_names_unique[subject.name] = subject_id
            self.subjects[subject_id] = SubjectInfo(
                subject_name=subject.name,
                no_split=src.yesno_to_bool(subject.no_split),
                one_group=src.yesno_to_bool(subject.one_group),
            )

    def fill_combinations(self, source: src.Settings):
        """Заполнение примерных планов смены.

        :arg source: Данные из файла
        """
        for src_combination in source.combinations:
            self.combinations.append(
                [
                    self.subjects_names_unique[comb.strip()]
                    for comb in src_combination.day_plan.split(',')
                ],
            )

    def fill_curriculum(self, source: src.Settings):
        """Заполнение учебного плана из файла.

        :arg source: Данные из файла
        """
        for src_grade in source.grades:
            for src_curriculum in src_grade.curriculum:
                subject_id = self.subjects_names_unique.get(src_curriculum.name, 0)
                curriculum_key = CurriculumKey(grade=src_grade.name, subject=subject_id)
                if curriculum_key in self.curriculum:
                    # !!! TODO logging
                    continue
                self.curriculum[curriculum_key] = CurriculumInfo(
                    hours=src_curriculum.hours,
                    days_of_week=split_days_of_week(src_curriculum.days_of_week),
                )

    def fill_teachers(self, source: src.Settings):
        """Заполнение учителей из файла.

        :arg source: Данные из файла
        """

        def fill_groups(src_groups: (str | None), time_of_day: TimeOfDay):
            """Заполнение групп из файла.

            :arg src_groups: Список групп через запятую
            :arg time_of_day: Смена
            """
            if src_groups is None:
                return
            groups_split = src_groups.split(',')
            for src_group in groups_split:
                default_groups.add(src_group)
                self.groups[src_group] = GroupInfo(
                    grade=src_group[0],
                    time_of_day=time_of_day,
                    class_master=teacher_id,
                    processed=False,
                    time_table={},
                )

        def fill_occupation():
            """Заполнение предметов, которые ведет учитель."""
            for src_occupation in src_teacher.occupations:
                subject_id = self.subjects_names_unique.get(src_occupation.name, 0)
                any_groups = src.yesno_to_bool(src_occupation.any_groups)
                group_set = set()
                if not any_groups:
                    if src_occupation.group_list:
                        group_set = set(src_occupation.group_list.split(','))
                    else:
                        group_set = default_groups
                else:
                    self.unassigned_teachers.setdefault(subject_id, []).append(
                        teacher_id,
                    )
                teacher_info.subjects[subject_id] = TeacherSubjectInfo(
                    autoselect_groups=any_groups, groups=group_set,
                )
                for group in group_set:
                    self.subject_assignment[
                        SubjectAssignmentKey(group=group, subject=subject_id)
                    ] = teacher_id

        teacher_id: TeacherId = 0
        for src_teacher in source.teachers:
            if src_teacher.name in self.teachers_names_unique:
                # !!! TODO logging
                continue
            teacher_id += 1
            self.teachers_names_unique[src_teacher.name] = teacher_id
            teacher_info = TeacherInfo(
                teacher_name=src_teacher.name, subjects={}, time_table={},
            )
            default_groups: Set[GroupId] = set()
            fill_groups(src_teacher.morning, TimeOfDay.MORNING)
            fill_groups(src_teacher.afternoon, TimeOfDay.AFTERNOON)
            fill_occupation()
            self.teachers[teacher_id] = teacher_info

    def write_to_destination(self) -> dst.Schedule:
        """Сохранение расписания в целевую структуру.

        :return dst.Schedule: Целевая структура
        """
        destination = dst.Schedule(teachers=[])
        for _, teacher in self.teachers.items():
            dst_teacher = dst.Teacher(name=teacher.teacher_name)
            for time_table_key, time_table_value in teacher.time_table.items():
                subject_name = self.subjects[time_table_value.subject_id].subject_name
                lesson = dst.Lesson(
                    npp=time_table_key.npp,
                    subject=subject_name,
                    group=time_table_value.group,
                )
                day_name = days_of_week[time_table_key.day].day_name
                dst_day = getattr(dst_teacher, day_name, None)
                if dst_day is None:
                    setattr(dst_teacher, day_name, dst.Day())
                    dst_day = getattr(dst_teacher, day_name, None)
                if time_table_key.time_of_day == TimeOfDay.MORNING:
                    if dst_day.morning is None:
                        dst_day.morning = dst.PartOfDay(lessons=[])
                    dst_day.morning.lessons.append(lesson)
                else:
                    if dst_day.afternoon is None:
                        dst_day.afternoon = dst.PartOfDay(lessons=[])
                    dst_day.afternoon.lessons.append(lesson)
            destination.teachers.append(dst_teacher)
        return destination
