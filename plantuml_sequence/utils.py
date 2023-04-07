import collections.abc
import contextlib
import enum
import os
import pathlib
import tempfile
import textwrap
from typing import Self, TextIO, TypeAlias

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover
    # Backport of the StrEnum class from Python 3.11
    class StrEnum(str, enum.Enum):
        """
        Enum where members are also (and must be) strings
        """

        def __new__(cls, *values):
            "values must already be of type `str`"
            if len(values) > 3:  # noqa: PLR2004
                raise TypeError("too many arguments for str(): %r" % (values,))
            if len(values) == 1:
                # it must be a string
                if not isinstance(values[0], str):
                    raise TypeError("%r is not a string" % (values[0],))
            if len(values) >= 2:  # noqa: PLR2004
                # check that encoding argument is a string
                if not isinstance(values[1], str):
                    raise TypeError("encoding must be a string, not %r" % (values[1],))
            if len(values) == 3:  # noqa: PLR2004
                # check that errors argument is a string
                if not isinstance(values[2], str):
                    raise TypeError("errors must be a string, not %r" % (values[2]))
            value = str(*values)
            member = str.__new__(cls, value)
            member._value_ = value
            return member

        def _generate_next_value_(name, start, count, last_values):
            """
            Return the lower-cased version of the member name.
            """
            return name.lower()


__all__ = ["StrEnum", "LineWriter", "cwd", "temp_cwd"]


StrPath: TypeAlias = os.PathLike | str


class LineWriter:
    """Write a line-wise to a file and automatically add a line break"""

    def __init__(self, file_like: TextIO) -> None:
        self._file = file_like
        self._prefix = ""

    def writeline(self, line: str) -> None:
        """Write a line to the enclosed file-like object"""
        self._file.write(textwrap.indent(line, prefix=self._prefix))
        self._file.write("\n")

    def writelines(self, lines: collections.abc.Iterable[str]) -> None:
        """Write lines from an iterable to the enclosed file object"""
        for line in lines:
            self.writeline(line)

    @contextlib.contextmanager
    def indent(self, indent: int = 2) -> collections.abc.Generator[Self, None, None]:
        """
        Contextmanager to automatically indent inside the context

        :param indent: Number of spaces to indent inside the context, defaults to 2
        :yield: Modified line writer
        """
        old_prefix = self._prefix
        self._prefix += " " * indent
        try:
            yield self
        finally:
            self._prefix = old_prefix


@contextlib.contextmanager
def cwd(path: StrPath) -> collections.abc.Generator[pathlib.Path, None, None]:
    """
    Contextmanager to temporarily change the current working directory

    :param path: Path to change the current working directory to
    :type path: StrPath
    :yield: Path the current working directory was changed to
    :rtype: Generator[pathlib.Path, None, None]
    """
    old_cwd = pathlib.Path.cwd()
    path = pathlib.Path(path).resolve()
    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(old_cwd)


@contextlib.contextmanager
def temp_cwd() -> collections.abc.Generator[pathlib.Path, None, None]:
    """
    Contextmanager to temporarily change the current working directory to a temporary directory

    :yield: Path the current working directory was changed to∏
    :rtype: Generator[pathlib.Path, None, None]
    """
    with tempfile.TemporaryDirectory() as temp_dir_name, cwd(temp_dir_name) as temp_dir:
        yield temp_dir
