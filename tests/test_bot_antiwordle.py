from unittest.mock import MagicMock, patch

import pytest
from telegram import Message, Update
from telegram.ext import ContextTypes

from src.bot.handlers import antiwordle


class TestIsWordleResult:
    def test_is_wordle_result_valid_wordle(self):
        message = "Wordle 123/6\n\n⬛️⬛️⬛️⬛️⬛️\n🟨🟨⬛️⬛️⬛️\n🟩⬛️⬛️⬛️⬛️"
        result = antiwordle.is_wordle_result(message)
        assert result is True

    def test_is_wordle_result_none_message(self):
        result = antiwordle.is_wordle_result(None)
        assert result is False

    def test_is_wordle_result_empty_string(self):
        result = antiwordle.is_wordle_result("")
        assert result is False

    def test_is_wordle_result_no_wordle_prefix(self):
        message = "Not a wordle\n\n⬛️⬛️⬛️⬛️⬛️"
        result = antiwordle.is_wordle_result(message)
        assert result is False

    def test_is_wordle_result_no_slash_six(self):
        message = "Wordle 123\n\n⬛️⬛️⬛️⬛️⬛️"
        result = antiwordle.is_wordle_result(message)
        assert result is False

    def test_is_wordle_result_too_short_first_line(self):
        message = "Wordle 1/6\n\n⬛️⬛️⬛️⬛️⬛️"
        result = antiwordle.is_wordle_result(message)
        assert result is False

    def test_is_wordle_result_invalid_characters(self):
        message = "Wordle 123/6\n\n⬛️⬛️⬛️⬛️⬛️\nABCDE"
        result = antiwordle.is_wordle_result(message)
        assert result is False

    def test_is_wordle_result_valid_with_multiple_attempts(self):
        message = "Wordle 123/6\n\n⬛️⬛️⬛️⬛️⬛️\n🟨🟨⬛️⬛️⬛️\n🟩🟩🟩🟩🟩"
        result = antiwordle.is_wordle_result(message)
        assert result is True

    def test_is_wordle_result_exactly_three_lines(self):
        message = "Wordle 123/6\n\n⬛️⬛️⬛️⬛️⬛️"
        result = antiwordle.is_wordle_result(message)
        assert result is True


class TestRandomReply:
    @patch("src.bot.handlers.antiwordle.random.randint")
    def test_random_reply(self, mock_randint):
        mock_randint.return_value = 0
        result = antiwordle.random_reply()
        assert result == "KILL ALL WORDLE TARDS 🔫"

    @patch("src.bot.handlers.antiwordle.random.randint")
    def test_random_reply_different_index(self, mock_randint):
        mock_randint.return_value = 2
        result = antiwordle.random_reply()
        assert result == "BHHAAAAAAAAKKKKK TERA WORDLE BSDK"


class TestHandle:
    @pytest.mark.anyio
    async def test_handle_wordle_message(self):
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "Wordle 123/6\n\n⬛️⬛️⬛️⬛️⬛️\n🟩🟩🟩🟩🟩"
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        with (
            patch("src.bot.handlers.antiwordle.dc"),
            patch.object(antiwordle, "random_reply", return_value="test reply"),
        ):
            await antiwordle.handle(update, context)
            update.message.reply_text.assert_called_once_with("test reply")

    @pytest.mark.anyio
    async def test_handle_non_wordle_message(self):
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "Just a regular message"
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        with patch("src.bot.handlers.antiwordle.dc"):
            await antiwordle.handle(update, context)
            update.message.reply_text.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_with_delete_success(self):
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "Wordle 123/6\n\n⬛️⬛️⬛️⬛️⬛️\n🟩🟩🟩🟩🟩"
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        with (
            patch("src.bot.handlers.antiwordle.dc"),
            patch.object(antiwordle, "random_reply", return_value="test reply"),
        ):
            await antiwordle.handle(update, context)
            update.message.delete.assert_called_once()

    @pytest.mark.anyio
    async def test_handle_delete_failure(self):
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "Wordle 123/6\n\n⬛️⬛️⬛️⬛️⬛️\n🟩🟩🟩🟩🟩"
        update.message.delete = MagicMock(side_effect=Exception("Delete failed"))
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        with (
            patch("src.bot.handlers.antiwordle.dc"),
            patch("src.bot.handlers.antiwordle.logger"),
            patch.object(antiwordle, "random_reply", return_value="test reply"),
        ):
            await antiwordle.handle(update, context)
            update.message.reply_text.assert_called_once()

    @pytest.mark.anyio
    async def test_handle_with_log_to_dc_false(self):
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "Wordle 123/6\n\n⬛️⬛️⬛️⬛️⬛️\n🟩🟩🟩🟩🟩"
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        with patch("src.bot.handlers.antiwordle.dc") as mock_dc:
            await antiwordle.handle(update, context, log_to_dc=False)
            mock_dc.log_command_usage.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_exception(self):
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = None
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        with patch("src.bot.handlers.antiwordle.dc"), patch("src.bot.handlers.antiwordle.logger"):
            await antiwordle.handle(update, context)
