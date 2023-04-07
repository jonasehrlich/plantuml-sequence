import pytest

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
    expected_output = """\
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
    assert content == expected_output


def test_declaring_participant_background_color_long_names() -> None:
    """Test declaration of participants with background color and long names"""
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        bob = sequence.declare_actor("Bob", color="#red")
        alice = sequence.declare_participant("Alice")
        long_name = sequence.declare_participant("I have a really\nlong name", alias="L", color="#99FF99")
        sequence.empty_line()
        sequence.message(alice, bob, "Authentication Request")
        sequence.message(bob, alice, "Authentication Response")
        sequence.message(bob, long_name, "Log transaction")
    content = file_like.read()
    expected_output = """\
@startuml
actor Bob #red
participant Alice
participant "I have a really\\nlong name" as L #99FF99

Alice -> Bob: Authentication Request
Bob -> Alice: Authentication Response
Bob -> L: Log transaction
@enduml
"""
    assert content == expected_output


def test_message_to_self() -> None:
    """Test sending of long messages from a participant to itself"""
    msg = "This is a signal to self.\nIt also demonstrates\nmultiline \ntext"
    expected_output0 = """\
@startuml
Alice -> Alice: This is a signal to self.\\nIt also demonstrates\\nmultiline \\ntext
@enduml
"""
    expected_output1 = """\
@startuml
Alice <- Alice: This is a signal to self.\\nIt also demonstrates\\nmultiline \\ntext
@enduml
"""
    for arrow_style, expected_output in (("->", expected_output0), ("<-", expected_output1)):
        with string_io() as file_like, SequenceDiagram(file_like) as sequence:
            sequence.message("Alice", "Alice", message=msg, arrow_style=arrow_style)

        content = file_like.read()
        assert content == expected_output


def test_arrow_style_contextmanager() -> None:
    """Test the contextmanager to change the arrow style"""
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        for arrow_style in ("->x", "->", "->>", "-\\", "\\\\-", "//--", "->o", "o\\\\--", "<->", "<->o"):
            with sequence.arrow_style(arrow_style):
                sequence.message("Bob", "Alice")

    expected_output = """\
@startuml
Bob ->x Alice
Bob -> Alice
Bob ->> Alice
Bob -\\ Alice
Bob \\\\- Alice
Bob //-- Alice
Bob ->o Alice
Bob o\\\\-- Alice
Bob <-> Alice
Bob <->o Alice
@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_message_sequence_numbering_basic() -> None:
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        sequence.autonumber()
        sequence.message("Bob", "Alice", "Authentication Request")
        sequence.message("Bob", "Alice", "Authentication Response", arrow_style="<-")
    expected_output = """\
@startuml
autonumber
Bob -> Alice: Authentication Request
Bob <- Alice: Authentication Response
@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_message_sequence_numbering_increment() -> None:
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        sequence.autonumber()
        sequence.message("Bob", "Alice", "Authentication Request")
        sequence.message("Bob", "Alice", "Authentication Response", arrow_style="<-")
        sequence.empty_line()
        sequence.autonumber(start=15)
        sequence.message("Bob", "Alice", "Another authentication Request")
        sequence.message("Bob", "Alice", "Another authentication Response", arrow_style="<-")
        sequence.empty_line()
        sequence.autonumber(start=40, increment=10)
        sequence.message("Bob", "Alice", "Yet another authentication Request")
        sequence.message("Bob", "Alice", "Yet another authentication Response", arrow_style="<-")
        sequence.empty_line()
    expected_output = """\
@startuml
autonumber
Bob -> Alice: Authentication Request
Bob <- Alice: Authentication Response

autonumber 15
Bob -> Alice: Another authentication Request
Bob <- Alice: Another authentication Response

autonumber 40 10
Bob -> Alice: Yet another authentication Request
Bob <- Alice: Yet another authentication Response

@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_message_sequence_numbering_increment_no_start_value() -> None:
    with string_io() as file_like, SequenceDiagram(file_like) as sequence, pytest.raises(ValueError):
        sequence.autonumber(increment=1)


def test_message_sequence_numbering_stop_resume() -> None:
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        (
            sequence.autonumber(10, 10)
            .message("Bob", "Alice", "Authentication Request")
            .message("Bob", "Alice", "Authentication Response", arrow_style="<-")
            .empty_line()
            .autonumber_stop()
            .message("Bob", "Alice", "dummy")
            .empty_line()
            .autonumber_resume()
            .message("Bob", "Alice", "Yet another authentication Request")
            .message("Bob", "Alice", "Yet another authentication Response", arrow_style="<-")
            .empty_line()
            .autonumber_stop()
            .message("Bob", "Alice", "dummy")
            .empty_line()
            .autonumber_resume(increment=1)
            .message("Bob", "Alice", "Yet another authentication Request")
            .message("Bob", "Alice", "Yet another authentication Response", arrow_style="<-")
        )

    expected_output = """\
@startuml
autonumber 10 10
Bob -> Alice: Authentication Request
Bob <- Alice: Authentication Response

autonumber stop
Bob -> Alice: dummy

autonumber resume
Bob -> Alice: Yet another authentication Request
Bob <- Alice: Yet another authentication Response

autonumber stop
Bob -> Alice: dummy

autonumber resume 1
Bob -> Alice: Yet another authentication Request
Bob <- Alice: Yet another authentication Response
@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_newpage():
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        sequence.empty_line()
        sequence.message("Alice", "Bob", "message 1")
        sequence.message("Alice", "Bob", "message 2").empty_line()
        sequence.newpage().empty_line()
        sequence.message("Alice", "Bob", "message 3")
        sequence.message("Alice", "Bob", "message 4").empty_line()
        sequence.newpage("A title for the\nlast page").empty_line()
        sequence.message("Alice", "Bob", "message 5")
        sequence.message("Alice", "Bob", "message 6")

    expected_output = """\
@startuml

Alice -> Bob: message 1
Alice -> Bob: message 2

newpage

Alice -> Bob: message 3
Alice -> Bob: message 4

newpage A title for the\\nlast page

Alice -> Bob: message 5
Alice -> Bob: message 6
@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_activate_lifeline() -> None:
    """Test lifeline activation and deactivation"""
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        user = sequence.declare_participant("User")
        sequence.empty_line().message(user, "A", "DoWork")
        with sequence.activate_lifeline("A"):
            sequence.empty_line().message("A", "B", "<< createRequest >>")
            with sequence.activate_lifeline("B"):
                sequence.empty_line().message("B", "C", "DoWork")
                with sequence.activate_lifeline("C", destroy=True), sequence.arrow_style("-->"):
                    sequence.message("C", "B", "WorkDone")
                sequence.empty_line().message("B", "A", "RequestCreated", arrow_style="-->")
            sequence.empty_line().message("A", user, "Done")
        sequence.empty_line()

    expected_output = """\
@startuml
participant User

User -> A: DoWork
activate A

A -> B: << createRequest >>
activate B

B -> C: DoWork
activate C
C --> B: WorkDone
destroy C

B --> A: RequestCreated
deactivate B

A -> User: Done
deactivate A

@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_activate_lifeline_with_colors() -> None:
    """Test lifeline activation with colors"""
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        user = sequence.declare_participant("User")
        sequence.empty_line().message(user, "A", "DoWork")
        with sequence.activate_lifeline("A", color="#FFBBBB"):
            sequence.empty_line().message("A", "A", "Internal call")
            with sequence.activate_lifeline("A", color="#DarkSalmon"):
                sequence.empty_line().message("A", "B", "<< createRequest >>")
                with sequence.activate_lifeline("B"), sequence.arrow_style("-->"):
                    sequence.empty_line().message("B", "A", "RequestCreated")
            sequence.message("A", user, "Done")
        sequence.empty_line()

    expected_output = """\
@startuml
participant User

User -> A: DoWork
activate A #FFBBBB

A -> A: Internal call
activate A #DarkSalmon

A -> B: << createRequest >>
activate B

B --> A: RequestCreated
deactivate B
deactivate A
A -> User: Done
deactivate A

@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_delay():
    """Test notation of delays"""
    with string_io() as file_like, SequenceDiagram(file_like) as sequence:
        sequence.empty_line().message("Alice", "Bob", "Authentication Request").delay()
        with sequence.arrow_style("-->"):
            (
                sequence.message("Bob", "Alice", "Authentication Response")
                .delay("5 minutes later")
                .message("Bob", "Alice", "Good Bye !")
                .empty_line()
            )

    expected_output = """\
@startuml

Alice -> Bob: Authentication Request
...
Bob --> Alice: Authentication Response
...5 minutes later...
Bob --> Alice: Good Bye !

@enduml
"""
    content = file_like.read()
    assert content == expected_output
