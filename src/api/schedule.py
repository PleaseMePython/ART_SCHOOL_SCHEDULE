"""API генерации расписания."""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks

import src.common.constants as constants
from src.processors.checker import Checker
from src.processors.excel import Excel
from src.processors.generator.generator import Generator

router = APIRouter()


@router.post('/api/v1/generate/', response_class=FileResponse)
async def api_generate(files: List[UploadFile], background_tasks: BackgroundTasks):
    """Генерация текстового файла расписания.

    :arg files: Исходный файл
    :arg background_tasks: Фоновое задание по очистке временной папки
    """
    with TemporaryDirectory(delete=False) as temp_dir:
        source_file_name = Path(temp_dir).joinpath('source' + constants.FILE_EXTENSION)
        destination_file_name = Path(temp_dir).joinpath(
            'destination' + constants.FILE_EXTENSION,
        )
        source_file_found = False
        for file in files:
            filename = str(file.filename)
            if file.content_type == constants.FILE_MIME_TYPE and filename.endswith(
                constants.FILE_EXTENSION,
            ):
                with Path.open(source_file_name, 'wb') as source_file:
                    source_file.write(await file.read())
                    source_file_found = True
        if not source_file_found:
            raise HTTPException(415)
        gen = Generator()
        gen.process(source_file_name, destination_file_name)
        background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
    return destination_file_name


@router.post('/api/v1/check/')
async def api_check(files: List[UploadFile]):
    """Проверка текстового файла расписания.

    :arg files: Исходный файл
    """
    with TemporaryDirectory(delete=True) as temp_dir:
        source_file_name = Path(temp_dir).joinpath('source' + constants.FILE_EXTENSION)
        source_file_found = False
        for file in files:
            filename = str(file.filename)
            if file.content_type == constants.FILE_MIME_TYPE and filename.endswith(
                constants.FILE_EXTENSION,
            ):
                with Path.open(source_file_name, 'wb') as source_file:
                    source_file.write(await file.read())
                    source_file_found = True
        if not source_file_found:
            raise HTTPException(415)
        chk = Checker()
        return chk.process(source_file_name)


@router.post('/api/v1/excel/', response_class=FileResponse)
async def api_excel(files: List[UploadFile], background_tasks: BackgroundTasks):
    """Преобразование текстового файла расписания в MS Excel.

    :arg files: Исходный файл + файл шаблона XLSX
    :arg background_tasks: Фоновое задание по очистке временной папки
    """
    with TemporaryDirectory(delete=False) as temp_dir:
        source_file_name = Path(temp_dir).joinpath('source' + constants.FILE_EXTENSION)
        xlsx_template_name = Path(temp_dir).joinpath('template.xlsx')
        xlsx_result_name = Path(temp_dir).joinpath('result.xlsx')
        source_file_found = False
        template_found = False
        for file in files:
            filename = str(file.filename)
            if file.content_type == constants.FILE_MIME_TYPE and filename.endswith(
                constants.FILE_EXTENSION,
            ):
                with Path.open(source_file_name, 'wb') as source_file_file:
                    source_file_file.write(await file.read())
                    source_file_found = True
            elif (
                file.content_type == constants.XLSX_MIME_TYPE
                and filename.endswith('.xlsx')
            ):
                with Path.open(xlsx_template_name, 'wb') as xlsx_file:
                    xlsx_file.write(await file.read())
                    template_found = True
        if not source_file_found or not template_found:
            raise HTTPException(415)
        ex = Excel()
        ex.process(
            template_path=xlsx_template_name,
            src_path=source_file_name,
            dst_path=xlsx_result_name,
        )
        background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
    return xlsx_result_name
