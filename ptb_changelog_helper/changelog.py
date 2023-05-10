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
    MAJOR: str = "Major Changes"
    MINOR: str = "Minor Changes"
    NEW_FEATURES: str = "New Features"
    BUG_FIXES: str = "Bug Fixes"
    DOCUMENTATION: str = "Documentation Improvements"
    INTERNAL: str = "Internal Changes"
    DEPENDENCIES: str = "Dependency Updates"


class ChangeBlock:
    def __init__(self, title: str):
        self.title = title
        self.changes: list[str] = []

    def add_change(self, change: str) -> None:
        self.changes.append(change)

    def to_md(self) -> str:
        return f"## {self.title}\n" + "\n".join(f"- {change}" for change in self.changes)


class Changelog:
    def __init__(self, version: Version, date: datetime.date | None = None) -> None:
        self.version: Version = version
        self.date = date or datetime.date.today()
        self.change_blocks: dict[ChangeCategory, ChangeBlock] = {
            category: ChangeBlock(category) for category in ChangeCategory
        }

    def add_change(self, category: ChangeCategory, change: str) -> None:
        self.change_blocks[category].add_change(change)

    def to_md(self) -> str:
        header = f"# Version {self.version}\n*Released {self.date.isoformat()}\n\n"
        header += (
            f"This is the technical changelog for version {self.version}. More elaborate "
            f"release notes can be found in the news channel [@pythontelegrambotchannel]("
            f"https://t.me/pythontelegrambotchannel)."
        )
        changes = "\n\n".join(block.to_md() for block in self.change_blocks.values())
        return header + "\n\n" + changes
