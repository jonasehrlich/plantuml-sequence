# plantuml-sequence

Create PlantUML sequence charts programmatically from Python

## Usage

The basic example of the [PlantUML Documentation](https://plantuml.com/sequence-diagram) can be implemented with the
following Python script:

``` python
from plantuml_sequence import Diagram

with open("my-diagram.puml", "w") as file, Diagram(file) as sequence:
    (
        sequence.message("Alice", "Bob", "Authentication Request")
        .message("Bob", "Alice", "Authentication Response", arrow_style="-->")
        .blank_line()
        .message("Alice", "Bob", "Another authentication Request")
        .message("Alice", "Bob", "Another authentication Response", arrow_style="<--")
    )

```

Its output inside *my-diagram.puml* is:

``` puml
@startuml
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response

Alice -> Bob: Another authentication Request
Alice <-- Bob: Another authentication Response
@enduml
```

## Features

Not all of the features of message sequence charts are supported yet. See the list of implemented features below.

### General

* [x] Use *teoz* renderer

### Participants

* [x] Declaring participants
* [ ] Multiline participants
* [ ] Create participant with message
* [x] Lifeline activation / deactivation
* [ ] Lifeline auto-activate
* [x] Participants encompass (Box around participants)
* [x] Remove foot boxes

### Messages

* [x] Messages
* [x] Basic `autonumber` message numbering
* [ ] Advanced auto numbering
  * [ ] `autonumber` formats
  * [ ] `autonumber` sequence increments
* [ ] Hide unlinked participants
* [ ] Mainframe

### Notes

* [ ] Different note shapes (`note`, `hnote`, `rnote`)
* [ ] Notes on messages
* [ ] Notes over / left / right of lifelines
* [ ] Notes across all participants
* [ ] Multiple notes at the same level

### Flow

* [ ] Basic message grouping
* [ ] `alt` / `else` groups
* [x] Divider
* [ ] Reference
* [x] Delay
* [x] Space

### Styling

* [ ] Colored groups
* [x] Arrow style change
  * [x] Standard arrow styles
  * [x] Short arrows
* [ ] Slanted arrows
* [ ] Styling changes using the [`skinparam`](https://plantuml.com/skinparam) command

### Preprocessing

> Currently no preprocessing features are planned to be supported

* [ ] Variable definition
* [ ] Boolean expression
* [ ] Conditions
* [ ] While loops
* [ ] Procedures & functions blocks
* [ ] Include directive
* [ ] Memory dump
* [ ] Assertions
