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

- Utils
  - WebM to MP4 Converter
  - `/translate` - translates any message into English
- Economy
  - Take part in Chaddi's internal economy with ₹okda
  - `/rokda` - tells you how much ₹okda you have
  - `/daan` - give ₹okda to someone-else in need
  - `/gamble` - try your luck at the Chaddi Casino!
- Fun and Games
  - `/roll` - starts a dice roll game
  - `/quotes` - showcase the important messages in your Group
  - `/remind 5m "Chai break"` - Chaddi will remind you to take a break
- Monitoring
  - Inbuilt and rich monitoring and metrics web UI and Grafana dashboard

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

# Install dependencies using uv
$ uv sync

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

The Spacy language model is automatically installed via the dependencies in pyproject.toml.
