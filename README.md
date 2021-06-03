<h1 align="center">
    Chaddi Bot for Telegram
</h1>
<div align="center">
<em>
    A tailor made (and mediocre) Telegram Bot written in Python 3.
</em> 
<br> <br> <br>
</div>

## About

Chaddi Bot has a variety of features to make your Telegram experience a whole lot more fun.

## Features

- WebM to MP4 Converter

## Getting Started

### Requirements

- Python 3.9
- PostgreSQL
- ffmpeg

### Running

**With Docker**

```bash
# Start the postgres container
$ docker-compose up -d postgres

# Build the chaddi-tg Docker image
$ docker-compose build chaddi-tg

# Run the chaddi-tg Docker image
$ docker-compose up chaddi-tg --force-recreate

# Optional: run the metrics stack
$ docker-compose up -d grafana prometheus
```

**With Local Python**

```bash
# Create a database for persistence
$ psql -c "CREATE DATABASE chaddi_tg"

# Setup Python virtualenv
$ python3 -m venv .venv
$ source .venv/bin/activate

# Install the Python libs
$ pip install -r requirments.txt

# Run Chaddi!
$ ./run.sh
```

### Troubleshooting

**Setup your Telegram Bot**

- Create your bot with [@BotFather](https://telegram.me/botfather).
  - Refer to Telegram's [documentation](https://core.telegram.org/bots#3-how-do-i-create-a-bot) for more help on creating bots.
  - Important settings in @BotFather -
    - Enable `Allow Groups`.
    - Disable `Privacy Mode`.

**Cryptography**

If you get any errors related to `cryptography`, please refer to - https://cryptography.io/en/latest/installation.html

**Spacy**

To download the latest Spacy language model -

```bash
python -m spacy download en_core_web_sm
```
