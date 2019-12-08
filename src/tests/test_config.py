import pytest
import config

def test_config():
    assert config.bot_username
    assert config.tg_bot_token
    assert config.allowed_setters
