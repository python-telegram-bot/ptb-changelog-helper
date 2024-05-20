"""This moudle contains the main entry point for the PTB changelog helper."""

import logging
from pathlib import Path

from pydantic_yaml import to_yaml_str

from ptb_changelog_helper.changelog import Changelog
from ptb_changelog_helper.conversions import convert_to_html, convert_to_md, convert_to_rst
from ptb_changelog_helper.graphqlclient import GraphQLClient
from ptb_changelog_helper.ptb import insert_next_version, update_changelog, update_version
from ptb_changelog_helper.send_telegram import publish_release_notes
from ptb_changelog_helper.version import Version

_LOGGER = logging.getLogger(__name__)


async def main(
    *,
    new_version: Version,
    github_token: str,
    bot_token: str,
    telegram_chat_id: int | str,
    ptb_dir: Path,
) -> None:
    """The main entry point for the PTB changelog helper. Executes all steps in the correct order.

    Args:
        new_version (:class:`Version`): The new version.
        github_token (:obj:`str`): The GitHub token to use for the GraphQL API.
        bot_token (:obj:`str`): The bot token to use for the Telegram API.
        telegram_chat_id (:obj:`int` | :obj:`str`): The chat ID to send the release notes to.
        ptb_dir (:obj:`Path`): The path to the PTB repository.
    """
    root = Path(__file__).parent.parent.absolute().resolve()
    output_dir = root / "output"
    yaml_changelog_path = output_dir / "changelog.yaml"
    md_changelog_path = output_dir / "changelog.md"
    html_changelog_path = output_dir / "changelog.html"
    rst_changelog_path = output_dir / "changelogs.rst"

    graphql_client = GraphQLClient(auth=github_token)
    await graphql_client.initialize()
    _LOGGER.info("Fetching changelog data from GitHub.")
    changelog = await Changelog.build_for_version(
        version=new_version,
        graphql_client=graphql_client,
    )
    _LOGGER.info("Writing changelog to files.")
    yaml_changelog_path.write_text(to_yaml_str(changelog), encoding="utf-8")
    await graphql_client.shutdown()

    print(
        f"I've written the changelog to the file {yaml_changelog_path}. "
        f"Please make any necessary changes to the changelog now. Press enter when you're done."
    )
    input()

    _LOGGER.info("Converting changelog to reStructuredText and Telegram HTML.")
    convert_to_rst(yaml_changelog_path, rst_changelog_path)
    convert_to_html(yaml_changelog_path, html_changelog_path)
    convert_to_md(yaml_changelog_path, md_changelog_path)

    _LOGGER.info("Sending release notes to Telegram.")
    await publish_release_notes(
        chat_id=telegram_chat_id,
        bot_token=bot_token,
        changelog_path=html_changelog_path,
    )

    _LOGGER.info("Updating version and changelog in python-telegram-bot.")
    print(
        "I've updated the version and changelog in the python-telegram-bot repository. Please "
        "review the changes and then commit and push them."
    )
    update_version(ptb_dir, new_version)
    update_changelog(ptb_dir, rst_changelog_path.read_text(encoding="utf-8"))
    insert_next_version(ptb_dir, new_version)
