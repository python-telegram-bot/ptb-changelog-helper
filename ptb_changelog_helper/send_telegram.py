"""This module contains functionality for sending a HTML message to a Telegram chat."""
import logging
from pathlib import Path

from telegram import Bot, Message, constants

_LOGGER = logging.getLogger(__name__)


async def publish_release_notes(
    chat_id: int | str, bot_token: str, changelog_path: Path
) -> Message:
    """Publishes the release notes to the given Telegram chat.

    Args:
        chat_id (:obj:`int` | :obj:`str`): The ID of the chat to publish the release notes to.
        bot_token (:obj:`str`): The bot token to use for publishing.
        changelog_path (:obj:`Path`): The path to the HTML changelog file.
    """
    async with Bot(token=bot_token) as bot:
        _LOGGER.info("Publishing release notes to Telegram chat %s.", chat_id)
        return await bot.send_message(
            chat_id=chat_id,
            text=changelog_path.read_text(encoding="utf-8"),
            parse_mode=constants.ParseMode.HTML,
            disable_web_page_preview=True,
        )
