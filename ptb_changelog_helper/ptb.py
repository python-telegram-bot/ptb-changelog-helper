"""This module contains functionality for automatically updating the changelog and version
in the configured PTB repository.
"""

import re
from pathlib import Path

from ptb_changelog_helper.version import Version


def update_version(ptb_dir: Path, new_version: Version) -> None:
    """Updates the version in the PTB repository.

    Args:
        ptb_dir (:obj:`Path`): The path to the PTB repository.
        new_version (:class:`Version`): The new version.
    """
    version_file = ptb_dir / "telegram" / "_version.py"
    text = version_file.read_text(encoding="utf-8")
    # replacing the quotes for black
    version_string = repr(new_version).replace("'", '"')
    text = re.sub(
        pattern=r"__version_info__ = .+\)\n",
        repl=f"__version_info__ = {version_string}\n",
        string=text,
    )
    version_file.write_text(text, encoding="utf-8")


def update_changelog(ptb_dir: Path, changelog: str) -> None:
    """Updates the changelog in the PTB repository.

    Args:
        ptb_dir (:obj:`Path`): The path to the PTB repository.
        changelog (:obj:`str`): The changelog to insert.
    """
    changelog_file = ptb_dir / "CHANGES.rst"
    text = changelog_file.read_text(encoding="utf-8")
    text = re.sub(
        pattern="Changelog\n=========",
        repl=f"Changelog\n=========\n\n{changelog}",
        string=text,
    )
    changelog_file.write_text(text, encoding="utf-8")
