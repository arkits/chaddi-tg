# ChaddiBot
http://t.me/ChaddiBot

[![CircleCI](https://circleci.com/gh/arkits/chaddi-tg/tree/master.svg?style=svg)](https://circleci.com/gh/arkits/chaddi-tg/tree/master)

A tailor made (and mediocre) Telegram Bot written in Python 3.

## Setup and Deployment

* Register your bot with @botfather. [Refer to Telegram's documentation](https://core.telegram.org/bots#3-how-do-i-create-a-bot).
* Clone the repo.
* Setup virtualenv.

```bash
python3 -m venv .env
source .env/bin/activate
```

* Install from requirements.txt
```bash
cd chaddi-tg
pip install -r requirements.txt
```
* Create `config.py` in `src/`
* Add `src/config.py` with relevant information


```python

# Bot Username
bot_username = "ChaddiBot"

# Telegram Bot API Token
tg_bot_token = "YOUR-TG-BOT-API-TOKEN-HERE"

# Telegram Webhook URL
tg_webhook_url = "https://chaddibot.com/"

# Whether runnning as dev or not
is_dev = True

# Choose which Text to Speech Engine to use.
tts_engine = "gTTS" # Google TTS

```
* Run locally with `python bot_chaddi.py`.
* Run in prod with `./run_prod.sh`.

### `/mom` handler

The `/mom` handler uses spaCy library. It needs to be installed with the English language model.

```bash 
python -m spacy download en_core_web_sm
```

### WebM converter

WebM files are converted into mp4 by `src/handlers/webm_converter.py` using ffmpeg. Make sure to install that. 

### Webhook conectivity

[Refer to python-telegram-bot's official documentation](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks)

To check if your setup is correct, do a GET at ` https://api.telegram.org/bot{my_bot_token}/getWebhookInfo `.


