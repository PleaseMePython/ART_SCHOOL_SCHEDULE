"""Консольный клиент."""

import argparse
import sys
from pathlib import Path

import requests

from src.common.constants import (
    FILE_EXTENSION,
    FILE_MIME_TYPE,
    PROJ_DESCR,
    XLSX_MIME_TYPE,
)
from src.processors.checker import Checker
from src.processors.excel import Excel
from src.processors.generator.generator import Generator


def parse_arguments() -> argparse.Namespace:
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(description=PROJ_DESCR)
    parser.add_argument(
        '-u',
        '--url',
        type=str,
        help='URL-адрес',
    )

    parser.add_argument(
        '-l',
        '--local',
        action='store_true',
        help='работа с локальной версией',
    )

    parser.add_argument(
        '-g',
        '--generate',
        action='store_true',
        help='расчет расписания',
    )
    parser.add_argument(
        '-c',
        '--check',
        action='store_true',
        help='проверка расписания',
    )
    parser.add_argument(
        '-e',
        '--excel',
        action='store_true',
        help='вывод в excel',
    )
    parser.add_argument(
        '-s',
        '--source',
        type=str,
        help='исходный файл XML',
    )
    parser.add_argument(
        '-t',
        '--template',
        type=str,
        help='файл шаблона Excel',
    )
    parser.add_argument(
        '-d',
        '--destination',
        type=str,
        help='целевой файл XML или XLSX',
    )
    arg_val = parser.parse_args()
    return arg_val

def check_arguments(arg_val: argparse.Namespace):
    """Проверка аргументов.

    :param arg_val: Аргументы командной строки
    """
    if not arg_val.generate and not arg_val.check and not arg_val.excel:
        wanna_gen = input('Хотите сгенерировать расписание(Да/Нет)?')
        arg_val.generate = wanna_gen.upper() == 'ДА'
        if not arg_val.generate:
            wanna_chk = input('Хотите проверить расписание(Да/Нет)?')
            arg_val.check = wanna_chk.upper() == 'ДА'
        if not arg_val.generate and not arg_val.check:
            wanna_excel = input('Хотите сформировать Excel-файл(Да/Нет)?')
            arg_val.excel = wanna_excel.upper() == 'ДА'

    if not arg_val.generate and not arg_val.check and not arg_val.excel:
        raise Exception('Не выбран режим работы (справка --help)')

    if not arg_val.url and not arg_val.local:
        arg_val.url = input('Введите адрес сервера')

    if not arg_val.url:
        arg_val.local = True

    if not arg_val.source:
        arg_val.source = input('Введите путь к исходному файлу')

    if not arg_val.template and arg_val.excel:
        arg_val.template = input('Введите путь к файлу шаблона')

    if not arg_val.check and not arg_val.destination:
        arg_val.destination = input('Введите путь к целевому файлу')

    if not arg_val.source:
        raise Exception('Не указан исходный файл (справка --help)')

    if arg_val.excel and not arg_val.template:
        raise Exception('Не указан файл шаблона (справка --help)')

    if not arg_val.check and not arg_val.destination:
        raise Exception('Не указан целевой файл (справка --help)')

def local_client(arg_val: argparse.Namespace):
    """Клиент для локальной проверки программы."""
    if arg_val.generate:
        gen = Generator()
        gen.process(src_path=Path(arg_val.source), dst_path=Path(arg_val.destination))
    elif arg_val.check:
        chk = Checker()
        chk.process(src_path=Path(arg_val.source))
    elif arg_val.excel:
        ex = Excel()
        ex.process(
            template_path=Path(arg_val.template),
            src_path=Path(arg_val.source),
            dst_path=Path(arg_val.destination),
        )

def http_client(arg_val: argparse.Namespace):
    """Клиент для работы с программой через http."""
    files_to_upload = [('files',('source' + FILE_EXTENSION,
                                 Path.open(arg_val.source,'rb'),
                                 FILE_MIME_TYPE)) ]
    if arg_val.excel:
        files_to_upload.append(('files',('template.xlsx',
                                 Path.open(arg_val.template,'rb'),
                                 XLSX_MIME_TYPE)))
    api_url = arg_val.url
    if ':' not in api_url:
        api_url += ':8000'
    if arg_val.generate:
        api_url += '/api/v1/generate/'
    elif arg_val.check:
        api_url += '/api/v1/check/'
    elif arg_val.excel:
        api_url += '/api/v1/excel/'

    response = requests.post(
        api_url, files=files_to_upload,
        timeout=10,
    )

    if response.status_code == 200:
        if arg_val.destination:
            with Path.open(arg_val.destination, 'wb') as file:
                file.write(response.content)
    else:
        raise Exception(f'Ошибка HTTP, статус {response.status_code}')


def cli_main() -> None:
    """Запуск из консоли."""
    arg_val = parse_arguments()
    try:
        check_arguments(arg_val)

        if arg_val.local:
            local_client(arg_val)
        else:
            http_client(arg_val)
    except Exception as err:
        print(err)
        sys.exit(1)

    print('Файлы обработаны успешно!!!')


if __name__ == '__main__':
    cli_main()
