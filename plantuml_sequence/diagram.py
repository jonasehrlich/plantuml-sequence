import collections.abc
import contextlib
import dataclasses
import functools
import sys
from types import TracebackType
from typing import Literal, TextIO, Type, TypeAlias

if sys.version_info >= (3, 11):
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

from . import utils

__all__ = ["Participant", "Diagram"]

ParticipantShape: TypeAlias = Literal[
    "participant", "actor", "boundary", "control", "entity", "database", "collections", "queue"
]

NoteShape: TypeAlias = Literal["default", "rectangle", "hexagon"]
MessageNotePosition: TypeAlias = Literal["left", "right"]
ParticipantNotePosition: TypeAlias = Literal["over"] | MessageNotePosition
_NOTE_SHAPE_COMMAND_MAP: dict[NoteShape, str] = {"default": "note", "rectangle": "rnote", "hexagon": "hnote"}
GroupType: TypeAlias = Literal["alt", "else", "opt", "loop", "par", "break", "critical", "group"]


@dataclasses.dataclass(frozen=True)
class Participant:
    """Instance of a participant in the diagram"""

    title: str
    shape: ParticipantShape
    alias: str = ""
    background_color: str | None = None

    def __post_init__(self) -> None:
        if not self.alias:
            object.__setattr__(self, "alias", "".join(filter(str.isalnum, self.title)))

    def __str__(self) -> str:
        quoted_title = utils.maybe_quote(self.title)

        alias_suffix = "" if self.title == self.alias else f" as {self.alias}"

        return (
            f"{self.shape} {utils.escape_newlines(quoted_title)}{alias_suffix}"
            f"{_format_color_cmd(self.background_color)}"
        )


ParticipantOrName: TypeAlias = Participant | str


class Diagram:
    """
    Core sequence diagram object

    Create the object and use it as a contextmanager. This ensures that the ``@startuml`` and ``@enduml``
    commands are written correctly.

    .. code-block:: python

       with open("my-diagram.puml", "w") as f, Diagram(f) as diagram:
          diagram.message("Alice", "Bob", "Hello World!")

    """

    def __init__(
        self,
        file_like: TextIO,
        title: str | None = None,
        hide_footboxes: bool = False,
        hide_unlinked: bool = False,
        teoz_rendering: bool = False,
    ) -> None:
        """
        Initialize the sequence diagram object

        :param file_like: File-like object to write the diagram to
        :type file_like: TextIO
        :param title: Title of the diagram, defaults to None
        :type title: str | None, optional
        :param hide_footboxes: Whether to hide the participant footboxes in the sequence diagram, defaults to False
        :type hide_footboxes: bool, optional
        :param hide_unlinked: Whether to hide unlinked participants, defaults to False
        :type hide_unlinked: bool, optional
        :param teoz_rendering: Whether to use the *teoz* rendering engine, defaults to False
        :type teoz_rendering: bool, optional
        """

        self._line_writer = utils.LineWriter(file_like)
        self._participants: dict[str, Participant] = {}
        self._arrow_style = "->"
        self._title = title
        self._teoz_rendering = teoz_rendering
        self._hide_footboxes = hide_footboxes
        self._hide_unlinked = hide_unlinked

        self.declare_participant = functools.partial(self._declare_some_participant, shape="participant")
        self.declare_actor = functools.partial(self._declare_some_participant, shape="actor")
        self.declare_boundary = functools.partial(self._declare_some_participant, shape="boundary")
        self.declare_control = functools.partial(self._declare_some_participant, shape="control")
        self.declare_entity = functools.partial(self._declare_some_participant, shape="entity")
        self.declare_database = functools.partial(self._declare_some_participant, shape="database")
        self.declare_collections = functools.partial(self._declare_some_participant, shape="collections")
        self.declare_queue = functools.partial(self._declare_some_participant, shape="queue")

    def __enter__(self) -> Self:
        """Enter the context and write the the *startuml* command to the file"""
        self.startuml()
        if self._teoz_rendering:
            self._line_writer.writeline("!pragma teoz true")
        if self._hide_footboxes:
            self._line_writer.writeline("hide footbox")
        if self._hide_unlinked:
            self._line_writer.writeline("hide unlinked")
        if self._title:
            self._line_writer.writeline(f"title {self._title}")
        return self

    def __exit__(
        self, exc_type: Type[BaseException] | None, exc: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Enter the context and write the the *enduml* command to the file"""
        self.enduml()

    def startuml(self) -> Self:
        """Write the `@startuml` command to the file"""
        self._line_writer.writeline("@startuml")
        return self

    def enduml(self) -> Self:
        """Write the `@enduml` command to the file"""
        self._line_writer.writeline("@enduml")
        return self

    def blank_line(self) -> Self:
        """Write a blank line to the file"""
        self._line_writer.writeline("")
        return self

    def message(
        self,
        participant1: ParticipantOrName | None,
        participant2: ParticipantOrName | None,
        msg: str | None = None,
        *,
        arrow_style: str | None = None,
        note: str | None = None,
        note_shape: NoteShape = "default",
        note_position: MessageNotePosition = "right",
        note_background_color: str | None = None,
    ) -> Self:
        """
        Create a message between *participant1* and *participant2*

        :param participant1: Participant left of the arrow
        :type participant1: Participant | str | None
        :param participant2: Participant right of the arrow
        :type participant2: Participant | str | None
        :param msg: Message to send between `participant1` and `participant2`, defaults to None
        :type msg: str | None, optional
        :param arrow_style: Override the arrow style to use, could be used for colored arrows, defaults to None
        :type arrow_style: str | None, optional
        :param note: Note to add left or right of the message, defaults to None
        :type note: str | None, optional
        :param note_shape: Shape of the note to add to the message, defaults to "default"
        :type note_shape: NoteShape, optional
        :param note_position: Position of the note relative to the message, defaults to "right"
        :type note_position: MessageNotePosition, optional
        :param note_background_color: Background color of the note relative to the message, defaults to None
        :type note_background_color: str, optional
        :return: Sequence diagram object for chaining
        :rtype: Self
        """
        message_suffix = ""
        if msg:
            message_suffix = f": {utils.escape_newlines(msg)}"
        participant1 = _participant_to_string(participant1)
        participant2 = _participant_to_string(participant2)
        arrow_style = arrow_style or self._arrow_style
        self._line_writer.writeline(f"{participant1} {arrow_style} {participant2}{message_suffix}")

        if note:
            self._line_writer.writeline(
                (
                    f"{self._note_shape_to_command(note_shape)} {note_position}"
                    f"{_format_color_cmd(note_background_color)}: {utils.escape_newlines(note)}"
                )
            )
        return self

    def _declare_some_participant(
        self, title: str, shape: ParticipantShape, alias: str | None = None, color: str | None = None
    ) -> Participant:
        """
        Declare a participant

        In order to reference this participant in the future use its :py:class:`Participant.alias` attribute.

        :param title: Title of the participant
        :type title: str
        :param shape: Shape of the participant
        :type shape: ParticipantShape
        :param alias: Alias for the participant to use, defaults to None
        :type alias: str, optional
        :param color: Color of the participant, defaults to None
        :type color: str, optional
        :raises ValueError: Raised if the participant exists already
        :return: Instance of the participant
        :rtype: Participant
        """
        alias = alias or ""
        color = color or ""
        participant = Participant(title=utils.escape_newlines(title), shape=shape, alias=alias, background_color=color)

        if participant.alias in self._participants:
            raise ValueError(f"Participant with alias '{participant.alias}' already exists")

        self._participants[participant.alias] = participant
        self._line_writer.writeline(str(participant))
        return participant

    @contextlib.contextmanager
    def participants_box(
        self, title: str | None = None, background_color: str | None = None
    ) -> collections.abc.Generator[Self, None, None]:
        """
        Create a contextmanager which will create a box around some participants

        :param title: Title of the box, defaults to None
        :type title: str | None, optional
        :param background_color: Background color of the box, defaults to None
        :type background_color: str | None, optional
        :yield: Sequence diagram instance
        :rtype: Iterator[collections.abc.Generator[Self, None, None]]
        """
        title = f' "{title}"' if title else ""

        self._line_writer.writeline(f"box{title}{_format_color_cmd(background_color)}")
        try:
            yield self
        finally:
            self._line_writer.writeline("end box")

    @contextlib.contextmanager
    def arrow_style(self, arrow_style: str) -> collections.abc.Generator[Self, None, None]:
        """
        Contextmanager to temporarily change the arrow style used in the diagram.

        The arrow style can be changed in several ways:

        * add a final ``x`` to denote a lost message
        * use ``\\`` or ``/`` instead of ``<`` or ``>`` to have only the bottom or top part of the arrow
        * repeat the arrow head (for example, ``>>`` or ``//``) head to have a thin drawing
        * use ``--`` instead of ``-`` to have a dotted arrow
        * add a final ``o`` at arrow head
        * use bidirectional arrow ``<->``
        """
        old_arrow_style = self._arrow_style
        self._arrow_style = arrow_style
        try:
            yield self
        finally:
            self._arrow_style = old_arrow_style

    def autonumber(self, start: int | None = None, increment: int | None = None) -> Self:
        """
        Enable auto numbering for messages

        :param start: Initial number, defaults to None which means 1
        :type start: int | None, optional
        :param increment: Increment per message, defaults to None which means 1
        :type increment: int | None, optional
        """

        start_suffix = ""
        increment_suffix = ""
        if start is None:
            if increment is not None:
                raise ValueError("Cannot set autonumber increment without start")
        else:
            start_suffix = f" {start}"
            if increment is not None:
                increment_suffix = f" {increment}"

        self._line_writer.writeline(f"autonumber{start_suffix}{increment_suffix}")
        return self

    def autonumber_stop(self) -> Self:
        """Stop auto numbering for messages"""
        self._line_writer.writeline("autonumber stop")
        return self

    def autonumber_resume(self, increment: int | None = None) -> Self:
        """
        Resume previously stopped auto numbering with an optional new increment

        :param increment: New increment to use, defaults to None
        :type increment: int | None, optional
        :return: Sequence diagram instance
        :rtype: Self
        """
        inc = str(increment) if increment is not None else ""
        self._line_writer.writeline(f"autonumber resume {inc}")
        return self

    def newpage(self, title: str | None = None) -> Self:
        """
        Split the diagram into multiple pages

        :param title: Description of the page, defaults to None
        :type title: str | None, optional
        :return: Sequence diagram instance
        :rtype: Self
        """
        title = utils.escape_newlines(title) if title is not None else ""
        self._line_writer.writeline(f"newpage {title}")
        return self

    @contextlib.contextmanager
    def active_lifeline(
        self, participant: ParticipantOrName, color: str | None = None, destroy: bool = False
    ) -> collections.abc.Generator[Self, None, None]:
        """
        Contextmanager to activate the lifeline of a participant

        :param participant: Participant to activate
        :type participant: Participant | str
        :param color: Color of the active lifeline, defaults to None
        :type color: str | None, optional
        :param destroy: Whether to destroy or deactivate the lifeline at the end of the context, defaults to False
        :type destroy: bool, optional
        :yield: Sequence diagram instance
        :rtype: Iterator[collections.abc.Generator[Self, None, None]]
        """
        self.activate_lifeline(participant, color)
        try:
            yield self
        finally:
            if destroy:
                self.destroy_lifeline(participant)
            else:
                self.deactivate_lifeline(participant)

    def activate_lifeline(self, participant: ParticipantOrName, color: str | None = None) -> Self:
        """
        Activate the lifeline of `participant`

        :param participant: Participant to activate
        :type participant: Participant | str
        :param color: Color of the active lifeline, defaults to None
        :type color: str | None, optional
        :return: Sequence diagram instance
        :rtype: Self
        """
        alias = _participant_to_string(participant)
        color = _format_color_cmd(color)
        self._line_writer.writeline(f"activate {alias}{color}")
        return self

    def deactivate_lifeline(self, participant: ParticipantOrName) -> Self:
        """
        Deactivate the lifeline of `participant`

        :param participant: Participant to activate
        :type participant: Participant | str
        :return: Sequence diagram instance
        :rtype: Self
        """
        alias = _participant_to_string(participant)
        self._line_writer.writeline(f"deactivate {alias}")
        return self

    def destroy_lifeline(self, participant: ParticipantOrName) -> Self:
        """
        Deactivate the lifeline of `participant`

        :param participant: Participant to activate
        :type participant: Participant | str
        :return: Sequence diagram instance
        :rtype: Self
        """
        alias = _participant_to_string(participant)
        self._line_writer.writeline(f"destroy {alias}")
        return self

    def delay(self, msg: str | None = None) -> Self:
        """
        Indicate a delay in the diagram

        :param msg: Message to add to the delay, defaults to None
        :type msg: str | None, optional
        :return: Sequence diagram instance
        :rtype: Self
        """
        line = f"...{msg}..." if msg else "..."
        self._line_writer.writeline(line)
        return self

    def space(self, num_pixels: int | None = None) -> Self:
        """
        Indicate some spacing in the diagram

        :param num_pixels: Number of pixels to use for the spacing, defaults to None
        :type num_pixels: int | None, optional
        :return: Sequence diagram instance
        :rtype: Self
        """

        line = f"||{num_pixels}||" if num_pixels is not None else "|||"
        self._line_writer.writeline(line)
        return self

    def divider(self, msg: str | None = None) -> Self:
        """
        Insert a divider or separator to divide the diagram into logical steps

        :param msg: Add a message to the separator
        :type msg: str | None
        :return: Sequence diagram instance
        :rtype: Self
        """
        msg = f" {utils.escape_newlines(msg)} " if msg else ""
        self._line_writer.writeline(f"=={msg}==")
        return self

    def participant_note(
        self,
        participants: collections.abc.Sequence[ParticipantOrName] | ParticipantOrName,
        msg: str,
        shape: NoteShape = "default",
        position: ParticipantNotePosition = "over",
        background_color: str | None = None,
    ) -> Self:
        """
        Place a note relative to a participant

        .. warning::
           Notes can only placed `over` multiple participants. Otherwise an exception will be raised.

        :param participants: Participant or sequence of participant definitions
        :type participants: collections.abc.Sequence[ParticipantOrName] | ParticipantOrName
        :param msg: Message of the note
        :type msg: str
        :param shape: Shape of the note, defaults to "default"
        :type shape: NoteShape, optional
        :param position: Position of the note relative to the participant, defaults to "over"
        :type position: ParticipantNotePosition, optional
        :param background_color: Background color of the note, defaults to None
        :type background_color: str | None, optional
        :raises ValueError: Raised if a note should be placed left or right of multiple participants
        :return: Sequence diagram instance
        :rtype: Self
        """
        if isinstance(participants, (str, Participant)):
            participants = [participants]
        aliases = ", ".join(_participant_to_string(participant) for participant in participants)
        note_cmd = self._note_shape_to_command(shape)
        background_color = _format_color_cmd(background_color)

        if position == "over":
            position_cmd: str = position
        else:
            position_cmd = f"{position} of"
            if len(participants) > 1:
                raise ValueError(f"Cannot add a note {position_cmd} multiple participants")

        self._line_writer.writeline(
            f"{note_cmd} {position_cmd} {aliases}{background_color}: {utils.escape_newlines(msg)}"
        )
        return self

    def note_across(self, msg: str, shape: NoteShape = "default", background_color: str | None = None) -> Self:
        """
        Create a note across all participants

        :param msg: Message of the note
        :type msg: str
        :param shape: Shape of the note, defaults to "default"
        :type shape: NoteShape, optional
        :param background_color: Background color of the note, defaults to None
        :type background_color: str | None, optional
        :return: Sequence diagram instance
        :rtype: Self
        """
        note_cmd = self._note_shape_to_command(shape)
        background_color = _format_color_cmd(background_color)
        self._line_writer.writeline(f"{note_cmd} across{background_color}: {utils.escape_newlines(msg)}")
        return self

    def _note_shape_to_command(self, shape: NoteShape) -> str:
        """
        Transform a note shape to a command

        :param shape: Shape of the note
        :type shape: NoteShape
        :raises ValueError: Raised for invalid note shapes
        :return: Command to create a note with this shape
        :rtype: str
        """
        try:
            return _NOTE_SHAPE_COMMAND_MAP[shape]
        except KeyError as exc:
            raise ValueError(f"Invalid note shape '{shape}'") from exc


def _format_color_cmd(color: str | None) -> str:
    """
    Format a color

    The formatting prepends a space and a hash mark

    :param color: Name of the color or hex code
    :type color: str | None
    :return: Formatted command for the color
    :rtype: str
    """
    return f" #{color}" if color else ""


def _participant_to_string(participant: ParticipantOrName | None) -> str:
    """
    Create a string representation of a participant

    :param participant: Participant or participant name
    :type participant: Participant | str | None
    :return: _description_
    :rtype: str
    """
    if participant is None:
        return ""
    if isinstance(participant, Participant):
        return participant.alias
    return utils.maybe_quote(participant)
