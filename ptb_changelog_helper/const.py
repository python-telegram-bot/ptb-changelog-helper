"""Constants for ptb_changelog_helper."""

import re
from typing import Final

GITHUB_ORGANIZATION: Final[str] = "python-telegram-bot"
"""The GitHub organization to use."""
REPOSITORY_NAME: Final[str] = "python-telegram-bot"
"""The repository name to use."""
USER_AGENT: Final[str] = "Github: python-telegram-bot/ptb-changelog-helper"
"""The user agent to use for the GitHub API requests."""
GITHUB_THREAD_PATTERN: Final[re.Pattern] = re.compile(pattern=r"(\#(\d+))")
"""The pattern to use for finding GitHub threads in changelog entries."""
PANDOC_METADATA_KEY: Final[str] = "ptb-thread-storage-file"
"""The key to use for storing the thread storage file in the Pandoc metadata."""
