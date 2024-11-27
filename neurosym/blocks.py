## Sample building blocks for building neurosym tools.
## Example taken from:
## https://github.com/langchain-ai/langgraph-example/blob/main/my_agent/agent.py

import json
import jsonschema
import os

from functools import lru_cache, partial
from typing import TypedDict, Annotated, Sequence, Literal, List, Optional, Tuple, Any

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langgraph.graph import add_messages, StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.errors import GraphRecursionError


class NotFoundError(Exception):
    pass


NEUROSYM_DEFAULT_MODEL = os.environ.get("NEUROSYM_DEFAULT_MODEL", "gpt-4o-mini")


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Define the config
class GraphConfig(TypedDict):
    model_name: Literal["openai"]  # other models can be added here


# Define the function that determines whether to continue using tools
# or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there are no tool calls, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


SYSTEM_PROMPT = os.environ.get("NEUROSYM_SYSTEM_PROMPT", "Solve the task you were provided. You can run as many actions as necessary to solve the problem. You can use all tools at your disposal. Do not use a tool if you do not need it. Note that all commands you invoke have to be **'one-shot'**, in other words you **can't launch interactive sessions** because you are running within an llm chain.")


# Define the function that calls the model
def call_model(state, config, model):
    messages = state["messages"]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define the function that calls the model
def call_postprocess(state, config, model, schema):
    messages = state["messages"]
    messages = [{
        "role": "system",
        "content": f"Convert the data to the jsonschema you will be provided with. Emit only json data, nothing else. The schema is: {schema}"
    }] + messages
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


def agent_tool_loop(toolbox, schema):
    """
    Basic neurosym while loop iterating over a toolbox
    by calling an agent to decide whether to continue or end.
    """
    # set_debug(True)

    # Define a new graph
    workflow = StateGraph(AgentState, config_schema=GraphConfig)
    toolnode = ToolNode(toolbox)

    # Define the model / only OpenAI for now, can be configured
    model = ChatOpenAI(temperature=0, model_name=NEUROSYM_DEFAULT_MODEL)
    model = model.bind_tools(toolbox)
    agentnode = partial(call_model, model=model)

    # Define the two nodes we will cycle between
    workflow.add_node("agent", agentnode)
    workflow.add_node("action", toolnode)

    # Define a post-processing node
    postprocessmodel = ChatOpenAI(temperature=0, model_name=NEUROSYM_DEFAULT_MODEL)
    postprocessnode = partial(call_postprocess, model=postprocessmodel, schema=schema)
    workflow.add_node("postprocess", postprocessnode)

    # Set the entrypoint as `agent`
    # This means that this node is the first one called
    workflow.set_entry_point("agent")

    # We now add a conditional edge
    workflow.add_conditional_edges(
        # First, we define the start node. We use `agent`.
        # This means these are the edges taken after the `agent` node is called.
        "agent",
        # Next, we pass in the function that will determine which node is called next.
        should_continue,
        # Finally we pass in a mapping.
        # The keys are strings, and the values are other nodes.
        # END is a special node marking that the graph should finish.
        # What will happen is we will call `should_continue`, and then the output of that
        # will be matched against the keys in this mapping.
        # Based on which one it matches, that node will then be called.
        {
            # If `tools`, then we call the tool node.
            "continue": "action",
            # Otherwise we finish.
            "end": "postprocess",
        },
    )

    # We now add a normal edge from `tools` to `agent`.
    # This means that after `tools` is called, `agent` node is called next.
    workflow.add_edge("action", "agent")

    # Finish it off by adding an edge from `postprocess` to `END`.
    workflow.add_edge("postprocess", END)

    # Finally, we compile it!
    # This compiles it into a LangChain Runnable,
    # meaning you can use it as you would any other runnable
    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)
    return graph


DEFAULT_SCHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "result": {
      "type": "string"
    }
  },
  "required": ["result"],
  "additionalProperties": False
}


def while_loop(prompt: str, toolbox: List[Any], max_iterations=10, schema=None) -> Optional[Tuple[Any, List[BaseMessage]]]:
    """Run the following tools in a loop up to max_iterations and return the result as a string."""
    if schema is None:
        schema = DEFAULT_SCHEMA

    program = agent_tool_loop(toolbox, schema)
    try:
        final_state = program.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"configurable": {"thread_id": 42}, "recursion_limit": max_iterations},
        )
        results = final_state["messages"]
        result = json.loads(results[-1].content)
        jsonschema.validate(result, schema)
        return result, results
    except GraphRecursionError:
        return None
