FROM python:3.12-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libxcb1 libxext6 libsm6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*
    

RUN pip install --no-cache-dir poetry

COPY pyproject.toml ./
COPY poetry.lock* ./

RUN poetry install --only main --no-root


COPY ./app ./app
COPY ./model ./model

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
