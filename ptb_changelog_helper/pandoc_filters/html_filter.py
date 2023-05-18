"""This module contains a Pandoc filter for converting to Telegram's HTML format."""
import logging
import re
from pydoc import Doc

from panflute import BulletList, Element, Header, Link, Para, Plain, Str, Strong, run_filter

LINE_BREAK = Str("\n")
_LOGGER = logging.getLogger(__name__)


def _build_pr_link(number: str | int) -> str:
    """Given a PR number, builds a link to a PR on GitHub."""
    return f"https://github.com/python-telegram-bot/python-telegram-bot/pull/{number}"


def action(
    element: Element, document: Doc | None  # pylint: disable=unused-argument
) -> Element | list[Element] | None:
    """Pandoc filter for converting to Telegram's HTML format.

    Currently, this does the following:

    * Insert links to PRs on GitHub
    * Make headers bold
    * Add line breaks before and after paragraphs
    * Convert bullet lists to Telegram's format

    """
    if isinstance(element, Str) and (
        match := re.match(pattern=r"\((\#(\d+))\)", string=element.text)
    ):
        _LOGGER.debug("Found PR link: %s. Inserting link to GitHub thread", match.group(1))
        return [
            Str("("),
            Link(Str(match.group(1)), url=_build_pr_link(match.group(2))),
            Str(")"),
        ]
    if isinstance(element, Header):
        _LOGGER.debug("Converting header to bold.")
        return Plain(Strong(*element.content))
    if isinstance(element, Para):
        _LOGGER.debug("Adding line breaks around paragraph.")
        return Plain(LINE_BREAK, *element.content, LINE_BREAK)
    if isinstance(element, BulletList):
        _LOGGER.debug("Converting bullet list to Telegram format.")
        # BulletList contains a list of LineItem
        # Each of those contains a Plain element (at least in our use case)
        lines = [e.content[0] for e in element.content]
        for line in lines:
            line.content.insert(0, Str("• "))
        return [Plain(LINE_BREAK), *lines, Plain(LINE_BREAK)]
    return element


def main(doc: Doc | None = None) -> Doc | None:
    """Main function to be called by panflute."""
    return run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
