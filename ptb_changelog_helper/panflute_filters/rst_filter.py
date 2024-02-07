# pylint: disable=duplicate-code
"""This module contains a Pandoc filter for converting to Sphinx's reStructuredText format."""
import pickle
import re
import sys
from pathlib import Path

from panflute import Doc, Element, MetaMap, RawInline, Str, run_filter

try:
    from ptb_changelog_helper import githubtypes
    from ptb_changelog_helper.const import GITHUB_THREAD_PATTERN, PANDOC_METADATA_KEY
except ImportError:
    # A small hack to get imports working while running this file as pandoc filter without
    # having to keep this file in the root directory
    sys.path.append(str(Path(__file__).parent.parent.parent.absolute().resolve()))

    from ptb_changelog_helper import githubtypes
    from ptb_changelog_helper.const import GITHUB_THREAD_PATTERN, PANDOC_METADATA_KEY

GH_THREADS: dict[int, githubtypes.PullRequest | githubtypes.Issue] = {}


def _get_gh_threads(file_path: Path) -> None:
    with file_path.open("rb") as file_:
        GH_THREADS.update(pickle.load(file_))


def _build_pr_directive(number: int) -> str:
    return f":pr:`{number}`"


def _build_issue_directive(number: int) -> str:
    return f":issue:`{number}`"


def _build_directive(number: str | int) -> str:
    """Given a PR number, builds a link to a PR on GitHub."""
    effective_number = int(number)
    if not GH_THREADS:
        return _build_issue_directive(effective_number)
    if (thread := GH_THREADS[effective_number]) and isinstance(thread, githubtypes.PullRequest):
        return _build_pr_directive(effective_number)
    return _build_issue_directive(effective_number)


def action(
    element: Element, document: Doc | None  # pylint: disable=unused-argument
) -> Element | list[Element] | None:
    """Pandoc filter for converting to Sphinx's reStructuredText format.

    Currently, this does the following:

    * Replace ``(#123)`` with ``(:pr:`123`)``.

    """
    if isinstance(element, MetaMap):
        _get_gh_threads(Path(element.content[PANDOC_METADATA_KEY].text))
    if isinstance(element, Str) and (
        match := re.search(pattern=GITHUB_THREAD_PATTERN, string=element.text)
    ):
        pre, post = element.text.split(match.group(1))
        return [
            Str(pre),
            RawInline(_build_directive(match.group(2)), format="rst"),
            Str(post),
        ]
    return None


def main(doc: Doc | None = None) -> Doc | None:
    """Main function to be called by panflute."""
    return run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
