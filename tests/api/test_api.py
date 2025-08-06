import pytest

from httpx import AsyncClient, ASGITransport

from src.main import app
from src.common.constants import (TESTFILE_PATH, XLSX_MIME_TYPE,
                                  FILE_MIME_TYPE,FILE_EXTENSION)


@pytest.mark.integration_test
@pytest.mark.asyncio
async def test_api_generate_status_ok():
    files_to_upload = [
        ('files', ('source' + FILE_EXTENSION, open(TESTFILE_PATH.joinpath(
            'settings' + FILE_EXTENSION), 'rb'), FILE_MIME_TYPE)),
    ]
    async with (AsyncClient(transport=ASGITransport(app=app),
                            base_url='http://test')) as ac:
        response= await ac.post(url='/api/v1/generate/',files=files_to_upload)
    assert response.status_code == 200

@pytest.mark.integration_test
@pytest.mark.asyncio
async def test_api_check_status_ok():
    files_to_upload = [
        ('files', ('source' + FILE_EXTENSION, open(TESTFILE_PATH.joinpath(
            'schedule' + FILE_EXTENSION), 'rb'), FILE_MIME_TYPE)),
    ]
    async with (AsyncClient(transport=ASGITransport(app=app),
                            base_url='http://test')) as ac:
        response= await ac.post(url='/api/v1/check/',files=files_to_upload)
    assert response.status_code == 200

@pytest.mark.integration_test
@pytest.mark.asyncio
async def test_api_excel_status_ok():
    files_to_upload = [
        ('files', ('source' + FILE_EXTENSION, open(TESTFILE_PATH.joinpath(
            'schedule' + FILE_EXTENSION), 'rb'), FILE_MIME_TYPE)),
        ('files', ('template.xlsx', open(TESTFILE_PATH.joinpath(
            'Template.xlsx'), 'rb'), XLSX_MIME_TYPE))
    ]
    async with (AsyncClient(transport=ASGITransport(app=app),
                            base_url='http://test')) as ac:
        response= await ac.post(url='/api/v1/excel/',files=files_to_upload)
    assert response.status_code == 200

