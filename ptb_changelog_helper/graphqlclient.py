from collections.abc import Collection
from pathlib import Path
from typing import Any, overload

from gql import Client, gql
from gql.client import AsyncClientSession
from gql.transport.aiohttp import AIOHTTPTransport

from ptb_changelog_helper import githubtypes
from ptb_changelog_helper.const import USER_AGENT


class GraphQLClient:
    def __init__(self, auth: str) -> None:
        # OAuth token must be prepended with "Bearer". User might forget to do this.
        authorization = auth if auth.casefold().startswith("bearer ") else f"Bearer {auth}"

        self._transport = AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={
                "Authorization": authorization,
                "user-agent": USER_AGENT,
            },
        )
        self._session = AsyncClientSession(Client(transport=self._transport))
        self._query_path = Path(__file__).parent.resolve().absolute() / "graphql_queries"
        self._get_thread_insertion = (self._query_path / "getThreadsInsertion.gql").read_text(
            encoding="utf-8"
        )

    async def initialize(self) -> None:
        await self._transport.connect()

    async def shutdown(self) -> None:
        await self._transport.close()

    def _get_query_text(self, query_name: str) -> str:
        return (self._query_path / f"{query_name}.gql").read_text(encoding="utf-8")

    @overload
    async def _do_request(
        self, *, query: str | None = None, variable_values: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        ...

    @overload
    async def _do_request(
        self, *, query_name: str | None = None, variable_values: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        ...

    async def _do_request(
        self,
        *,
        query_name: str | None = None,
        query: str | None = None,
        variable_values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if query_name is None and query is None:
            raise ValueError("Either query_name or query must be specified")
        return await self._session.execute(
            gql(query or self._get_query_text(query_name)),  # type: ignore[arg-type]
            variable_values=variable_values,
        )

    async def get_threads(
        self,
        numbers: Collection[int],
    ) -> dict[int, githubtypes.PullRequest | githubtypes.Issue]:
        """Get specified threads (issues/prs) on the PTB repository"""
        insertion = "\n".join(
            self._get_thread_insertion.replace("<NUMBER>", str(number)) for number in numbers
        )
        query = self._get_query_text("getThreads").replace("<INSERTION>", insertion)
        result = await self._do_request(
            query=query,
        )

        data = result["repository"]
        by_number = {}
        for entry in data.values():
            if entry is not None:
                cls = getattr(githubtypes, entry["__typename"])
                obj = cls(**entry)
                by_number[obj.number] = obj
        return by_number

    async def get_ptb_devs(self) -> tuple[githubtypes.User, ...]:
        """Get all PTB developers on the PTB organization"""
        result = await self._do_request(query_name="getPTBDevs")
        organization = githubtypes.Organization(**result["organization"])
        return organization.membersWithRole.nodes or ()

    async def get_last_release_tag(self) -> githubtypes.Tag:
        """Get the last release tag of PTB."""
        result = await self._do_request(query_name="getLastRelease")
        return githubtypes.Tag(**result["repository"]["releases"]["edges"][0]["node"])

    async def get_commits_since(self, date: str) -> tuple[githubtypes.Commit, ...]:
        """Get all commits since the given date."""
        result = await self._do_request(
            query_name="getCommitsSince", variable_values={"date": date}
        )
        commit_history_connection = githubtypes.CommitHistoryConnection(
            **result["repository"]["object"]["history"]
        )
        commits = list(commit_history_connection.nodes) if commit_history_connection.nodes else []

        while commit_history_connection.pageInfo.hasNextPage:
            result = await self._do_request(
                query_name="getCommitsSince",
                variable_values={
                    "date": date,
                    "after": commit_history_connection.pageInfo.endCursor,
                },
            )
            commit_history_connection = githubtypes.CommitHistoryConnection(
                **result["repository"]["object"]["history"]
            )
            if commit_history_connection.nodes:
                commits.extend(commit_history_connection.nodes)

        return tuple(commits)

    async def get_commits_since_last_release(self) -> tuple[githubtypes.Commit, ...]:
        """Get all commits since the last release."""
        last_release_tag = await self.get_last_release_tag()
        return await self.get_commits_since(last_release_tag.createdAt)
