from plantuml_sequence import SequenceDiagram
from plantuml_sequence.utils import string_io


def test_basic_examples() -> None:
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


def test_declaring_participant() -> None:
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        participants = [
            sequence.declare_participant("Participant", alias="Foo"),
            sequence.declare_actor("Actor", alias="Foo1"),
            sequence.declare_boundary("Boundary", alias="Foo2"),
            sequence.declare_control("Control", alias="Foo3"),
            sequence.declare_entity("Entity", alias="Foo4"),
            sequence.declare_database("Database", alias="Foo5"),
            sequence.declare_collections("Collections", alias="Foo6"),
            sequence.declare_queue("Queue", alias="Foo7"),
        ]
        for dest in participants[1:]:
            sequence.message(participants[0], dest, f"To {dest.shape}")

    content = file_like.read()
    assert (
        content
        == """\
@startuml
participant Participant as Foo
actor Actor as Foo1
boundary Boundary as Foo2
control Control as Foo3
entity Entity as Foo4
database Database as Foo5
collections Collections as Foo6
queue Queue as Foo7
Foo -> Foo1: To actor
Foo -> Foo2: To boundary
Foo -> Foo3: To control
Foo -> Foo4: To entity
Foo -> Foo5: To database
Foo -> Foo6: To collections
Foo -> Foo7: To queue
@enduml
"""
    )
