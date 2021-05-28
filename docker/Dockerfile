FROM python:3.9-alpine

RUN apk add gcc musl-dev libffi-dev openssl-dev cargo

RUN pip install --upgrade pip

WORKDIR /usr/src/chaddi-tg

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src src

CMD [ "python", "src/chaddi.py" ]