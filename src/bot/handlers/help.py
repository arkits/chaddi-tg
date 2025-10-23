from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.domain import dc


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dc.log_command_usage("help", update)
    await update.message.reply_text(
        text="""
<b>Welcome to ChaddiBot!</b>
- Utils
  - WebM to MP4 Converter
  - <code>/translate</code> - translates any message into English
- Economy
  - Take part in Chaddi's internal economy with ₹okda
  - <code>/rokda</code> - tells you how much ₹okda you have
  - <code>/daan</code> - give ₹okda to someone-else in need
  - <code>/gamble</code> - try your luck at the Chaddi Casino!
- Fun and Games
  - <code>/roll</code> - starts a dice roll game
  - <code>/quotes</code> - showcase the important messages in your Group
  - <code>/remind 5m "Chai break"</code> - Chaddi will remind you to take a break

Support group: https://t.me/chaddi_b
""",
        parse_mode=ParseMode.HTML,
    )
