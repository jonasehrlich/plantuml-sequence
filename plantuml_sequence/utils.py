import collections.abc
import contextlib
import enum
import os
import pathlib
import tempfile
from typing import Literal, TextIO, TypeAlias

try:
    from enum import StrEnum
except ImportError:
    # Backport of the StrEnum class from Python 3.11
    class StrEnum(str, enum.Enum):
        """
        Enum where members are also (and must be) strings
        """

        def __new__(cls, *values):
            "values must already be of type `str`"
            if len(values) > 3:
                raise TypeError("too many arguments for str(): %r" % (values,))
            if len(values) == 1:
                # it must be a string
                if not isinstance(values[0], str):
                    raise TypeError("%r is not a string" % (values[0],))
            if len(values) >= 2:
                # check that encoding argument is a string
                if not isinstance(values[1], str):
                    raise TypeError("encoding must be a string, not %r" % (values[1],))
            if len(values) == 3:
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

    def __init__(
        self, file_like: TextIO, line_break: Literal["\n", "\r\n"] = "\n", trim_trailing_whitespace: bool = True
    ) -> None:
        self._file = file_like
        self._line_break = line_break
        self._trim_trailing_whitespace = trim_trailing_whitespace

    def writeline(self, line: str) -> None:
        """Write a line to the enclosed file-like object"""
        if self._trim_trailing_whitespace:
            line = line.rstrip()
        self._file.write(line)
        self._file.write(self._line_break)

    def writelines(self, lines: collections.abc.Iterable[str]) -> None:
        """Write lines from an iterable to the enclosed file object"""
        for line in lines:
            self.writeline(line)


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
