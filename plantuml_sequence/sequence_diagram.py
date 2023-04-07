import dataclasses
from types import TracebackType
from typing import Literal, Self, TextIO, Type, TypeAlias, TypeVar

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
    color: str = ""

    def key(self) -> str:
        return self.title.replace(" ", "_").replace("-", "_").lower()

    def __str__(self) -> str:
        return f'{self.shape} "{self.title}" as {self.key()} {self.color}'


def title_to_key(title: str):
    return title.replace(" ", "_").replace("-", "_").lower()


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
        participant1 = participant_to_key(participant1)
        participant2 = participant_to_key(participant2)
        arrow_style = arrow_style or self._arrow_style
        self._line_writer.writeline(f"{participant1} {arrow_style} {participant2}{message_suffix}")
        return self


def participant_to_key(participant: Participant | str | None) -> str:
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
        return participant.key()

    if participant.isalnum():
        return participant
    return f'"{participant}"'
