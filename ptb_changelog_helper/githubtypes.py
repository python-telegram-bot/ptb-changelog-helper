from typing import Any
from warnings import warn

from pydantic import BaseModel


class PageInfo(BaseModel):
    endCursor: str | None
    hasNextPage: bool


class _Connection(BaseModel):
    pageInfo: PageInfo
    nodes: tuple[BaseModel, ...] | None


def _issue_pagination_warning(
    source_description: str, node_description: str, connection: _Connection | None
) -> None:
    if connection and connection.pageInfo.hasNextPage:
        warn(
            f"{source_description} has more {node_description} available. Retrieved only the "
            f"first {len(connection.nodes or [])}.",
            stacklevel=3,
        )


class Label(BaseModel):
    name: str
    description: str | None


class LabelConnection(_Connection):
    nodes: tuple[Label, ...] | None


class User(BaseModel):
    login: str
    url: str


class Author(User):
    pass


class Issue(BaseModel):
    number: int
    url: str
    labels: LabelConnection | None
    author: Author

    def __init__(self, **data: dict[str, Any]) -> None:
        super().__init__(**data)
        _issue_pagination_warning(f"Issue {self.number}", "labels", self.labels)


class ClosingIssuesReferences(_Connection):
    nodes: tuple[Issue, ...] | None


class PullRequest(BaseModel):
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


class MembersWithRole(_Connection):
    pageInfo: PageInfo
    nodes: tuple[User, ...] | None


class Organization(BaseModel):
    membersWithRole: MembersWithRole

    def __init__(self, **data: dict[str, Any]) -> None:
        super().__init__(**data)
        _issue_pagination_warning("PTB", "developers", self.membersWithRole)


class Tag(BaseModel):
    tagName: str
    createdAt: str


class Commit(BaseModel):
    messageHeadline: str


class CommitHistoryConnection(_Connection):
    nodes: tuple[Commit, ...] | None
