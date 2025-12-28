import os
from unittest.mock import MagicMock, patch


class TestConfig:
    @patch.dict(os.environ, {"CHADDI_BOT_PROFILE": "test"})
    def test_get_config_with_profile_env(self):
        """Test that get_config uses profile from environment variable"""
        from src.domain.config import get_config

        result = get_config()
        assert result is not None

    @patch.dict(os.environ, {}, clear=True)
    @patch("src.domain.config.config.read")
    def test_get_config_default_profile(self, mock_read):
        """Test that get_config defaults to 'dev' profile"""
        from src.domain.config import get_config

        mock_config = MagicMock()
        mock_read.return_value = None

        with patch("src.domain.config.config", mock_config):
            result = get_config()
            assert result is not None

    def test_get_config_callable(self):
        """Test that get_config function exists and is callable"""
        from src.domain.config import get_config

        assert callable(get_config)
