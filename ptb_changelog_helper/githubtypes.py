"""This module contains the classes that represent types from the GitHub GraphQL API."""

from collections.abc import Collection
from typing import Any
from warnings import warn

import pydantic


class BaseModel(pydantic.BaseModel):
    """Convenience class that makes all models immutable and hashable by default."""

    class Config:
        """Configuration for the base model."""

        frozen = True


class PageInfo(BaseModel):
    """This class represents the page info of a connection.

    Attributes:
        endCursor (:obj:`str` | :obj:`None`): The cursor of the last node in the connection.
            Can be used to fetch the next page, if there is one.
        hasNextPage (:obj:`bool`): Whether there are more nodes available.
    """

    endCursor: str | None
    hasNextPage: bool


class _Connection(BaseModel):
    """This class represents a generic connection in the GitHub GraphQL API, i.e. something that
    contains a list of nodes and page info.

    This is not part of the public API.
    """

    pageInfo: PageInfo
    nodes: tuple[BaseModel, ...] | None


def _issue_pagination_warning(
    source_description: str, node_description: str, connection: _Connection | None
) -> None:
    """Issue a warning if the connection has more nodes available than were returned."""
    if connection and connection.pageInfo.hasNextPage:
        warn(
            f"{source_description} has more {node_description} available. Retrieved only the "
            f"first {len(connection.nodes or [])}.",
            stacklevel=3,
        )


class Label(BaseModel):
    """This class represents a label on a GitHub thread..

    Attributes:
        name (:obj:`str`): The name of the label.
        description (:obj:`str` | :obj:`None`): The description of the label, if any.
    """

    name: str
    description: str | None


class LabelConnection(_Connection):
    """This class represents a connection of labels on a GitHub thread.

    Attributes:
        nodes (:obj:`tuple` [:class:`Label`, ...] | :obj:`None`): The labels in the connection.
        pageInfo (:class:`PageInfo`): The page info of the connection.
    """

    nodes: tuple[Label, ...] | None


class User(BaseModel):
    """This class represents a GitHub user.

    Attributes:
        login (:obj:`str`): The login of the user.
        url (:obj:`str`): The URL of the user's profile.
    """

    login: str
    url: str

    def as_md(self) -> str:
        """Returns the user as markdown."""
        return f"[@{self.login}]({self.url})"

    def __hash__(self) -> int:
        """We do this to ensure that authors are treated as users for the purposes of hashing,
        especially for checking whether a author is in a collection of users."""
        return hash((self.login, self.url))

    def __eq__(self, other: object) -> bool:
        """We do this to ensure that authors are treated as users for the purposes of hashing,
        especially for checking whether a author is in a collection of users."""
        if isinstance(other, User):
            return self.login == other.login
        return NotImplemented


DEPENDABOT_USER = User(login="dependabot", url="https://github.com/apps/dependabot")
"""The user that Dependabot uses to open pull requests."""
PRE_COMMIT_CI_USER = User(login="pre-commit-ci", url="https://github.com/apps/pre-commit-ci")
"""The user that pre-commit.ci uses to open pull requests."""


class Author(User):
    """This class represents the author of a GitHub thread.
    Basically an alias for :class:`User`.
    """

    def as_md(self) -> str:
        """Return a Markdown representation of the issue."""
        return self.login

    def as_html(self) -> str:
        """Return a HTML representation of the issue."""
        return f'<a href="{self.url}">{self.login}</a>'

    def as_rst(self) -> str:
        """Return a reStructuredText representation of the issue."""
        return f"`{self.login} <{self.url}>`_"


class Issue(BaseModel):
    """This class represents a GitHub issue.

    Attributes:
        number (:obj:`int`): The number of the issue.
        url (:obj:`str`): The URL of the issue.
        labels (:class:`LabelConnection` | :obj:`None`): The labels of the issue.
        author (:class:`Author`): The author of the issue.
    """

    number: int
    url: str
    labels: LabelConnection | None
    author: Author

    def __init__(self, **data: dict[str, Any]) -> None:
        super().__init__(**data)
        _issue_pagination_warning(f"Issue {self.number}", "labels", self.labels)

    def as_md(self) -> str:
        """Return a Markdown representation of the issue."""
        return f"{self.number}"

    def as_html(self) -> str:
        """Return a HTML representation of the issue."""
        return f'<a href="{self.url}">#{self.number}</a>'

    def as_rst(self) -> str:
        """Return a reStructuredText representation of the issue."""
        return f":issue:`{self.number}`"


class ClosingIssuesReferences(_Connection):
    """This class represents the closing issues references of a GitHub pull request.

    Attributes:
        nodes (:obj:`tuple` [:class:`Issue`, ...] | :obj:`None`): The closing issues references
            of the pull request.
        pageInfo (:class:`PageInfo`): The page info of the connection.
    """

    nodes: tuple[Issue, ...] | None


class PullRequest(BaseModel):
    """This class represents a GitHub pull request.

    Attributes:
        number (:obj:`int`): The number of the pull request.
        url (:obj:`str`): The URL of the pull request.
        author (:class:`Author`): The author of the pull request.
        closingIssuesReferences (:class:`ClosingIssuesReferences` | :obj:`None`): The closing
            issues references of the pull request.
        labels (:class:`LabelConnection` | :obj:`None`): The labels of the pull request.
    """

    number: int
    url: str
    author: Author
    closingIssuesReferences: ClosingIssuesReferences | None
    labels: LabelConnection | None

    def __init__(self, **data: dict[str, Any]) -> None:
        super().__init__(**data)
        _issue_pagination_warning(
            f"PullRequest {self.number} {self.number}", "labels", self.labels
        )
        _issue_pagination_warning(
            f"PullRequest {self.number}", "closing issues", self.closingIssuesReferences
        )

    def as_md(self, exclude_users: Collection[User] = ()) -> str:
        """Return a Markdown representation of the pull request.

        This includes the author - unless excluded - and the closing issues references.

        Args:
            exclude_users (Collection[:class:`User`]): A collection of users to exclude from the
                Markdown representation. The users :attr:`DEPENDABOT_USER` and
                :attr:`PRE_COMMIT_CI_USER` are always excluded.
        """
        exclude_users = set(exclude_users)
        exclude_users.update({DEPENDABOT_USER, PRE_COMMIT_CI_USER})

        md_str = f"#{self.number}"

        if self.author not in exclude_users:
            md_str += f" by {self.author.as_md()}"

        if self.closingIssuesReferences and self.closingIssuesReferences.nodes:
            nodes = self.closingIssuesReferences.nodes
            md_str += " closes "
            if len(nodes) == 1:
                md_str += nodes[0].as_md()
            else:
                md_str += f"{', '.join(node.as_md() for node in nodes[:-1])} "
                md_str += f"and {nodes[-1].as_md()}"

        return md_str

    def as_html(self, exclude_users: Collection[User] = ()) -> str:
        """
        Return a HTML representation of the pull request.

        This includes the author - unless excluded - and the closing issues references.

        Args:
            exclude_users (Collection[:class:`User`]): A collection of users to exclude from the
                HTML representation. The users :attr:`DEPENDABOT_USER` and
                :attr:`PRE_COMMIT_CI_USER` are always excluded.
        """
        exclude_users = set(exclude_users)
        exclude_users.update({DEPENDABOT_USER, PRE_COMMIT_CI_USER})

        html_str = f'<a href="{self.url}">#{self.number}</a>'

        if self.author not in exclude_users:
            html_str += f" by {self.author.as_html()}"

        if self.closingIssuesReferences and self.closingIssuesReferences.nodes:
            nodes = self.closingIssuesReferences.nodes
            html_str += " closes "
            if len(nodes) == 1:
                html_str += nodes[0].as_html()
            else:
                html_str += f"{', '.join(node.as_html() for node in nodes[:-1])} "
                html_str += f"and {nodes[-1].as_html()}"

        return html_str

    def as_rst(self, exclude_users: Collection[User] = ()) -> str:
        """
        Return a reStructuredText representation of the pull request.

        This includes the author - unless excluded - and the closing issues references.

        Args:
            exclude_users (Collection[:class:`User`]): A collection of users to exclude from the
                reStructuredText representation. The users :attr:`DEPENDABOT_USER` and
                :attr:`PRE_COMMIT_CI_USER` are always excluded.
        """
        exclude_users = set(exclude_users)
        exclude_users.update({DEPENDABOT_USER, PRE_COMMIT_CI_USER})

        rst_str = f":pr:`{self.number}`"

        if self.author not in exclude_users:
            rst_str += f" by {self.author.as_rst()}"

        if self.closingIssuesReferences and self.closingIssuesReferences.nodes:
            nodes = self.closingIssuesReferences.nodes
            rst_str += " closes "
            if len(nodes) == 1:
                rst_str += nodes[0].as_rst()
            else:
                rst_str += f"{', '.join(node.as_rst() for node in nodes[:-1])} "
                rst_str += f"and {nodes[-1].as_rst()}"

        return rst_str

    def effective_labels(self) -> set[Label]:
        """Return the effective labels of the pull request, i.e. the labels of the pull request
        itself and the labels of the closing issues references.
        """
        labels = set()
        if self.labels and self.labels.nodes:
            labels.update(set(self.labels.nodes))

        if self.closingIssuesReferences and self.closingIssuesReferences.nodes:
            for issue in self.closingIssuesReferences.nodes:
                if issue.labels and issue.labels.nodes:
                    labels.update(set(issue.labels.nodes))

        return labels


class MembersWithRole(_Connection):
    """This class represents the members with role of a GitHub organization.

    Attributes:
        nodes (:obj:`tuple` [:class:`User`, ...] | :obj:`None`): The members with role of the
            organization.
        pageInfo (:class:`PageInfo`): The page info of the connection.
    """

    nodes: tuple[User, ...] | None


class Organization(BaseModel):
    """This class represents a GitHub organization.

    Attributes:
        membersWithRole (:class:`MembersWithRole` | :obj:`None`): The members
    """

    membersWithRole: MembersWithRole

    def __init__(self, **data: dict[str, Any]) -> None:
        super().__init__(**data)
        _issue_pagination_warning("PTB", "developers", self.membersWithRole)


class Tag(BaseModel):
    """This class represents a GitHub Git tag.

    Attributes:
        tagName (:obj:`str`): The name of the tag.
        createdAt (:obj:`str`): The creation date of the tag as an ISO 8601 string.
    """

    tagName: str
    createdAt: str


class Commit(BaseModel):
    """This class represents a GitHub Git commit.

    Attributes:
        messageHeadline (:obj:`str`): The headline of the commit message.
        messageBody (:obj:`str`): The body of the commit message.
    """

    messageHeadline: str
    messageBody: str

    def effective_text(self) -> str:
        """Return the effective text of the commit, i.e. combines the headline with the
        relevant part of the body, if the headline is truncated."""
        if self.messageHeadline.endswith("…"):
            return self.messageHeadline[:-1] + self.messageBody.split("\n")[0].strip("…")
        return self.messageHeadline


class CommitHistoryConnection(_Connection):
    """This class represents the commit history of a GitHub repository.

    Attributes:
        nodes (:obj:`tuple` [:class:`Commit`, ...] | :obj:`None`): The commits of the repository.
        pageInfo (:class:`PageInfo`): The page info of the connection.
    """

    nodes: tuple[Commit, ...] | None
