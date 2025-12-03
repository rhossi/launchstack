
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

def graph():
    graph = StateGraph(State)
    graph.add_edge(START, END)
    return graph.compile()
