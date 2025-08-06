"""Алгоритм генерации расписания."""

import math
import operator
from collections import Counter
from copy import copy
from functools import reduce
from pathlib import Path
from random import choice, shuffle
from typing import Dict, List

import src.parsers.serializer as serializer
import src.parsers.settings as settings
import src.processors.generator.structures as struct


class Generator:
    """Генератор расписания."""

    def __init__(self):
        """Инициализация."""
        self.__data = struct.GeneratorData()

    def process(self, src_path: Path, dst_path: Path):
        """Точка входа в алгоритм.

        :arg src_path: Путь к файлу с настройками
        :arg dst_path: Путь к файлу с расписанием
        """
        # Читаем XML с настройками
        with Path.open(src_path, 'r', encoding='utf-8') as file:
            src_content = file.read()
        # Парсим через pydantic_xml
        src_data = settings.parse_settings(src_content)
        if not src_data:
            raise Exception('Исходный файл имеет неверный формат')

        self.__data.fill_from_source(src_data)

        self.make_time_table()

        dst_data = self.__data.write_to_destination()

        dst_content = serializer.seralizer(dst_data)
        with Path.open(dst_path, 'wb') as file:
            file.write(dst_content)

    def make_time_table(self):
        """Расчет расписания."""
        # Обход групп в случайном порядке
        group_keys = list(self.__data.groups.keys())
        shuffle(group_keys)
        for group_key in group_keys:
            self.make_tt_for_group(group_key, self.__data.groups[group_key])

    def make_tt_for_group_effort(
        self,
        group_id: struct.GroupId,
        group_info: struct.GroupInfo,
        comb_nums: List[int],
    ) -> bool:
        """Составление расписания для группы - попытка.

        :arg group_id: Номер группы
        :arg group_info: Данные группы
        :arg comb_nums: Индекс для перебора комбинаций
        :return: Попытка успешная
        """

        def check_combination() -> bool:
            """Проверка комбинации.

            :return: Комбинация подходит
            """
            # В комбинации есть лишние предметы
            if set(comb_counter.keys()) - set(curriculum.keys()):
                return False

            # Часов в комбинации больше, чем нужно
            if reduce(
                operator.add,
                [comb_counter[k] > curriculum[k].hours for k in comb_counter],
            ):
                return False

            # Проверка по дням недели
            days_set_list = [curriculum[k].days_of_week for k in comb_counter]
            return _day_num in set.union(*days_set_list)

        def teachers_vacant(tutors_list) -> bool:
            """Проверка занятости учителя.

            :return: Учитель свободен
            """
            for npp, lesson_info in tutors_list.items():
                if not lesson_info.teacher_id:
                    continue
                tt_key = struct.TimeTableKey(
                    day=_day_num,
                    time_of_day=group_info.time_of_day,
                    npp=npp,
                )
                if tt_key in self.__data.teachers[lesson_info.teacher_id].time_table:
                    return False
            return True

        def unmounted_vacant(tutors_list) -> bool:
            """Проверка занятости непривязанного учителя.

            :return: Учитель свободен
            """
            # Предметы, для которых надо подобрать учителя
            subject_map: Dict[struct.SubjectId, List[int]] = {}
            for npp, lesson_info in tutors_list.items():
                if not lesson_info.teacher_id:
                    subject_map.setdefault(lesson_info.subject_id, []).append(npp)
            if not subject_map:
                return True
            all_teachers_found = True
            for subject in subject_map:
                selected_teacher = 0
                vacant_teachers = []
                for teacher_id in self.__data.unassigned_teachers[subject]:
                    vacant_flag = True
                    # Проверим, свободен ли учитель в этот момент
                    for npp in subject_map[subject]:
                        tt_key = struct.TimeTableKey(
                            day=_day_num,
                            time_of_day=group_info.time_of_day,
                            npp=npp,
                        )
                        if tt_key in self.__data.teachers[teacher_id].time_table:
                            vacant_flag = False
                    if not vacant_flag:
                        continue
                    vacant_teachers.append(teacher_id)
                    # Проверим, есть ли у него другие занятия в этот день
                    # Если есть - это преимущество
                    for tt_key in self.__data.teachers[teacher_id].time_table:
                        if tt_key.day == _day_num:
                            selected_teacher = teacher_id
                            for npp in subject_map[subject]:
                                tutors_list[npp].teacher_id = teacher_id
                            # Эту фичу оставил на будущее
                            # она нужна, если предмет идет в разные дни
                            # Но значения нужно удалять при каждой попытке
                            # self.__data.subject_assignment[
                            #     struct.SubjectAssignmentKey(
                            #         group=group_id,
                            #         subject=subject)] = teacher_id

                # С преимуществом никого не нашли
                if not selected_teacher and vacant_teachers:
                    shuffle(vacant_teachers)
                    selected_teacher = choice(vacant_teachers)
                    for npp in subject_map[subject]:
                        tutors_list[npp].teacher_id = selected_teacher
                all_teachers_found = all_teachers_found and bool(selected_teacher > 0)
            return all_teachers_found

        def apply_combination(tutors_list):
            """Добавляем комбинацию в расписание."""
            # Уменьшаем доступное количество часов
            for k in comb_counter:
                curriculum[k].hours -= comb_counter[k]
            # Добавляем расписание для группы
            for sbj_npp, sbj_info in tutors_list.items():
                group_info.time_table[
                    struct.TimeTableKey(
                        day=_day_num,
                        time_of_day=group_info.time_of_day,
                        npp=sbj_npp,
                    )
                ] = struct.GroupTimeTableInfo(
                    subject_id=sbj_info.subject_id,
                    teacher_id=sbj_info.teacher_id,
                )

        # Перечень предметов
        curriculum = {
            ck.subject: copy(cd)
            for ck, cd in (self.__data.curriculum.items())
            if ck.grade == group_info.grade
        }

        combs_used = set()
        # По дням недели
        for _day_num in struct.DayOfWeek:
            # Подберем комбинацию предметов на этот день
            for comb_num in comb_nums:
                # Каждая комбинация предметов уникальна в рамках группы
                if comb_num in combs_used:
                    continue
                combination = self.__data.combinations[comb_num]
                # Количество часов по предметам в комбинации
                comb_counter = Counter(combination)
                # Проверка комбинации
                if not check_combination():
                    continue
                # Выборка педагогов
                tutors = {
                    n: struct.GroupTimeTableInfo(
                        subject_id=s,
                        teacher_id=self.__data.subject_assignment.get(
                            struct.SubjectAssignmentKey(group=group_id, subject=s),
                            0,
                        ),
                    )
                    for n, s in enumerate(combination, 1)
                }
                # Проверка занятости педагогов
                if not teachers_vacant(tutors):
                    continue
                # Подбор непривязанных педагогов
                if not unmounted_vacant(tutors):
                    continue
                # Комбинация одобрена
                apply_combination(tutors)
                combs_used.add(comb_num)
                break

        # Все часы удалось распределить
        return reduce(operator.add, [v.hours for v in curriculum.values()]) == 0

    def map_to_teachers_tt(
        self,
        group_id: struct.GroupId,
        group_tt: struct.GroupTimeTable,
    ):
        """Преобразование расписания для групп в расписание для учителей.

        :arg group_id: Номер группы
        :arg group_tt: Расписание группы
        """
        for gtt_key, gtt_info in group_tt.items():
            if gtt_info.teacher_id:
                tt_key = struct.TimeTableKey(
                    day=gtt_key.day,
                    time_of_day=gtt_key.time_of_day,
                    npp=gtt_key.npp,
                )
                tt_info = struct.TimeTableInfo(
                    subject_id=gtt_info.subject_id,
                    group=group_id,
                )
                self.__data.teachers[gtt_info.teacher_id].time_table[tt_key] = tt_info

    def make_tt_for_group(self, group_id: struct.GroupId, group_info: struct.GroupInfo):
        """Составление расписания для группы.

        :arg group_id: Номер группы
        :arg group_info: Данные группы
        """
        combs_count = len(self.__data.combinations)
        # Индекс по комбинациям
        comb_nums = list(range(combs_count))

        # Максимальная сложность перебора - факториальная
        # (число сочетаний)
        efforts_count = math.comb(combs_count, 3)
        for _ in range(efforts_count):
            # Перебор комбинаций в случайном порядке
            shuffle(comb_nums)
            if self.make_tt_for_group_effort(group_id, group_info, comb_nums):
                break
            group_info.time_table.clear()
        # Перенос расписания группы на преподавателей
        if group_info.time_table:
            self.map_to_teachers_tt(group_id, group_info.time_table)
        else:
            #!!! Ошибка
            pass
