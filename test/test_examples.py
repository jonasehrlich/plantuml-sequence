import pytest

from plantuml_sequence import Diagram
from plantuml_sequence.utils import string_io


def test_basic_example() -> None:
    """Test creation of a simple message"""
    with string_io() as file_like, Diagram(file_like) as sequence:
        (
            sequence.message("Alice", "Bob", "Authentication Request")
            .message("Bob", "Alice", "Authentication Response", arrow_style="-->")
            .blank_line()
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


def test_declare_duplicate_participant_raises() -> None:
    """Test that declaring two participants with the same alias raises an error"""
    with string_io() as file_like, Diagram(file_like) as sequence:
        sequence.declare_participant("Participant", alias="Foo")
        with pytest.raises(ValueError):
            sequence.declare_participant("Participant", alias="Foo")

    with string_io() as file_like, Diagram(file_like) as sequence:
        sequence.declare_participant("Participant")
        with pytest.raises(ValueError):
            sequence.declare_participant("Participant")


def test_declaring_participant() -> None:
    with string_io() as file_like, Diagram(file_like) as sequence:
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
    with string_io() as file_like, Diagram(file_like) as sequence:
        bob = sequence.declare_actor("Bob", color="red")
        alice = sequence.declare_participant("Alice")
        long_name = sequence.declare_participant("I have a really\nlong name", alias="L", color="99FF99")
        sequence.blank_line()
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


def test_declaring_multiline_participant() -> None:
    with string_io() as file_like, Diagram(file_like) as sequence:
        sequence.declare_participant("bob")
        sequence.declare_participant("I have a really\nlong name", alias="L", color="99FF99")
        sequence.blank_line()
        sequence.message("bob", "L", "Log transaction")
    content = file_like.read()

    expected_output = """\
@startuml
participant bob
participant "I have a really\\nlong name" as L #99FF99

bob -> L: Log transaction
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
        with string_io() as file_like, Diagram(file_like) as sequence:
            sequence.message("Alice", "Alice", msg=msg, arrow_style=arrow_style)

        content = file_like.read()
        assert content == expected_output


def test_message_from_edge() -> None:
    with string_io() as file_like, Diagram(file_like) as sequence:
        sequence.message(None, "Alice", msg="from left edge")
        sequence.message("Alice", None, msg="from right edge", arrow_style="<-")

        sequence.message(None, "Alice", msg="to left edge", arrow_style="<-")
        sequence.message("Alice", None, msg="to right edge")

    expected_output = """\
@startuml
-> Alice: from left edge
Alice <- : from right edge
<- Alice: to left edge
Alice -> : to right edge
@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_arrow_style_contextmanager() -> None:
    """Test the contextmanager to change the arrow style"""
    with string_io() as file_like, Diagram(file_like) as sequence:
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
    with string_io() as file_like, Diagram(file_like) as sequence:
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
    with string_io() as file_like, Diagram(file_like) as sequence:
        sequence.autonumber()
        sequence.message("Bob", "Alice", "Authentication Request")
        sequence.message("Bob", "Alice", "Authentication Response", arrow_style="<-")
        sequence.blank_line()
        sequence.autonumber(start=15)
        sequence.message("Bob", "Alice", "Another authentication Request")
        sequence.message("Bob", "Alice", "Another authentication Response", arrow_style="<-")
        sequence.blank_line()
        sequence.autonumber(start=40, increment=10)
        sequence.message("Bob", "Alice", "Yet another authentication Request")
        sequence.message("Bob", "Alice", "Yet another authentication Response", arrow_style="<-")
        sequence.blank_line()
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
    with string_io() as file_like, Diagram(file_like) as sequence, pytest.raises(ValueError):
        sequence.autonumber(increment=1)


def test_message_sequence_numbering_stop_resume() -> None:
    with string_io() as file_like, Diagram(file_like) as sequence:
        (
            sequence.autonumber(10, 10)
            .message("Bob", "Alice", "Authentication Request")
            .message("Bob", "Alice", "Authentication Response", arrow_style="<-")
            .blank_line()
            .autonumber_stop()
            .message("Bob", "Alice", "dummy")
            .blank_line()
            .autonumber_resume()
            .message("Bob", "Alice", "Yet another authentication Request")
            .message("Bob", "Alice", "Yet another authentication Response", arrow_style="<-")
            .blank_line()
            .autonumber_stop()
            .message("Bob", "Alice", "dummy")
            .blank_line()
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
    with string_io() as file_like, Diagram(file_like) as sequence:
        sequence.blank_line()
        sequence.message("Alice", "Bob", "message 1")
        sequence.message("Alice", "Bob", "message 2").blank_line()
        sequence.newpage().blank_line()
        sequence.message("Alice", "Bob", "message 3")
        sequence.message("Alice", "Bob", "message 4").blank_line()
        sequence.newpage("A title for the\nlast page").blank_line()
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
    with string_io() as file_like, Diagram(file_like) as sequence:
        user = sequence.declare_participant("User")
        sequence.blank_line().message(user, "A", "DoWork")
        with sequence.active_lifeline("A"):
            sequence.blank_line().message("A", "B", "<< createRequest >>")
            with sequence.active_lifeline("B"):
                sequence.blank_line().message("B", "C", "DoWork")
                with sequence.active_lifeline("C", destroy=True), sequence.arrow_style("-->"):
                    sequence.message("C", "B", "WorkDone")
                sequence.blank_line().message("B", "A", "RequestCreated", arrow_style="-->")
            sequence.blank_line().message("A", user, "Done")
        sequence.blank_line()

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
    with string_io() as file_like, Diagram(file_like) as sequence:
        user = sequence.declare_participant("User")
        sequence.blank_line().message(user, "A", "DoWork")
        with sequence.active_lifeline("A", color="FFBBBB"):
            sequence.blank_line().message("A", "A", "Internal call")
            with sequence.active_lifeline("A", color="DarkSalmon"):
                sequence.blank_line().message("A", "B", "<< createRequest >>")
                with sequence.active_lifeline("B"), sequence.arrow_style("-->"):
                    sequence.blank_line().message("B", "A", "RequestCreated")
            sequence.message("A", user, "Done")
        sequence.blank_line()

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


def test_delay() -> None:
    """Test notation of delays"""
    with string_io() as file_like, Diagram(file_like) as sequence:
        sequence.blank_line().message("Alice", "Bob", "Authentication Request").delay()
        with sequence.arrow_style("-->"):
            (
                sequence.message("Bob", "Alice", "Authentication Response")
                .delay("5 minutes later")
                .message("Bob", "Alice", "Good Bye !")
                .blank_line()
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


def test_space() -> None:
    """Test notation of spacings"""
    with string_io() as file_like, Diagram(file_like) as sequence:
        (
            sequence.blank_line()
            .message("Alice", "Bob", "message 1")
            .message("Bob", "Alice", "ok", arrow_style="-->")
            .space()
            .message("Alice", "Bob", "message 2")
            .message("Bob", "Alice", "ok", arrow_style="-->")
            .space(45)
            .message("Alice", "Bob", "message 3")
            .message("Bob", "Alice", "ok", arrow_style="-->")
            .blank_line()
        )

    expected_output = """\
@startuml

Alice -> Bob: message 1
Bob --> Alice: ok
|||
Alice -> Bob: message 2
Bob --> Alice: ok
||45||
Alice -> Bob: message 3
Bob --> Alice: ok

@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_divider() -> None:
    """Test creation of dividers with and without message"""
    with string_io() as file_like, Diagram(file_like) as sequence:
        (
            sequence.blank_line()
            .divider("Initialization")
            .blank_line()
            .message("Alice", "Bob", "Authentication Request")
            .message("Bob", "Alice", "Authentication Response", arrow_style="-->")
            .blank_line()
            .divider("Repetition")
            .blank_line()
            .message("Alice", "Bob", "Another authentication Request")
            .message("Alice", "Bob", "Another authentication Response", arrow_style="<--")
            .blank_line()
            .divider()
            .blank_line()
            .message("Alice", "Bob", "Yet another authentication Request")
            .message("Alice", "Bob", "Yet another authentication Response", arrow_style="<--")
            .blank_line()
        )
    expected_output = """\
@startuml

== Initialization ==

Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response

== Repetition ==

Alice -> Bob: Another authentication Request
Alice <-- Bob: Another authentication Response

====

Alice -> Bob: Yet another authentication Request
Alice <-- Bob: Yet another authentication Response

@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_participants_encompass() -> None:
    """Test creation of a participants encompass"""
    with string_io() as file_like, Diagram(file_like) as sequence:
        sequence.blank_line()
        with sequence.participants_box("Internal Service", "LightBlue"):
            bob = sequence.declare_participant("Bob")
            alice = sequence.declare_participant("Alice")
        other = sequence.declare_participant("Other")
        sequence.blank_line().message(bob, alice, "hello").message(alice, other, "hello").blank_line()

    expected_output = """\
@startuml

box "Internal Service" #LightBlue
participant Bob
participant Alice
end box
participant Other

Bob -> Alice: hello
Alice -> Other: hello

@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_participants_encompass_nested():
    with string_io() as file_like, Diagram(file_like, teoz_rendering=True) as sequence:
        sequence.blank_line()
        with sequence.participants_box("Internal Service", "LightBlue"):
            bob = sequence.declare_participant("Bob")
            with sequence.participants_box("Subteam"):
                alice = sequence.declare_participant("Alice")
                john = sequence.declare_participant("John")
            sequence.blank_line()
        other = sequence.declare_participant("Other")
        (
            sequence.blank_line()
            .message(bob, alice, "hello")
            .message(alice, john, "hello")
            .message(john, other, "Hello")
            .blank_line()
        )

    expected_output = """\
@startuml
!pragma teoz true

box "Internal Service" #LightBlue
participant Bob
box "Subteam"
participant Alice
participant John
end box

end box
participant Other

Bob -> Alice: hello
Alice -> John: hello
John -> Other: Hello

@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_hide_unlinked() -> None:
    """Test the `hide unlinked` option"""
    with string_io() as file_like, Diagram(file_like, hide_unlinked=True) as sequence:
        alice = sequence.declare_participant("Alice")
        bob = sequence.declare_participant("Bob")
        sequence.declare_participant("Carol")
        sequence.blank_line()

        sequence.message(alice, bob, "hello")
    expected_output = """\
@startuml
hide unlinked
participant Alice
participant Bob
participant Carol

Alice -> Bob: hello
@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_remove_footbox() -> None:
    """Test the `hide footbox` option"""
    with string_io() as file_like, Diagram(file_like, title="Foot Box removed", hide_footboxes=True) as sequence:
        (
            sequence.blank_line()
            .message("Alice", "Bob", "Authentication Request")
            .message("Bob", "Alice", "Authentication Response", arrow_style="-->")
            .blank_line()
        )
    expected_output = """\
@startuml
hide footbox
title Foot Box removed

Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response

@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_some_other_notes() -> None:
    """Test notes relative to participants, across all participants with and without colors"""
    with (
        string_io() as file_like,
        Diagram(
            file_like,
        ) as sequence,
    ):
        alice = sequence.declare_participant("Alice")
        bob = sequence.declare_participant("Bob")
        sequence.participant_note(
            alice, "This is displayed\nleft of Alice.", position="left", background_color="aqua"
        ).blank_line()
        sequence.participant_note(alice, "This is displayed right of Alice.", position="right").blank_line()
        sequence.participant_note(alice, "This is displayed over Alice.").blank_line()
        sequence.participant_note([alice, bob], "This is displayed\nover Bob and Alice.", background_color="FFAAAA")

    expected_output = """\
@startuml
participant Alice
participant Bob
note left of Alice #aqua: This is displayed\\nleft of Alice.

note right of Alice: This is displayed right of Alice.

note over Alice: This is displayed over Alice.

note over Alice, Bob #FFAAAA: This is displayed\\nover Bob and Alice.
@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_note_multiple_participants_left_and_right_raises() -> None:
    """Test that the creation of notes `left of` or `right of` multiple participants fails"""
    for position in ("left", "right"):
        with (
            pytest.raises(ValueError),
            string_io() as file_like,
            Diagram(
                file_like,
            ) as sequence,
        ):
            sequence.participant_note(["Alice", "Bob"], "This is displayed\nleft of Alice.", position=position)


def test_notes_on_messages() -> None:
    """Test notes relative to messages"""
    alice = "Alice"
    bob = "Bob"
    with (
        string_io() as file_like,
        Diagram(
            file_like,
        ) as sequence,
    ):
        (
            sequence.message(alice, bob, "hello", note="this is a first note", note_position="left")
            .blank_line()
            .message(bob, alice, "ok", note="this is another note")
            .blank_line()
            .message(
                bob, bob, "I am thinking", note="a note\ncan also be defined\nusing line breaks", note_position="left"
            )
        )

    expected_output = """\
@startuml
Alice -> Bob: hello
note left: this is a first note

Bob -> Alice: ok
note right: this is another note

Bob -> Bob: I am thinking
note left: a note\\ncan also be defined\\nusing line breaks
@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_notes_across_all_participants() -> None:
    """Test placing notes across all participants"""

    alice = "Alice"
    bob = "Bob"
    charlie = "Charlie"
    with (
        string_io() as file_like,
        Diagram(
            file_like,
        ) as sequence,
    ):
        (
            sequence.message(alice, bob, "m1")
            .message(bob, charlie, "m2")
            .participant_note(
                [alice, charlie], 'Old method for note over all part. with:\n ""note over //FirstPart, LastPart//"".'
            )
            .note_across('New method with:\n""note across""')
            .message(bob, alice)
            .note_across("Note across all part.", shape="hexagon")
        )

    expected_output = """\
@startuml
Alice -> Bob: m1
Bob -> Charlie: m2
note over Alice, Charlie: Old method for note over all part. with:\\n ""note over //FirstPart, LastPart//"".
note across: New method with:\\n""note across""
Bob -> Alice
hnote across: Note across all part.
@enduml
"""
    content = file_like.read()
    assert content == expected_output


def test_invalid_note_shape() -> None:
    """Test that invalid note shapes raise value errors"""
    with pytest.raises(ValueError), string_io() as file_like, Diagram(file_like) as sequence:
        sequence.message("bob", "alice", note="important message", note_shape="circle")

    with pytest.raises(ValueError), string_io() as file_like, Diagram(file_like) as sequence:
        sequence.note_across("important message", shape="circle")

    with pytest.raises(ValueError), string_io() as file_like, Diagram(file_like) as sequence:
        sequence.participant_note("bob", "important message", shape="circle")
