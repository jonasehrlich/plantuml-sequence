import collections.abc
import contextlib
import dataclasses
import functools
import sys
from types import TracebackType
from typing import Literal, TextIO, Type, TypeAlias, TypeVar

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from . import utils

__all__ = ["Participant", "Diagram"]

ParticipantShape: TypeAlias = Literal[
    "participant", "actor", "boundary", "control", "entity", "database", "collections", "queue"
]

GroupType: TypeAlias = Literal["alt", "else", "opt", "loop", "par", "break", "critical", "group"]


T = TypeVar("T", bound=TextIO)


@dataclasses.dataclass(frozen=True)
class Participant:
    """Instance of a participant in the diagram"""

    title: str
    shape: ParticipantShape
    alias: str = ""
    color: str = ""

    def __post_init__(self) -> None:
        if not self.alias:
            object.__setattr__(self, "alias", "".join(filter(str.isalnum, self.title)))

    def __str__(self) -> str:
        quoted_title = utils.maybe_quote(utils.escape_newlines(self.title))
        alias_suffix = "" if self.title == self.alias else f" as {self.alias}"
        return f"{self.shape} {quoted_title}{alias_suffix} {self.color}"


class Diagram:
    """
    Core sequence diagram object

    Create the object and use it as a contextmanager.

    .. code-block:: python

       with open("my-diagram.puml", "w") as f, SequenceDiagram(f) as diagram:
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
        participant1: Participant | str | None,
        participant2: Participant | str | None,
        msg: str | None = None,
        *,
        arrow_style: str | None = None,
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
        :return: Sequence diagram object for chaining
        :rtype: Self
        """
        message_suffix = ""
        if msg:
            message_suffix = f": {utils.escape_newlines(msg)}"
        participant1 = participant_to_string(participant1)
        participant2 = participant_to_string(participant2)
        arrow_style = arrow_style or self._arrow_style
        self._line_writer.writeline(f"{participant1} {arrow_style} {participant2}{message_suffix}")
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
        participant = Participant(title=title, shape=shape, alias=alias, color=color)

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
        background_color = " " + background_color if background_color else ""

        self._line_writer.writeline(f"box{title}{background_color}")
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
        self, participant: Participant | str, color: str = "", destroy: bool = False
    ) -> collections.abc.Generator[Self, None, None]:
        """
        Contextmanager to activate the lifeline of a participant

        :param participant: Participant to activate
        :type participant: Participant | str
        :param color: Color of the active lifeline, defaults to ""
        :type color: str, optional
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

    def activate_lifeline(self, participant: Participant | str, color: str = "") -> Self:
        """
        Activate the lifeline of `participant`

        :param participant: Participant to activate
        :type participant: Participant | str
        :param color: Color of the active lifeline, defaults to ""
        :type color: str, optional
        :return: Sequence diagram instance
        :rtype: Self
        """
        alias = participant_to_string(participant)
        self._line_writer.writeline(f"activate {alias} {color}")
        return self

    def deactivate_lifeline(self, participant: Participant | str) -> Self:
        """
        Deactivate the lifeline of `participant`

        :param participant: Participant to activate
        :type participant: Participant | str
        :param color: Color of the active lifeline, defaults to ""
        :type color: str, optional
        :return: Sequence diagram instance
        :rtype: Self
        """
        alias = participant_to_string(participant)
        self._line_writer.writeline(f"deactivate {alias}")
        return self

    def destroy_lifeline(self, participant: Participant | str) -> Self:
        """
        Deactivate the lifeline of `participant`

        :param participant: Participant to activate
        :type participant: Participant | str
        :param color: Color of the active lifeline, defaults to ""
        :type color: str, optional
        :return: Sequence diagram instance
        :rtype: Self
        """
        alias = participant_to_string(participant)
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
        msg = f" {msg} " if msg else ""
        self._line_writer.writeline(f"=={msg}==")
        return self


def participant_to_string(participant: Participant | str | None) -> str:
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
