import platform

from subprocess import run
from typing import Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class BashInput(BaseModel):
    """Commands for the Bash Shell tool."""

    command: str = Field(
        description=f"Bash shell command to run on this {platform.system()} system. Output will be truncated to 1024 characters, so make sure you extract the output you need. The command will be killed after 10 seconds."
    )
    reason: str = Field(
        description="One-sentence reason (up to 140 chars) for running the command."
    )


class BashTool(BaseTool):
    name: str = "BashTool"
    description: str = "Runs a bash command"
    args_schema: Type[BaseModel] = BashInput

    def _run(self, command: str, reason: str) -> str:
        print(f"## {reason}")
        print(f"{command}")
        # run command in a shell and capture stdout and stderr
        process = run(
            ["/usr/bin/timeout", "-s", "9", "10", "/bin/bash", "-c", command],
            capture_output=True,
        )
        stdout = process.stdout.decode("utf-8")
        stderr = process.stderr.decode("utf-8")
        trunc_limit = 1024
        stdout_truncated = len(stdout) > trunc_limit
        stderr_truncated = len(stderr) > trunc_limit
        # timedout when it got killed by 9
        timeout = process.returncode == 137
        result = {
            "stdout": stdout[:trunc_limit],
            "stdout_truncated": stdout_truncated,
            "stderr": stderr[:trunc_limit],
            "stderr_truncated": stderr_truncated,
            "returncode": process.returncode,
            "timeout": timeout,
        }
        print(result)
        return str(result)
