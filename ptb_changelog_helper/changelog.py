"""This module contains a class based changelog generator for Python Telegram Bot."""

import asyncio
import datetime
import logging
from collections.abc import Collection, Iterable
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field

from ptb_changelog_helper.const import GITHUB_THREAD_PATTERN, MD_MONO_PATTERN
from ptb_changelog_helper.githubtypes import Commit, Issue, Label, PullRequest, User
from ptb_changelog_helper.graphqlclient import GraphQLClient
from ptb_changelog_helper.version import Version

_LOGGER = logging.getLogger(__name__)


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
                    _LOGGER.debug("Resolved category %s from label %s", category, label)
                    return category
        _LOGGER.debug(
            "Could not resolve category from labels %s. Returning %s.", label_names, cls.MAJOR
        )
        return cls.MAJOR


class Change(BaseModel):
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

    text: str
    pull_requests: Annotated[set[PullRequest], Field(default_factory=set, init=False)]
    thread_numbers: Annotated[set[int], Field(default_factory=set, init=False)]
    category: Annotated[ChangeCategory, Field(default=ChangeCategory.MAJOR, init=False)]
    effective_labels: Annotated[set[Label], Field(default_factory=set, init=False)]

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.thread_numbers: set[int] = {
            int(match.group(2)) for match in GITHUB_THREAD_PATTERN.finditer(self.text)
        }

    def update_from_pull_requests(
        self, github_threads: dict[int, PullRequest | Issue], ptb_devs: Collection[User]
    ) -> None:
        """Extracts the pull requests of the change and stores them to :attr:`pull_requests`.
        Also

            * updates the :attr:`text` with additional information as provided by
                :meth:`PullRequest.as_md`.
            * updates the :attr:`effective_labels` with the labels of the pull requests.
            * updates the :attr:`category` with the category of the pull requests as derived
                from the labels via :meth:`ChangeCategory.resolve_from_labels`.

        Args:
            github_threads (Dict[:obj:`int`: :class:`PullRequest` | :class:`Issue`]):
                A mapping of thread numbers to pull requests or issues.
            ptb_devs (:obj:`Collection` of :obj:`User`): The PTB developers. These will not be
                mentioned in the change.
        """
        self.pull_requests = {
            thread
            for thread_number in self.thread_numbers
            if isinstance(thread := github_threads[thread_number], PullRequest)
        }

        for pull_request in self.pull_requests:
            self.text = self.text.replace(
                f"#{pull_request.number}", pull_request.as_md(exclude_users=ptb_devs)
            )

        self.effective_labels.update(
            *(pull_request.effective_labels() for pull_request in self.pull_requests)
        )
        self.category = ChangeCategory.resolve_from_labels(self.effective_labels)

    def as_md(self) -> str:
        """Returns the change as markdown including information about the associated pull requests
        and issues."""
        return f"{self.text} ({', '.join(pr.as_md() for pr in self.pull_requests)})"

    def as_html(self) -> str:
        """Returns the change as HTML including information about the associated pull requests
        and issues."""
        text = MD_MONO_PATTERN.sub(r"<code>\1</code>", self.text)
        return f"{text} ({', '.join(pr.as_html() for pr in self.pull_requests)})"

    def as_rst(self) -> str:
        """Returns the change as reStructuredText including information about the associated pull
        requests and issues."""
        text = MD_MONO_PATTERN.sub(r"``\1``", self.text)
        return f"{text} ({', '.join(pr.as_rst() for pr in self.pull_requests)})"


class ChangeBlock(BaseModel):
    """This class represents a block of changes that is usually associated with a specific
    category.

    Args:
        title (:obj:`str`): The title of the change block.
    """

    title: str
    changes: Annotated[list[Change], Field(default_factory=list, init=False)]

    def add_change(self, change: Change) -> None:
        """Adds a change to the change block.

        Args:
            change (:class:`Change`): The change to add.
        """
        self.changes.append(change)

    def has_changes(self) -> bool:
        """Returns whether the change block has changes."""
        return bool(self.changes)

    def as_md(self) -> str:
        """Returns the change block as markdown."""
        return f"## {self.title}\n" + "\n".join(f"- {change.as_md()}" for change in self.changes)

    def as_html(self) -> str:
        """Returns the change block as HTML."""
        return f"<b>{self.title}</b>\n" + "\n".join(
            f"• {change.as_html()}" for change in self.changes
        )

    def as_rst(self) -> str:
        """Returns the change block as reStructuredText."""
        return f"{self.title}\n\n" + "\n".join(f"  - {change.as_rst()}" for change in self.changes)


class Changelog(BaseModel):
    """This class represents a changelog for a specific version.

    Args:
        version (:obj:`Version`): The version of the changelog.
        date (:obj:`datetime.date`, optional): The release date of the version. Defaults to today.

    Attributes:
        changes (:obj:`list` of :class:`Change`, optional): The changes of the version.
        change_blocks (Dict[:obj:`ChangeCategory`: :class:`ChangeBlock`]): The change blocks of
            the changelog. Will be set by :meth:`update_changes_from_pull_requests`.
    """

    version: Version
    date: Annotated[datetime.date, Field(default_factory=datetime.date.today)]
    changes: Annotated[list[Change], Field(default_factory=list, init=False)]
    change_blocks: Annotated[
        dict[ChangeCategory, ChangeBlock],
        Field(
            default_factory=lambda: {
                category: ChangeBlock(title=category) for category in ChangeCategory
            },
            init=False,
        ),
    ]

    def add_change(self, change: Change) -> None:
        """Adds a change to the backlog.

        Args:
            change (:class:`Change`): The change to add.

        """
        self.changes.append(change)

    def add_changes(self, changes: Iterable[Change]) -> None:
        """Adds multiple changes to the backlog.

        Args:
            changes (Iterable[:class:`Change`]): The changes to add.
        """
        self.changes.extend(changes)

    def add_changes_from_commits(self, commits: Iterable[Commit]) -> None:
        """Adds multiple changes from commits to the backlog.

        Args:
            commits (Iterable[:class:`Commit]): The commits to add as changes.
        """
        self.add_changes(Change(text=commit.effective_text()) for commit in commits)

    def get_all_thread_numbers(self) -> set[int]:
        """Returns all thread numbers of the changes in the changelog."""
        return set().union(*(change.thread_numbers for change in self.changes))

    def update_changes_from_pull_requests(
        self, github_threads: dict[int, PullRequest | Issue], ptb_devs: Collection[User]
    ) -> None:
        """Calls :meth:`Change.update_from_pull_requests` for all changes.
        Additionally, it updates :attr:`change_blocks` with the changes.

        Args:
            github_threads (Dict[:obj:`int`: :class:`PullRequest` | :class:`Issue`]):
                A mapping of thread numbers to pull requests or issues.
            ptb_devs (:obj:`Collection` of :obj:`User`): The PTB developers. These will not be
                mentioned in the changes.
        """
        for change in self.changes:
            change.update_from_pull_requests(github_threads, ptb_devs)
            self.change_blocks[change.category].add_change(change)

    @property
    def _sorted_blocks(self) -> Iterable[ChangeBlock]:
        for block in ChangeCategory:
            if block in self.change_blocks:
                yield self.change_blocks[block]

    def as_md(
        self,
    ) -> str:
        """Returns the changelog as markdown."""
        header = (
            f"# Version {self.version}\n*Released {self.date.isoformat()}*\n\n"
            f"This is the technical changelog for version {self.version}. More elaborate "
            f"release notes can be found in the news channel [@pythontelegrambotchannel]("
            f"https://t.me/pythontelegrambotchannel)."
        )

        changes = "\n\n".join(
            block.as_md() for block in self._sorted_blocks if block.has_changes()
        )
        return f"{header}\n\n{changes}"

    def as_html(self) -> str:
        """Returns the changelog as HTML."""
        header = (
            f"<b>We've just released v{self.version}.</b>\n\n"
            "Thank you to everyone who contributed to this release.\n\n"
            "As usual, upgrade using <code>pip install -U python-telegram-bot</code>."
        )
        changes = "\n\n".join(
            block.as_html() for block in self._sorted_blocks if block.has_changes()
        )
        return f"{header}\n\n{changes}"

    def as_rst(self) -> str:
        """Returns the changelog as reStructuredText."""
        title = f"Version {self.version}"
        header = (
            f"{title}\n{'=' * len(title)}\n\n"
            f"Released {self.date.isoformat()}\n\n"
            "This is the technical changelog for version {self.version}. More elaborate "
            "release notes can be found in the news channel `@pythontelegrambotchannel "
            "<https://t.me/pythontelegrambotchannel>`_."
        )
        changes = "\n\n".join(
            block.as_rst() for block in self._sorted_blocks if block.has_changes()
        )
        return f"{header}\n\n{changes}"

    @classmethod
    async def build_for_version(
        cls, version: Version, graphql_client: GraphQLClient
    ) -> "Changelog":
        """Builds a changelog for a specific version.

        Args:
            version (:class:`Version`): The version of the changelog.
            graphql_client (:class:`GraphQLClient`): The GraphQL client to use for fetching the
                data from GitHub.
        """
        changelog = cls(version=version)  # type: ignore[call-arg]

        _LOGGER.info("Fetching commits since last release.")
        commits = await graphql_client.get_commits_since_last_release()
        _LOGGER.info("Found %d commits.", len(commits))
        changelog.add_changes_from_commits(commits)

        thread_numbers = changelog.get_all_thread_numbers()

        _LOGGER.info("Fetching pull requests, issues and ptb devs.")
        threads, ptb_devs = await asyncio.gather(
            graphql_client.get_threads(thread_numbers), graphql_client.get_ptb_devs()
        )
        _LOGGER.info("Found %d pull requests and issues.", len(threads))
        _LOGGER.info("Found the following PTB devs: %s.", ptb_devs)

        _LOGGER.info("Inserting fetched information into changelog.")
        changelog.update_changes_from_pull_requests(threads, ptb_devs)

        return changelog
