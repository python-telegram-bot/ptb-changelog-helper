"""This module contains functionality for converting the MD Changlelog to RST and TG HTML."""
import logging
import subprocess
from pathlib import Path
from typing import Literal

_LOGGER = logging.getLogger(__name__)


def _get_filter_path(output_format: Literal["rst", "html"]) -> Path:
    return Path(__file__).parent / "pandoc_filters" / f"{output_format}_filter.py"


def _run_pandoc(
    input_file: Path, output_file: Path, filter_path: Path, output_format: Literal["rst", "html"]
) -> None:
    args = [
        "pandoc",
        "-o",
        str(output_file.absolute().resolve()),
        "--to",
        output_format,
        "--wrap",
        "none",
        "--filter",
        str(filter_path.absolute().resolve()),
        str(input_file.absolute().resolve()),
    ]
    subprocess.run(args, check=True, capture_output=True)


def convert_to_rst(input_file: Path, output_file: Path) -> None:
    """Converts the given markdown changelog file to reStructuredText.

    Args:
        input_file (:obj:`Path`): The path to the input file.
        output_file (:obj:`Path`): The path to the output file.
    """
    _LOGGER.info("Converting changelog to reStructuredText.")
    _run_pandoc(input_file, output_file, _get_filter_path("rst"), "rst")


def convert_to_tg_html(input_file: Path, output_file: Path) -> None:
    """Converts the given markdown changelog file to Telegram HTML.

    Args:
        input_file (:obj:`Path`): The path to the input file.
        output_file (:obj:`Path`): The path to the output file.
    """
    _LOGGER.info("Converting changelog to Telegram HTML.")
    _run_pandoc(input_file, output_file, _get_filter_path("html"), "html")
