import tempfile
import time

from subprocess import run, TimeoutExpired
from typing import Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class Z3Input(BaseModel):
    """SMTLIB formula for solving with Z3."""

    formula: str = Field(
        description=f"SMTLIB formula to be solved using Z3, default timeout is 10 seconds."
    )


class Z3Tool(BaseTool):
    name: str = "Z3Tool"
    description: str = "Solves SMTLIB formulas using Z3"
    args_schema: Type[BaseModel] = Z3Input

    def _run(self, formula: str) -> str:
        print(f"{formula}")
        # store formula in a temporary file and run z3 on it
        with tempfile.NamedTemporaryFile(mode="w") as form_file:
            form_file.write(formula)
            form_file.flush()
            now = time.time()
            try:
                process = run(["z3", "-smt2", form_file.name], capture_output=True, timeout=10)
            except TimeoutExpired:
                return {"result": "timeout", "time": 10}
            elapsed = time.time() - now
            stdout = process.stdout.decode("utf-8")
            result = {
                "result": stdout,
                "time": elapsed,
            }
            print(result)
            return result
