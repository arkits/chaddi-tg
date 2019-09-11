# ChaddiBot
http://t.me/ChaddiBot

A tailor made (and mediocre) Telegram Bot written in Python 3.

## Running

* Clone the repo
* Install from requirements.txt
* Update `config.py` with relevant information
 
```python
# Telegram Bot API Token
tg_bot_token = "YOUR-TG-BOT-API-TOKEN-HERE"

# Chat ID of your testing group
test_chat_id = '-123456789'

# Chat ID of your main group
mains_chat_id = '-123456789'
true_chat_id = '-123456789'

# Whether runnning as dev or not
is_dev = True
# Choose which Text to Speech Engine to use.
# Available:
# [gTTS] Google TTS
# [festival] Festival TTS- Requires Festival TTS installed.
tts_engine = "gTTS"
# tts_engine = "festival"
```

* Run with `python3 bot_chaddi.py`.
* Can be deployed on any EC2-like VPS. Run with `./run_prod.sh`.
