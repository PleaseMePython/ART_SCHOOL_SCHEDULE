"""Переиспользуемые константы."""

from pathlib import Path
from typing import Final

PROJ_NAME: Final[str] = 'ART_SCHOOL_SCHEDULE'
PROJ_DESCR: Final[str] = 'Генератор расписания школы дополнительного образования'
PROJ_PATH: Final[Path] = [
    p for p in Path(__file__).parents if p.parts[-1] == PROJ_NAME
][0]
TESTFILE_PATH: Final[Path] = PROJ_PATH.joinpath('tests').joinpath('test_files')
FILE_EXTENSION: Final[str] = '.xml'
FILE_MIME_TYPE: Final[str] = 'application/xml'
XLSX_MIME_TYPE: Final[str] = (
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
