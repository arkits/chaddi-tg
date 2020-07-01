<h1 align="center">Chaddi Bot</h1>
<div align="center">
<em>A tailor made (and mediocre) Telegram Bot written in Python 3.</em> <br>
<br> <br>
<img src="https://circleci.com/gh/arkits/chaddi-tg/tree/master.svg?style=svg"></img>
</div>

# Features

ChaddiBot has a variety of features to make your Telegram experience a whole lot more fun! Some of them are -

- WebM to MP4 Converter
- `/mom` insults your mom.
- `/quotes` fetches a random quote
- `/rokda` displays your message count in the chat as a currency.
- `/gamble` lets you win or lose some of your internet points.
- `/choose` makes a random selection if you're confused about two or more things.

## Requirements and Dependencies

- A node to run Chaddi 24*7
  - Your node needs to be publicly accessible over the internet if you want to setup Webhook Connectivity.
- Python 3
- ffmpeg (For WebM Conversion)

## Setup and Deployment

### Docker deployment

Copy `env-example` to `.env` and change all values. Then you may run:

```bash
$ docker-compose -p <project-name> up -d --build
```

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
* Create a `config.json` based on `sample_config.json` in `src/resources`.

### Running 

* Run locally with `python chaddi_bot.py`.
* Run in prod with `./scripts/run_prod.sh`.

### Additional Setup for Special Handlers

#### WebM converter

WebM files are converted into mp4 by `src/handlers/webm_converter.py` using ffmpeg. Make sure to install that. 

#### Webhook Connectivity

[Refer to python-telegram-bot's official documentation](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks)

To check if your setup is correct, do a GET at ` https://api.telegram.org/bot{my_bot_token}/getWebhookInfo `.
