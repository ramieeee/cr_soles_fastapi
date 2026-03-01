from functools import lru_cache

from langgraph.graph import END, StateGraph, START
from app.langgraph.cr_extraction.state import CrExtractionState
from app.langgraph.cr_extraction.nodes.population_node import population_node
from app.langgraph.cr_extraction.nodes.instrument_router_node import (
    instrument_router_node,
)
from app.langgraph.cr_extraction.nodes.reduce_node import reduce_node


def build_cr_extraction_graph():
    graph = StateGraph(CrExtractionState)
    graph.add_node("population_node", population_node)
    graph.add_node("instrument_router_node", instrument_router_node)
    graph.add_node("reduce", reduce_node)

    graph.add_edge(START, "population_node")
    graph.add_edge("population_node", "instrument_router_node")
    graph.add_edge("instrument_router_node", "reduce")
    graph.add_edge("reduce", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_cr_extraction_graph():
    return build_cr_extraction_graph()
