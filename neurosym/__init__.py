import sys

from neurosym.bashtool import BashTool
from langchain_community.tools import ReadFileTool, WriteFileTool

from .blocks import while_loop


MYSCHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path of the generated optimized formula",
    }
  },
  "required": ["path"],
  "additionalProperties": False
}



def main():
    """Simple neurosymbolic solver with bash/read/write file capabilities."""
    if len(sys.argv) < 2:
        print("Usage: You need to provide an instruction to the neurosymbolic solver.")
        sys.exit(1)

    user_input = sys.argv[1]

    toolbox = [BashTool(), ReadFileTool(verbose=True), WriteFileTool(verbose=True)]
    result, messages = while_loop(prompt=user_input, toolbox=toolbox, schema=MYSCHEMA)
    for message in messages:
        print(message)
    print(result["path"])


__all__ = ["main"]