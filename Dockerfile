FROM python:3.9.1

EXPOSE 9808

RUN apt-get update && apt install -y locales libcurl4-openssl-dev libssl-dev \
        openssh-client \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN curl https://github.com/gruntwork-io/fetch/releases/download/v0.4.2/fetch_linux_amd64 -o /usr/local/bin/fetch -L \
        && chmod +x /usr/local/bin/fetch

RUN fetch --repo https://github.com/borgbackup/borg --release-asset="borg-linux64" --tag=1.1.16 /tmp && \
        fetch --repo https://github.com/danihodovic/borgmatic-binary --release-asset='borgmatic' --tag 1.5.13 /tmp && \
        mv /tmp/borg-linux64 /usr/local/bin/borg && \
        mv /tmp/borgmatic /usr/local/bin/borgmatic && \
        chmod +x /usr/local/bin/borg /usr/local/bin/borgmatic

WORKDIR /app/

RUN pip install poetry==1.1.4
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && poetry install --no-interaction #!COMMIT

ENV PYTHONUNBUFFERED 1

COPY . /app/

ENTRYPOINT ["python", "/app/cli.py"]
