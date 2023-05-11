"""This module contains a class based changelog generator for Python Telegram Bot."""

import datetime
from enum import StrEnum
from typing import NamedTuple


class Version(NamedTuple):
    """This class is basically copied from PTB. We don't import it, because it's private and
    we want to rely only on the public API."""

    major: int
    minor: int
    micro: int
    releaselevel: str  # Literal['alpha', 'beta', 'candidate', 'final']
    serial: int

    def _rl_shorthand(self) -> str:
        return {
            "alpha": "a",
            "beta": "b",
            "candidate": "rc",
        }[self.releaselevel]

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}"
        if self.micro != 0:
            version = f"{version}.{self.micro}"
        if self.releaselevel != "final":
            version = f"{version}{self._rl_shorthand()}{self.serial}"

        return version


class ChangeCategory(StrEnum):
    """This enum contains the categories for changes."""

    MAJOR: str = "Major Changes"
    MINOR: str = "Minor Changes"
    NEW_FEATURES: str = "New Features"
    BUG_FIXES: str = "Bug Fixes"
    DOCUMENTATION: str = "Documentation Improvements"
    INTERNAL: str = "Internal Changes"
    DEPENDENCIES: str = "Dependency Updates"


class ChangeBlock:
    """This class represents a block of changes that is usually associated with a specific
    category.

    Args:
        title (:obj:`str`): The title of the change block.
    """

    def __init__(self, title: str):
        self.title = title
        self.changes: list[str] = []

    def add_change(self, change: str) -> None:
        """Adds a change to the change block.

        Args:
            change (:obj:`str`): The change to add.
        """
        self.changes.append(change)

    def to_md(self) -> str:
        """Returns the change block as markdown."""
        return f"## {self.title}\n" + "\n".join(f"- {change}" for change in self.changes)


class Changelog:
    """This class represents a changelog for a specific version.

    Args:
        version (:obj:`Version`): The version of the changelog.
        date (:obj:`datetime.date`, optional): The release date of the version. Defaults to today.
    """

    def __init__(self, version: Version, date: datetime.date | None = None) -> None:
        self.version: Version = version
        self.date = date or datetime.date.today()
        self.change_blocks: dict[ChangeCategory, ChangeBlock] = {
            category: ChangeBlock(category) for category in ChangeCategory
        }

    def add_change(self, category: ChangeCategory, change: str) -> None:
        """Adds a change to the changelog.

        Args:
            category (:obj:`ChangeCategory`): The category of the change.
            change (:obj:`str`): The change to add.

        """
        self.change_blocks[category].add_change(change)

    def to_md(self) -> str:
        """Returns the changelog as markdown."""
        header = f"# Version {self.version}\n*Released {self.date.isoformat()}\n\n"
        header += (
            f"This is the technical changelog for version {self.version}. More elaborate "
            f"release notes can be found in the news channel [@pythontelegrambotchannel]("
            f"https://t.me/pythontelegrambotchannel)."
        )
        changes = "\n\n".join(block.to_md() for block in self.change_blocks.values())
        return header + "\n\n" + changes
