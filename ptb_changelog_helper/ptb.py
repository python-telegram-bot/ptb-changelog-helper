"""This module contains functionality for automatically updating the changelog and version
in the configured PTB repository.
"""

import logging
import re
from pathlib import Path

from ptb_changelog_helper.version import VERSION_PATTERN, Version

_LOGGER = logging.getLogger(__name__)


def update_version(ptb_dir: Path, new_version: Version) -> None:
    """Updates the version in the PTB repository.

    Args:
        ptb_dir (:obj:`Path`): The path to the PTB repository.
        new_version (:class:`Version`): The new version.
    """
    _LOGGER.info("Updating version in PTB repository.")
    version_file = ptb_dir / "telegram" / "_version.py"
    text = version_file.read_text(encoding="utf-8")
    # replacing the quotes for black

    def replace_version(match: re.Match[str]) -> str:
        def format_value(val: str | int) -> str:
            if isinstance(val, str):
                return f'"{val}"'
            return str(val)

        print(match.groupdict())
        full_match = match.group(0)
        for key, value in match.groupdict().items():
            print(key, value, getattr(new_version, key))
            if key not in new_version._fields:
                continue
            full_match = full_match.replace(
                f"{key}={value}", f"{key}={format_value(getattr(new_version, key))}"
            )

        return full_match

    # print(text)
    # print("=====")
    # print(VERSION_PATTERN)
    # print("=====")
    print(re.findall(VERSION_PATTERN, text))
    text = re.sub(
        pattern=VERSION_PATTERN,
        repl=replace_version,
        string=text,
    )
    version_file.write_text(text, encoding="utf-8")


def update_changelog(ptb_dir: Path, changelog: str) -> None:
    """Updates the changelog in the PTB repository.

    Args:
        ptb_dir (:obj:`Path`): The path to the PTB repository.
        changelog (:obj:`str`): The changelog to insert.
    """
    _LOGGER.info("Updating changelog in PTB repository.")
    changelog_file = ptb_dir / "CHANGES.rst"
    text = changelog_file.read_text(encoding="utf-8")
    text = re.sub(
        pattern="Changelog\n=========",
        repl=f"Changelog\n=========\n\n{changelog}",
        string=text,
    )
    changelog_file.write_text(text, encoding="utf-8")


def insert_next_version(ptb_dir: Path, next_version: Version) -> None:
    """Replaces "NEXT.VERSION" with the new version in the docs of the PTB repository.

    Args:
        ptb_dir (:obj:`Path`): The path to the PTB repository.
        next_version (:class:`Version`): The new version.
    """
    _LOGGER.info("Replacing 'NEXT.VERSION' in PTB repository.")

    forbidden_dirs = {"venv", ".github"}

    for extension in ("py", "rst", "md"):
        for file in ptb_dir.rglob(f"*.{extension}"):
            if any(any(f_dir in part for part in file.parts) for f_dir in forbidden_dirs):
                continue
            if file.name == "CONTRIBUTING.rst":
                continue

            text = file.read_text(encoding="utf-8")
            text = text.replace("NEXT.VERSION", str(next_version))
            file.write_text(text, encoding="utf-8")
