# chaddi-tg

This is a Telegram bot written in Python.

## Dev environment setup

- This project uses `uv` for Python related commands
- Run `uv run ruff check` to check for lint issues
- Run `uv run ruff format` to format your code
- Run `uv run pytest` to run all tests
- Run `make test-cov` to run all tests with coverage
- The application can be run from `./run.sh` -- HOWEVER DO NOT run it yourself! Always ask me to run the application.

## Development workflow

- Upon completion of your task, you MUST run commands to lint, format and test.
  - `make lint`
  - `make format`
  - `make test-cov`
- You MUST ensure that there are no lint issues and that all tests pass.
