import collections.abc
import dataclasses
import functools
from types import TracebackType
from typing import Literal, ParamSpec, Self, TextIO, Type, TypeAlias, TypeVar

from . import utils

ParticipantShape: TypeAlias = Literal[
    "participant", "actor", "boundary", "control", "entity", "database", "collections", "queue"
]

GroupType: TypeAlias = Literal["alt", "else", "opt", "loop", "par", "break", "critical", "group"]


T = TypeVar("T", bound=TextIO)
P = ParamSpec


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
        quoted_title = quote_string_if_required(self.title)
        return f"{self.shape} {quoted_title} as {self.alias} {self.color}"


def _participant_shape_partialmethod(
    generic_declare_method: collections.abc.Callable[..., Participant], shape: ParticipantShape
) -> functools.partialmethod[Participant]:
    """Create a :py:class:`functools.partialmethod` object with a fixed shape argument"""
    new_method = functools.partialmethod(generic_declare_method, shape=shape)
    if generic_declare_method.__doc__ is not None:
        new_docstring = "\n".join(
            line.replace("participant", shape)
            for line in generic_declare_method.__doc__.split("\n")
            if "shape" not in line
        )
        new_method.__doc__ = new_docstring
    return new_method


class SequenceDiagram:
    def __init__(self, file_like: TextIO) -> None:
        self._line_writer = utils.LineWriter(file_like)
        self._participants: dict[str, Participant] = {}
        self._arrow_style = "->"

    def __enter__(self):
        """Enter the context and write the the startuml command to the file"""
        return self.startuml()

    def __exit__(
        self, exc_type: Type[BaseException] | None, exc: BaseException | None, exc_tb: TracebackType | None
    ) -> bool:
        """Enter the context and write the the enduml command to the file"""
        self.enduml()
        # Do not suppress any raised exceptions
        return False

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

    def declare_participant(
        self, title: str, shape: ParticipantShape = "participant", alias: str | None = None, color: str | None = None
    ) -> Participant:
        """
        Declare a participant

        In order to reference this participant in the future use its :py:class:`Participant.alias` attribute.

        :param title: Title of the participant
        :type title: str
        :param shape: Shape of the participant, defaults to "participant"
        :type shape: ParticipantShape, optional
        :param alias: Alias for the participant to use, defaults to ""
        :type alias: str, optional
        :param color: _description_, defaults to ""
        :type color: str, optional
        :raises ValueError: _description_
        :return: _description_
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

    declare_actor = _participant_shape_partialmethod(declare_participant, shape="actor")
    declare_boundary = _participant_shape_partialmethod(declare_participant, shape="boundary")
    declare_control = _participant_shape_partialmethod(declare_participant, shape="control")
    declare_entity = _participant_shape_partialmethod(declare_participant, shape="entity")
    declare_database = _participant_shape_partialmethod(declare_participant, shape="database")
    declare_collections = _participant_shape_partialmethod(declare_participant, shape="collections")
    declare_queue = _participant_shape_partialmethod(declare_participant, shape="queue")


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
    return quote_string_if_required(participant)


def quote_string_if_required(value: str):
    """
    Quote a string if it is not purely alphanumeric

    :param value: String to quote
    :type value: str
    :return: Quoted or unquoted string
    :rtype: _type_
    """
    if value.isalnum():
        return value
    return f'"{value}"'
