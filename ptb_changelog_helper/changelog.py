"""This module contains a class based changelog generator for Python Telegram Bot."""

import datetime
from collections.abc import Collection
from enum import StrEnum
from typing import NamedTuple

from ptb_changelog_helper.const import GITHUB_THREAD_PATTERN
from ptb_changelog_helper.githubtypes import Issue, Label, PullRequest, User


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

    @classmethod
    def resolve_from_labels(cls, labels: Collection[Label]) -> "ChangeCategory":
        """Given a set of labels, return the category that best matches the labels.

        Args:
            labels (:obj:`Collection` of :obj:`Label`): The labels to resolve.
        """
        mapping = {
            "bug :bug:": cls.BUG_FIXES,
            "enhancement": cls.NEW_FEATURES,
            "API": cls.MAJOR,
            "documentation": cls.DOCUMENTATION,
            "tests": cls.INTERNAL,
            "security :lock:": cls.BUG_FIXES,
            "examples": cls.DOCUMENTATION,
            "type hinting": cls.MINOR,
            "refactor :gear:": cls.INTERNAL,
            "breaking :boom:": cls.MAJOR,
            "dependencies": cls.DEPENDENCIES,
            "github_actions": cls.INTERNAL,
            "code quality ✨": cls.INTERNAL,
        }
        label_names = {label.name for label in labels}
        for source_label, category in mapping.items():
            for label in label_names:
                if source_label == label:
                    return category
        return cls.MAJOR


class Change:
    """This class represents a single change.

    Args:
        text (:obj:`str`): The text of the change.

    Attributes:
        text (:obj:`str`): The text of the change.
        thread_numbers (Set[:obj:`int`]): The thread numbers of the change.
        category (:obj:`ChangeCategory`, optional): The category of the change. Defaults to
            :attr:`ChangeCategory.MAJOR`. This is set by :meth:`update_from_pull_requests`.
        pull_requests (:obj:`set` of :obj:`PullRequest`, optional): The pull requests associated
            with the change. This is set by :meth:`update_from_pull_requests`.
        effective_labels (:obj:`set` of :obj:`Label`, optional): The effective labels of the
            change. This is set by :meth:`update_from_pull_requests`.
    """

    def __init__(
        self,
        text: str,
    ):
        self.text: str = text
        self.thread_numbers: set[int] = set(GITHUB_THREAD_PATTERN.findall(self.text))
        self.category: ChangeCategory = ChangeCategory.MAJOR
        self.pull_requests: set[PullRequest] = set()
        self.effective_labels: set[Label] = set()

    def update_from_pull_requests(
        self, github_threads: dict[int, PullRequest | Issue], ptb_devs: Collection[User]
    ) -> None:
        """Fetches the pull requests of the change and stores them to :attr:`pull_requests`.
        Also

            * updates the :attr:`text` with additional information as provided by
                :meth:`PullRequest.as_markdown`.
            * updates the :attr:`effective_labels` with the labels of the pull requests.
            * updates the :attr:`category` with the category of the pull requests as derived
                from the labels via :meth:`ChangeCategory.resolve_from_labels`.

        Args:
            github_threads (Dict[:obj:`int`: :class:`PullRequest` | :class:`Issue`]):
                A mapping of thread numbers to pull requests or issues.
            ptb_devs (:obj:`Collection` of :obj:`User`): The PTB developers. These will not be
                mentioned in the change.
        """
        threads = set(GITHUB_THREAD_PATTERN.findall(self.text))
        self.pull_requests = {
            thread
            for thread_number in threads
            if isinstance(thread := github_threads[thread_number], PullRequest)
        }

        for pull_request in self.pull_requests:
            self.text.replace(
                f"#{pull_request.number}", pull_request.as_markdown(exclude_users=ptb_devs)
            )

        self.effective_labels.union(
            *(pull_request.effective_labels() for pull_request in self.pull_requests)
        )
        self.category = ChangeCategory.resolve_from_labels(self.effective_labels)

    def as_markdown(self) -> str:
        """Returns the change as markdown."""
        return self.text


class ChangeBlock:
    """This class represents a block of changes that is usually associated with a specific
    category.

    Args:
        title (:obj:`str`): The title of the change block.
    """

    def __init__(self, title: str):
        self.title = title
        self.changes: list[Change] = []

    def add_change(self, change: Change) -> None:
        """Adds a change to the change block.

        Args:
            change (:class:`Change`): The change to add.
        """
        self.changes.append(change)

    def as_markdown(self) -> str:
        """Returns the change block as markdown."""
        return f"## {self.title}\n" + "\n".join(
            f"- {change.as_markdown()}" for change in self.changes
        )


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

    def add_change(self, category: ChangeCategory, change: Change) -> None:
        """Adds a change to the changelog.

        Args:
            category (:obj:`ChangeCategory`): The category of the change.
            change (:class:`Change`): The change to add.

        """
        self.change_blocks[category].add_change(change)

    def as_markdown(
        self,
    ) -> str:
        """Returns the changelog as markdown."""
        header = f"# Version {self.version}\n*Released {self.date.isoformat()}\n\n"
        header += (
            f"This is the technical changelog for version {self.version}. More elaborate "
            f"release notes can be found in the news channel [@pythontelegrambotchannel]("
            f"https://t.me/pythontelegrambotchannel)."
        )
        changes = "\n\n".join(block.as_markdown() for block in self.change_blocks.values())
        return header + "\n\n" + changes
