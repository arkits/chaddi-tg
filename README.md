# ChaddiBot
http://t.me/ChaddiBot

[![CircleCI](https://circleci.com/gh/arkits/chaddi-tg/tree/master.svg?style=svg)](https://circleci.com/gh/arkits/chaddi-tg/tree/master)

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

# Chat ID of your testing group
test_chat_id = '-0123456789'

# Chat ID of your main group
mains_chat_id = '-123456789'
true_chat_id = '-123456789'

# Whether runnning as dev or not
is_dev = True

# Choose which Text to Speech Engine to use.
tts_engine = "gTTS" # Google TTS

```
* Get your TeleGram Bot API Token
* How to get Telegram bot API token: https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token
* Paste your Telegram token id in `tg_bot_token` in `config.py`


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


