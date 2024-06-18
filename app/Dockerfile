FROM python:3.12.3-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_OPTIONS_NO_PIP=1 \
    POETRY_VIRTUALENVS_OPTIONS_NO_SETUPTOOLS=1


RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests git curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

WORKDIR /app
COPY pyproject.toml poetry.lock /app/

RUN $POETRY_HOME/bin/poetry install --only main,uvloop

FROM python:3.12.3-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY . /app/

RUN groupadd -r bot && \
    useradd -r -s /bin/false -g bot bot && \
    chown -R bot:bot /app

COPY --from=builder /app/.venv /app/.venv

USER bot
