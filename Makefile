setup:
	python -m pip install --upgrade pip
	python -m pip install poetry
	python -m poetry env activate
	python -m poetry lock
	python -m poetry install

run:
	uvicorn src.main:app --reload
client:
	python src\cli.py
lint:
	python -m ruff check src
format:
	python -m ruff format src
fix:
	python -m ruff check src --fix
typing:
	python -m mypy src --follow-untyped-imports
test:
	coverage run --source=src -m pytest -v .\tests\api\test_api.py
	coverage report -m