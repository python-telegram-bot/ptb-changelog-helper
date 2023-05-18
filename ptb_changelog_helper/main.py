"""This moudle contains the main entry point for the PTB changelog helper."""
import logging
from pathlib import Path

from ptb_changelog_helper.changelog import Changelog
from ptb_changelog_helper.graphqlclient import GraphQLClient
from ptb_changelog_helper.pandoc import convert_to_rst, convert_to_tg_html
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
    docs_md_changelog_path = output_dir / "changelogs_docs.md"
    tg_md_changelog_path = output_dir / "changelog_tg.md"
    tg_html_changelog_path = output_dir / "changelog_tg.html"
    docs_rst_changelog_path = output_dir / "changelogs_docs.rst"
    data_storage_path = output_dir / "github_threads.pickle"

    graphql_client = GraphQLClient(auth=github_token)
    await graphql_client.initialize()
    _LOGGER.info("Fetching changelog data from GitHub.")
    changelog = await Changelog.build_for_version(
        version=new_version,
        graphql_client=graphql_client,
        store_threads=data_storage_path,
    )
    _LOGGER.info("Writing changelog to files both for the docs and for the release channel.")
    docs_md_changelog_path.write_text(changelog.as_markdown(target="docs"), encoding="utf-8")
    tg_md_changelog_path.write_text(changelog.as_markdown(target="channel"), encoding="utf-8")
    await graphql_client.shutdown()

    print(
        f"I've written the changelog to the files {docs_md_changelog_path} and "
        f"{tg_md_changelog_path}. Please make any necessary changes to the changelog now. Press "
        f"enter when you're done."
    )
    input()

    _LOGGER.info("Converting changelog to reStructuredText and Telegram HTML.")
    convert_to_rst(docs_md_changelog_path, docs_rst_changelog_path, data_storage_path)
    convert_to_tg_html(tg_md_changelog_path, tg_html_changelog_path, data_storage_path)

    _LOGGER.info("Sending release notes to Telegram.")
    await publish_release_notes(
        chat_id=telegram_chat_id,
        bot_token=bot_token,
        changelog_path=tg_html_changelog_path,
    )

    _LOGGER.info("Updating version and changelog in python-telegram-bot.")
    print(
        "I've updated the version and changelog in the python-telegram-bot repository. Please "
        "review the changes and then commit and push them."
    )
    update_version(ptb_dir, new_version)
    update_changelog(ptb_dir, docs_rst_changelog_path.read_text(encoding="utf-8"))
    insert_next_version(ptb_dir, new_version)
