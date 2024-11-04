"""This module contains functionality for converting the MD Changlelog to RST and TG HTML."""

import logging
from collections.abc import Collection
from pathlib import Path
from typing import Literal

from pydantic_yaml import parse_yaml_file_as

from ptb_changelog_helper.changelog import Changelog
from ptb_changelog_helper.githubtypes import User

_LOGGER = logging.getLogger(__name__)


def _convert_to_format(
    input_file: Path,
    output_file: Path,
    target_format: Literal["rst", "md", "html"],
    ptb_devs: Collection[User],
) -> None:
    """Converts the given markdown changelog file to the given format.

    Args:
        input_file (:obj:`Path`): The path to the input file.
        output_file (:obj:`Path`): The path to the output file.
        target_format (:obj:`Literal`["rst", "html"]): The format to convert to.
        ptb_devs (:obj:`Collection`[:class:`User`]): The PTB devs to include in the changelog.
    """
    _LOGGER.info("Converting changelog to %s.", target_format.upper())
    changelog = parse_yaml_file_as(model_type=Changelog, file=input_file.open("rb"))
    with output_file.open("w", encoding="utf-8") as file:
        file.write(getattr(changelog, f"as_{target_format}")(ptb_devs))


def convert_to_rst(input_file: Path, output_file: Path, ptb_devs: Collection[User]) -> None:
    """Converts the given markdown changelog file to reStructuredText.

    Args:
        input_file (:obj:`Path`): The path to the input file.
        output_file (:obj:`Path`): The path to the output file.
        ptb_devs (:obj:`Collection`[:class:`User`]): The PTB devs to include in the changelog.
    """
    _convert_to_format(input_file, output_file, "rst", ptb_devs)


def convert_to_html(input_file: Path, output_file: Path, ptb_devs: Collection[User]) -> None:
    """Converts the given markdown changelog file to Telegram HTML.

    Args:
        input_file (:obj:`Path`): The path to the input file.
        output_file (:obj:`Path`): The path to the output file.
        ptb_devs (:obj:`Collection`[:class:`User`]): The PTB devs to include in the changelog.
    """
    _convert_to_format(input_file, output_file, "html", ptb_devs)


def convert_to_md(input_file: Path, output_file: Path, ptb_devs: Collection[User]) -> None:
    """Converts the given markdown changelog file to markdown.

    Args:
        input_file (:obj:`Path`): The path to the input file.
        output_file (:obj:`Path`): The path to the output file.
        ptb_devs (:obj:`Collection`[:class:`User`]): The PTB devs to include in the changelog.
    """
    _convert_to_format(input_file, output_file, "md", ptb_devs)
