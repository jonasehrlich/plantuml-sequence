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

ParticipantShape: TypeAlias = Literal[
    "participant", "actor", "boundary", "control", "entity", "database", "collections", "queue"
]

GroupType: TypeAlias = Literal["alt", "else", "opt", "loop", "par", "break", "critical", "group"]


T = TypeVar("T", bound=TextIO)


@dataclasses.dataclass(frozen=True)
class Participant:
    title: str
    shape: ParticipantShape
    alias: str = ""
    color: str = ""

    def __post_init__(self) -> None:
        if not self.alias:
            object.__setattr__(self, "alias", "".join(filter(str.isalnum, self.title)))

    def __str__(self) -> str:
        quoted_title = utils.quote_string_if_required(utils.escape_newlines(self.title))
        return f"{self.shape} {quoted_title} as {self.alias} {self.color}"


class SequenceDiagram:
    def __init__(self, file_like: TextIO) -> None:
        self._line_writer = utils.LineWriter(file_like)
        self._participants: dict[str, Participant] = {}
        self._arrow_style = "->"

        self.declare_participant = functools.partial(self._declare_some_participant, shape="participant")
        self.declare_participant.__doc__ = "foobar test"
        self.declare_actor = functools.partial(self._declare_some_participant, shape="actor")
        self.declare_boundary = functools.partial(self._declare_some_participant, shape="boundary")
        self.declare_control = functools.partial(self._declare_some_participant, shape="control")
        self.declare_entity = functools.partial(self._declare_some_participant, shape="entity")
        self.declare_database = functools.partial(self._declare_some_participant, shape="database")
        self.declare_collections = functools.partial(self._declare_some_participant, shape="collections")
        self.declare_queue = functools.partial(self._declare_some_participant, shape="queue")

    def __enter__(self) -> Self:
        """Enter the context and write the the startuml command to the file"""
        return self.startuml()

    def __exit__(
        self, exc_type: Type[BaseException] | None, exc: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Enter the context and write the the enduml command to the file"""
        self.enduml()

    def startuml(self) -> Self:
        """Write the @startuml command to the file"""
        self._line_writer.writeline("@startuml")
        return self

    def enduml(self) -> Self:
        """Write the @enduml command to the file"""
        self._line_writer.writeline("@enduml")
        return self

    def empty_line(self) -> Self:
        """Write an empty line to the file"""
        self._line_writer.writeline("")
        return self

    def message(
        self,
        participant1: Participant | str | None,
        participant2: Participant | str | None,
        message: str | None = None,
        arrow_style: str | None = None,
    ) -> Self:
        """
        Create a message between `participant1` and `participant2`

        :param participant1: Key or :py:class:`Participant`
        :type participant1: Participant | str | None
        :param participant2: Key or :py:class:`Participant`
        :type participant2: Participant | str | None
        :param message: Message to send between `participant1` and `participant2`, defaults to None
        :type message: str | None, optional
        :param arrow_style: Override the arrow style to use, could be used for colored arrows, defaults to None
        :type arrow_style: str | None, optional
        :return: Sequence diagram object for chaining
        :rtype: Self
        """
        message_suffix = ""
        if message:
            message_suffix = f": {message}"
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
    return utils.quote_string_if_required(participant)
