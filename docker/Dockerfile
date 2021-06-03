FROM python:3.9-slim

RUN apt-get update && apt-get -y install \
    gcc \
    musl-dev \
    libffi-dev \
    libssl-dev \
    cargo \
    g++ \
    libpq-dev \
    git

RUN pip install --upgrade pip

WORKDIR /usr/src/chaddi-tg

COPY freeze.txt freeze.txt
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/chaddi-tg"

ENV CHADDI_BOT_PROFILE "dockerized"

COPY src src
COPY .git .git

WORKDIR /usr/src/chaddi-tg/src

CMD [ "python", "chaddi.py" ]