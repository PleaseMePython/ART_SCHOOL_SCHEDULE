FROM python:3.12-slim

WORKDIR /app

COPY ./pyproject.toml /code/pyproject.toml

RUN python -m pip install --upgrade pip
RUN python -m pip install poetry
RUN python -m poetry env activate
RUN python -m poetry lock
RUN python -m poetry install

COPY . /code/.

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]