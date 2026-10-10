from datetime import UTC, datetime
from unittest.mock import MagicMock

from telegram import Chat, Message, MessageEntity, Update, User

from src.bot import command_handler


async def noop(update, context):
    pass


def make_message(text: str) -> Message:
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=-100, type="supergroup", title="Test"),
        from_user=User(id=1, first_name="Test", is_bot=False),
        text=text,
        entities=[MessageEntity(type=MessageEntity.BOT_COMMAND, offset=0, length=5)],
    )
    bot = MagicMock()
    bot.username = "ChaddiBot"
    message.set_bot(bot)
    return message


def test_handles_new_commands():
    handler = command_handler("daan", noop)
    update = Update(update_id=1, message=make_message("/daan 25"))

    assert handler.check_update(update)


def test_ignores_edited_commands():
    # Editing an old /daan used to run the donation again
    handler = command_handler("daan", noop)
    update = Update(update_id=1, edited_message=make_message("/daan 25"))

    assert not handler.check_update(update)
