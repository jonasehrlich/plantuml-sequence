import collections.abc
import contextlib
import enum
import io
import os
import pathlib
import sys
import tempfile
import textwrap
from typing import Any, TextIO, TypeAlias

if sys.version_info >= (3, 11):
    from enum import StrEnum
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

    # Backport of the StrEnum class from Python 3.11
    class StrEnum(str, enum.Enum):
        """
        Enum where members are also (and must be) strings
        """

        def __new__(cls, *values: Any) -> Self:
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

        @staticmethod
        def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
            """
            Return the lower-cased version of the member name.
            """
            return name.lower()


__all__ = ["StrEnum", "LineWriter", "cwd", "temp_cwd", "string_io", "maybe_quote", "escape_newlines"]


StrPath: TypeAlias = os.PathLike[str] | str


class LineWriter:
    """Write a line-wise to a file and automatically add a line break"""

    def __init__(self, file_like: TextIO) -> None:
        self._file = file_like
        self._prefix = ""

    def writeline(self, line: str) -> None:
        """Write a line to the enclosed file-like object"""
        self._file.write(textwrap.indent(line.strip(), prefix=self._prefix))
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


@contextlib.contextmanager
def string_io() -> collections.abc.Generator[io.StringIO, None, None]:
    """Contextmanager that yields a :py:class:`StringIO` object and seeks to zero position on exit"""
    file_like = io.StringIO()
    try:
        yield file_like
    finally:
        file_like.seek(0)


def maybe_quote(value: str) -> str:
    """
    Quote a string if it is not purely alphanumeric

    :param value: String to quote
    :type value: str
    :return: Quoted or unquoted string
    :rtype: str
    """
    if not value or value.isalnum():
        return value
    return f'"{value}"'


def escape_newlines(val: str) -> str:
    """Escape newline characters in a string"""
    return val.replace("\n", "\\n")
