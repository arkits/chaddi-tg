# ChaddiBot
http://t.me/ChaddiBot

A tailor made (and mediocre) Telegram Bot written in Python 3.

## Running

* Clone the repo
* Setup virtualenv

```bash
python3 -m venv .env
source .env/bin/activate
```

* Install from requirements.txt
```bash
pip install -r requirements.txt
```
* Update `src/config.py` with relevant information
 
```python

# Bot Username
bot_username = "ChaddiBot"

# Telegram Bot API Token
tg_bot_token = "YOUR-TG-BOT-API-TOKEN-HERE"

# Telegram Webhook URL
tg_webhook_url = "https://chaddibot.com/"

# Chat ID of your testing group
test_chat_id = '-0123456789'

# Chat ID of your main group
mains_chat_id = '-123456789'
true_chat_id = '-123456789'

# Whether runnning as dev or not
is_dev = True

# Choose which Text to Speech Engine to use.
# Available:
tts_engine = "gTTS" # Google TTS
# tts_engine = "festival" # Festival TTS - Requires Festival TTS installed.
```

* Run locally with `python bot_chaddi.py`.
* Run in prod with `./run_prod.sh`.

### Setup for /mom handler

The `/mom` handler uses spaCy library. It needs to be installed with the English language model.

```bash 
python -m spacy download en_core_web_sm
```

### Setup for WebM converter

WebM files are converted into mp4 by `src/handlers/webm_converter.py` using ffmpeg. Make sure to install that. 

### Setup for Webhook

Refer to python-telegram-bot's official documentation - https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks

To check if your setup is correct, do a GET at ` https://api.telegram.org/bot{my_bot_token}/getWebhookInfo `.


