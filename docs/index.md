
# plantuml-sequence

Create PlantUML sequence diagrams programmatically from Python.

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

``` text
@startuml
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response

Alice -> Bob: Another authentication Request
Alice <-- Bob: Another authentication Response
@enduml
```

:::{tip}
This file be compiled to an image using the `plantuml` command-line or a online server. See the
[PlantUML documentation](https://plantuml.com/starting) for more details.
:::

For more examples covering different functionality see [examples](#examples).

## Contents

```{toctree}
:maxdepth: 3

examples
apidoc
```

## Indices and tables

* [Index](genindex)
* [Search](search)
