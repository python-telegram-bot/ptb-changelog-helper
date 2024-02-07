"""This module contains functionality for converting the MD Changlelog to RST and TG HTML."""

import logging
import subprocess
from pathlib import Path
from typing import Literal

from ptb_changelog_helper.const import PANDOC_METADATA_KEY

_LOGGER = logging.getLogger(__name__)


def _get_filter_path(output_format: Literal["rst", "html"]) -> Path:
    return Path(__file__).parent / "panflute_filters" / f"{output_format}_filter.py"


def _run_pandoc(
    input_file: Path,
    output_file: Path,
    filter_path: Path,
    output_format: Literal["rst", "html"],
    thread_storage_path: Path,
) -> None:
    args = [
        "pandoc",
        "-o",
        str(output_file.absolute().resolve()),
        "--to",
        output_format,
        "--wrap",
        "none",
        "--metadata",
        f"{PANDOC_METADATA_KEY}:{thread_storage_path.absolute().resolve()}",
        "--filter",
        str(filter_path.absolute().resolve()),
        str(input_file.absolute().resolve()),
    ]
    subprocess.run(args, check=True)


def convert_to_rst(input_file: Path, output_file: Path, thread_storage_path: Path) -> None:
    """Converts the given markdown changelog file to reStructuredText.

    Args:
        input_file (:obj:`Path`): The path to the input file.
        output_file (:obj:`Path`): The path to the output file.
        thread_storage_path (:obj:`Path`): The path to the thread storage file.
    """
    _LOGGER.info("Converting changelog to reStructuredText.")
    _run_pandoc(input_file, output_file, _get_filter_path("rst"), "rst", thread_storage_path)


def convert_to_tg_html(input_file: Path, output_file: Path, thread_storage_path: Path) -> None:
    """Converts the given markdown changelog file to Telegram HTML.

    Args:
        input_file (:obj:`Path`): The path to the input file.
        output_file (:obj:`Path`): The path to the output file.
        thread_storage_path (:obj:`Path`): The path to the thread storage file.
    """
    _LOGGER.info("Converting changelog to Telegram HTML.")
    _run_pandoc(input_file, output_file, _get_filter_path("html"), "html", thread_storage_path)
