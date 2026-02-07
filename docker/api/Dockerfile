FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip && pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY src ./src
COPY alembic.ini ./

COPY commands /commands
RUN chmod +x /commands/*.sh

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
