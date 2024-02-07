"""This module is an example of how to use ptb_changelog_helper as a library.

Please fill in your credentials below before running this script.
"""

import asyncio
import logging
from pathlib import Path

from ptb_changelog_helper.main import main
from ptb_changelog_helper.version import Version

logging.basicConfig(level=logging.INFO)
logging.getLogger("gql").setLevel(logging.WARNING)

if __name__ == "__main__":
    asyncio.run(
        main(
            new_version=Version(3, 0, 0, "final", 0),
            github_token="Bearer ghp_abcdefg",
            bot_token="12456:token",
            telegram_chat_id=11880,
            ptb_dir=Path(r"C:\Users\user\PycharmProjects\python-telegram-bot"),
        )
    )
