FROM bitnami/python:3.7-prod

RUN useradd -ms /bin/bash chaddi
RUN install_packages ffmpeg gcc libc-dev jq

RUN pip3 install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN ln -s /usr/local/bin/docker-entrypoint.sh /
RUN mkdir /logs

COPY src /bot
WORKDIR /bot

RUN chown -R chaddi:chaddi /bot /logs
USER chaddi:chaddi

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "/bot/chaddi_bot.py"]
