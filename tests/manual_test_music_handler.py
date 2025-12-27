import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.bot.handlers import music


async def test_music_handler():
    print("Starting music handler test...")

    # Mock Update and Context
    update = MagicMock()
    context = MagicMock()

    # Test Case 1: Spotify Link
    print("\nTest Case 1: Spotify Link")
    update.message.text = (
        "Check this out: https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
    )
    update.message.reply_text = AsyncMock()

    await music.handle(update, context)

    if update.message.reply_text.called:
        args, kwargs = update.message.reply_text.call_args
        print(f"SUCCESS: Replied with: {args[0]}")
    else:
        print("FAILURE: Did not reply")

    # Test Case 2: Apple Music Link
    print("\nTest Case 2: Apple Music Link")
    update.message.text = "https://music.apple.com/us/album/never-gonna-give-you-up/1558533900?i=1558534271"
    update.message.reply_text = AsyncMock()

    await music.handle(update, context)

    if update.message.reply_text.called:
        args, kwargs = update.message.reply_text.call_args
        print(f"SUCCESS: Replied with: {args[0]}")
    else:
        print("FAILURE: Did not reply")

    # Test Case 3: No Link
    print("\nTest Case 3: No Link")
    update.message.text = "Just a normal message"
    update.message.reply_text = AsyncMock()

    await music.handle(update, context)

    if update.message.reply_text.called:
        print("FAILURE: Replied when it shouldn't have")
    else:
        print("SUCCESS: Did not reply")


if __name__ == "__main__":
    asyncio.run(test_music_handler())
