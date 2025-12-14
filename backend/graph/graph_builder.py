# graph/graph_builder.py
"""
Graph Builder
-------------
Constructs the LangGraph state machine.
Defines the flow: Intent -> Planner -> Agents -> RAG -> Report.
"""

from langgraph.graph import StateGraph, END

from graph.state import AgentState
from graph.nodes.intent_node import intent_node
from graph.nodes.planner_node import planner_node
from graph.nodes.agent_node import agent_node
from graph.nodes.rag_node import rag_node
from graph.nodes.report_node import report_node


def _build_graph():
    """
    Builds the compiled StateGraph.
    """
    graph = StateGraph(AgentState)

    # 1. Add Nodes
    graph.add_node("intent", intent_node)
    graph.add_node("planner", planner_node)
    graph.add_node("agents", agent_node)
    graph.add_node("rag", rag_node)
    graph.add_node("report", report_node)

    # 2. Define Edges
    graph.set_entry_point("intent")
    graph.add_edge("intent", "planner")
    graph.add_edge("planner", "agents")
    graph.add_edge("agents", "rag")
    graph.add_edge("rag", "report")
    graph.add_edge("report", END)

    return graph.compile()


# Singleton graph instance
agent_graph = _build_graph()