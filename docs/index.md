
# plantuml-sequence

Create PlantUML sequence charts programmatically from Python

```{toctree}
:maxdepth: 3

examples
apidocs/index
```

## Usage

The basic example of the [PlantUML Documentation](https://plantuml.com/sequence-diagram) can be implemented with the
following Python script:

``` python
from plantuml_sequence import SequenceDiagram

with open("my-diagram.puml", "w") as file, SequenceDiagram(file) as sequence:
    (
        sequence.message("Alice", "Bob", "Authentication Request")
        .message("Bob", "Alice", "Authentication Response", arrow_style="-->")
        .blank_line()
        .message("Alice", "Bob", "Another authentication Request")
        .message("Alice", "Bob", "Another authentication Response", arrow_style="<--")
    )

```

Its output inside *my-diagram.puml* is:

``` text
@startuml
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response

Alice -> Bob: Another authentication Request
Alice <-- Bob: Another authentication Response
@enduml
```

For more examples covering different functionality see [examples](#examples).

## Indices and tables

* [Index](genindex)
* [Modules](modindex)
* [Search](search)
