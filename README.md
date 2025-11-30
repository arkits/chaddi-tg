<h1 align="center">
    Chaddi Bot for Telegram
</h1>
<div align="center">
<em>
    A feature-rich Telegram Bot written in Python, powered by AI and community-driven fun.
</em> 
<br> <br> <br>
</div>

## About

Chaddi Bot is a comprehensive Telegram bot designed to enhance group chats with a variety of utilities, economy features, AI integrations, and fun mini-games.

## Features

### 🤖 AI & Utilities
- **Music Link Converter**: Automatically detects music links (Spotify, Apple Music, YouTube, etc.) and provides links for all other platforms.
- **`/ask`**: Ask ChatGPT anything! (Costs ₹okda).
- **`/dalle`**: Generate images using DALL-E.
- **`/translate`**: Translate any message into English.
- **WebM to MP4**: Automatically converts WebM videos to MP4 for better compatibility.

### 💰 Economy (₹okda)
- **`/rokda`**: Check your current balance of ₹okda.
- **`/daan`**: Transfer ₹okda to other users.
- **`/gamble`**: Try your luck at the Chaddi Casino!

### 🎉 Fun & Games
- **`/roll`**: Roll the dice.
- **`/quotes`**: Save and showcase memorable messages from your group.
- **`/remind`**: Set reminders (e.g., `/remind 5m "Chai break"`).
- **`/mom`**: Mom jokes and insults.

### 🛡️ Group Management
- **Command Restrictions**: Admins can enable or disable specific commands for their group via the web dashboard.

### 📊 Monitoring
- Built-in monitoring and metrics web UI with Grafana integration.

## Getting Started

### Requirements

- Python 3.13+
- PostgreSQL
- ffmpeg
- [uv](https://github.com/astral-sh/uv) (for fast Python package management)

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
  - Important settings in @BotFather:
    - Enable `Allow Groups`.
    - Disable `Privacy Mode`.

**Cryptography**

If you get any errors related to `cryptography`, please refer to [cryptography.io installation](https://cryptography.io/en/latest/installation.html).

**Spacy**

The Spacy language model is automatically installed via the dependencies in `pyproject.toml`.
