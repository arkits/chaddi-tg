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

### Requirments

- Python 3.9
- PostgreSQL
- ffmpeg

### Running

**With Docker**

```bash
$ docker-compose build chaddi-tg
$ docker-compose up chaddi-tg
```

**With Local Python**

```bash
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirments.txt
$ ./run.sh
```

### Troubleshooting

**Cryptography**

If you get any errors related to `cryptography`, please refer to - https://cryptography.io/en/latest/installation.html

**Spacy**

To download the latest Spacy language model -

```bash
python -m spacy download en_core_web_sm
```
