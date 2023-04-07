from plantuml_sequence import SequenceDiagram
from plantuml_sequence.utils import string_io


def test_basic_examples():
    """Test creation of a simple message"""
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        (
            sequence.message("Alice", "Bob", "Authentication Request")
            .message("Bob", "Alice", "Authentication Response", arrow_style="-->")
            .empty_line()
            .message("Alice", "Bob", "Another authentication Request")
            .message("Alice", "Bob", "Another authentication Response", arrow_style="<--")
        )

    content = file_like.read()
    assert (
        content
        == """\
@startuml
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response

Alice -> Bob: Another authentication Request
Alice <-- Bob: Another authentication Response
@enduml
"""
    )
