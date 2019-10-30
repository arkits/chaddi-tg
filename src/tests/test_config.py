import pytest
import config

def test_config():
    assert config.bot_username
    assert config.tg_bot_token
    assert config.is_dev is not None

    if config.is_dev is False:
        assert config.tg_webhook_url 

    assert config.allowed_setters
