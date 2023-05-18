"""This module contains a Pandoc filter for converting to Telegram's HTML format."""
import pickle
import re
import sys
from pathlib import Path

from panflute import (
    BulletList,
    Citation,
    Cite,
    Doc,
    Element,
    Header,
    Link,
    MetaMap,
    Para,
    Plain,
    Str,
    Strong,
    run_filter,
)

try:
    from ptb_changelog_helper import githubtypes
    from ptb_changelog_helper.const import GITHUB_THREAD_PATTERN, PANDOC_METADATA_KEY
except ImportError:
    # A small hack to get imports working while running this file as pandoc filter without
    # having to keep this file in the root directory
    sys.path.append(str(Path(__file__).parent.parent.parent.absolute().resolve()))

    from ptb_changelog_helper import githubtypes
    from ptb_changelog_helper.const import GITHUB_THREAD_PATTERN, PANDOC_METADATA_KEY

LINE_BREAK = Str("\n")

GH_THREADS: dict[int, githubtypes.PullRequest | githubtypes.Issue] = {}


def _get_gh_threads(file_path: Path) -> None:
    with file_path.open("rb") as file_:
        GH_THREADS.update(pickle.load(file_))


def _build_pr_link(number: int) -> str:
    return f"https://github.com/python-telegram-bot/python-telegram-bot/pull/{number}"


def _build_issue_link(number: int) -> str:
    return f"https://github.com/python-telegram-bot/python-telegram-bot/issue/{number}"


def _build_link(number: str | int) -> str:
    """Given a PR number, builds a link to a PR on GitHub."""
    effective_number = int(number)
    if not GH_THREADS:
        return _build_issue_link(effective_number)
    if (thread := GH_THREADS[effective_number]) and isinstance(thread, githubtypes.PullRequest):
        return _build_pr_link(effective_number)
    return _build_issue_link(effective_number)


def action(  # pylint: disable=too-many-return-statements  # noqa: PLR0911
    element: Element, document: Doc | None  # pylint: disable=unused-argument
) -> Element | list[Element] | None:
    """Pandoc filter for converting to Telegram's HTML format.

    Currently, this does the following:

    * Insert links to PRs on GitHub
    * Make headers bold
    * Add line breaks before and after paragraphs
    * Convert bullet lists to Telegram's format

    """
    if isinstance(element, MetaMap):
        _get_gh_threads(Path(element.content[PANDOC_METADATA_KEY].text))
    if isinstance(element, Str) and (
        match := re.search(pattern=GITHUB_THREAD_PATTERN, string=element.text)
    ):
        pre, post = element.text.split(match.group(1))
        return [
            Str(pre),
            Link(Str(match.group(1)), url=_build_link(match.group(2))),
            Str(post),
        ]
    if isinstance(element, Header):
        return Plain(LINE_BREAK, Strong(*element.content), LINE_BREAK)
    if isinstance(element, Para):
        return Plain(*element.content)
    if isinstance(element, BulletList):
        # BulletList contains a list of LineItem
        # Each of those contains a Plain element (at least in our use case)
        lines = [e.content[0] for e in element.content]
        for line in lines:
            line.content.insert(0, Str("• "))
        return lines
    if isinstance(element, Citation):
        return None
    if isinstance(element, Cite):
        return element.content[0]
    return element


def main(doc: Doc | None = None) -> Doc | None:
    """Main function to be called by panflute."""
    return run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
