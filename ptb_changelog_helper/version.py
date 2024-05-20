"""This module contains a class that represents a version number."""

import re
from typing import Final, Literal, NamedTuple


class Version(NamedTuple):
    """This class is basically copied from PTB. We don't import it, because it's private and
    we want to rely only on the public API."""

    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int

    def _rl_shorthand(self) -> str:
        return {
            "alpha": "a",
            "beta": "b",
            "candidate": "rc",
        }[self.releaselevel]

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}"
        if self.micro != 0:
            version = f"{version}.{self.micro}"
        if self.releaselevel != "final":
            version = f"{version}{self._rl_shorthand()}{self.serial}"

        return version


VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    pattern=r"""
    __version_info__:\ Final\[Version\]\ =\ Version\(\s*
        major=(?P<major>\d+),\s*
        minor=(?P<minor>\d+),\s*
        micro=(?P<micro>\d+),\s*
        releaselevel=(?P<releaselevel>[\"a-z]+),\s*
        serial=(?P<serial>\d+)\s*
    \)
    """,
    flags=re.VERBOSE,
)
