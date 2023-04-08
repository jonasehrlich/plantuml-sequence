import pathlib
import tempfile

import pytest

from plantuml_sequence import utils


def test_line_writer_writeline() -> None:
    lines = ["hello", "world", "lorem ipsum"]
    with utils.string_io() as file_like:
        line_writer = utils.LineWriter(file_like)
        for line in lines:
            line_writer.writeline(line)

    # Read lines from file-like, except the last, empty one
    output_lines = file_like.read().split("\n")[:-1]
    assert output_lines == lines


def test_line_writer_writelines() -> None:
    lines = ["hello", "world", "lorem ipsum"]
    with utils.string_io() as file_like:
        line_writer = utils.LineWriter(file_like)
        line_writer.writelines(lines)

    # Read lines from file-like, except the last, empty one
    output_lines = file_like.read().split("\n")[:-1]
    assert output_lines == lines


def test_line_writer_indent() -> None:
    lines = ["123", "hello", "world", "lorem ipsum", "zero"]
    expected_output = [" " * num_spaces + item for num_spaces, item in zip((0, 2, 4, 2, 0), lines, strict=True)]
    lines_iter = iter(lines)
    with utils.string_io() as file_like:
        line_writer = utils.LineWriter(file_like)
        line_writer.writeline(next(lines_iter))
        with line_writer.indent():
            line_writer.writeline(next(lines_iter))
            with line_writer.indent():
                line_writer.writeline(next(lines_iter))
            line_writer.writeline(next(lines_iter))
        line_writer.writeline(next(lines_iter))

    # Read lines from file-like, except the last, empty one
    output_lines = file_like.read().split("\n")[:-1]
    assert output_lines == expected_output


def test_line_writer_trailing_whitespace():
    word = "  hello  "
    with utils.string_io() as file_like:
        line_writer = utils.LineWriter(file_like)
        line_writer.writeline(word)
    lines = list(filter(lambda line: line, file_like.read().splitlines()))
    assert lines == [word.strip()]


def test_cwd_contextmanager() -> None:
    """Test the cwd contextmanager"""
    old_cwd = pathlib.Path.cwd()

    with tempfile.TemporaryDirectory() as temp_dir_name:
        with utils.cwd(temp_dir_name) as temp_dir:
            assert pathlib.Path(temp_dir_name).resolve() == temp_dir
            assert pathlib.Path.cwd() == temp_dir
    assert pathlib.Path.cwd() == old_cwd

    with pytest.raises(ValueError), tempfile.TemporaryDirectory() as temp_dir_name:
        with utils.cwd(temp_dir_name) as temp_dir:
            assert pathlib.Path(temp_dir_name).resolve() == temp_dir
            assert pathlib.Path.cwd() == temp_dir
            raise ValueError
    assert pathlib.Path.cwd() == old_cwd


def test_temp_cwd_contextmanager() -> None:
    """Test the temp_cwd contextmanager"""
    old_cwd = pathlib.Path.cwd()
    with utils.temp_cwd() as temp_dir:
        assert pathlib.Path.cwd() == temp_dir
    assert not temp_dir.exists()
    assert pathlib.Path.cwd() == old_cwd

    with pytest.raises(ValueError), utils.temp_cwd() as temp_dir:
        assert pathlib.Path.cwd() == temp_dir
        raise ValueError
    assert not temp_dir.exists()
    assert pathlib.Path.cwd() == old_cwd


def test_string_quoting() -> None:
    for value, quote_required in (
        ("", False),
        ("hello", False),
        ("Hello World", True),
        ("Bob()", True),
        ("Foo.Bar", True),
        ("foo_bar", True),
        ("Foo-bar", True),
    ):
        quoted = utils.maybe_quote(value)
        if quote_required:
            assert quoted == f'"{value}"'
        else:
            assert quoted == value
