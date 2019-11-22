<h1 align="center">Chaddi Bot</h1>
<div align="center">
<em>A tailor made (and mediocre) Telegram Bot written in Python 3.</em> 
<br> <br>
<img src="https://circleci.com/gh/arkits/chaddi-tg/tree/master.svg?style=svg"></img>
</div>

## Features

ChaddiBot has a variety of features to make your Telegram experience a whole lot more fun! Some of them are -

- WebM Converter
- `/tts` performs Text-To-Speech with an english voice.
- `/ghati` performs Text-To-Speech with a hindi voice.
- `/superpower` is a countown to 1st January when India will become a superpower.
- `/jyotish` tries to solve your problems of life and fails everytime.
- `/mom` insults your mom.
- `/quotes` fetches a random quote
- `/hi` performs an unenthusiastic greeting
- `/rokda` displays your message count in the chat as a currency.
- `/gamble` lets you win or lose some of your internet points.
- `/chutiya` calls someone a chutiya
- `/birthday` announces birthdays today
- `/choose` makes a random selection if you're confused about two or more things.

## Setup and Deployment

### Setup your Telegram Bot
* Create your bot with [@BotFather](https://telegram.me/botfather).   
    * Refer to Telegram's [documentation](https://core.telegram.org/bots#3-how-do-i-create-a-bot) for more help on creating bots.
    * Important settings in @BotFather -
        * Enable `Allow Groups`.
        * Disbale `Privacy Mode`.

### Setup chaddi-tg code
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
* Create `src/config.py` based on `src/config.py.sample`

### Running 

* Run locally with `python bot_chaddi.py`.
* Run in prod with `./run_prod.sh`.

### Additional Setup for Special Handlers

#### `/mom` handler

The `/mom` handler uses spaCy library. It needs to be installed with the English language model.

```bash 
python -m spacy download en_core_web_sm
```

#### WebM converter

WebM files are converted into mp4 by `src/handlers/webm_converter.py` using ffmpeg. Make sure to install that. 

#### Webhook Conectivity

[Refer to python-telegram-bot's official documentation](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks)

To check if your setup is correct, do a GET at ` https://api.telegram.org/bot{my_bot_token}/getWebhookInfo `.


