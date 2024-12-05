import sys

from dataclasses import dataclass, field
from dataclasses_jsonschema import JsonSchemaMixin

from neurosym.bashtool import BashTool
from langchain_community.tools import ReadFileTool, WriteFileTool

from .blocks import compute


# Example schema
@dataclass
class Formula(JsonSchemaMixin):
    path: str = field(
        metadata={"description": "Path of the generated optimized formula"}
    )


def main():
    """Simple neurosymbolic solver with bash/read/write file capabilities."""
    if len(sys.argv) < 2:
        print("Usage: You need to provide an instruction to the neurosymbolic solver.")
        sys.exit(1)

    user_input = sys.argv[1]

    toolbox = [BashTool(), ReadFileTool(verbose=True), WriteFileTool(verbose=True)]
    formula, messages = compute(prompt=user_input, toolbox=toolbox, schema=Formula)
    for message in messages:
        print(message)
    print(formula.path)


__all__ = ["main"]
