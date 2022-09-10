FROM python:alpine AS builder

RUN apk update && apk add \
    alpine-sdk openssl-dev libffi-dev python3-dev cargo

ENV POETRY_VIRTUALENVS_CREATE=false

RUN pip install poetry

WORKDIR /app/
COPY ./pyproject.toml ./poetry.lock /app/
RUN poetry install --only main
COPY . /app/

RUN pyinstaller pyinstaller.spec

FROM b3vis/borgmatic:latest
COPY --from=builder /app/dist/borg-exporter /bin/borg-exporter

ENTRYPOINT ["borg-exporter", "run"]
