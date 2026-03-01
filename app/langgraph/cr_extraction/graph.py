from functools import lru_cache

from langgraph.graph import END, StateGraph, START
from app.langgraph.cr_extraction.state import CrExtractionState
from app.langgraph.cr_extraction.nodes.population_node import population_node
from app.langgraph.cr_extraction.nodes.validation_node import validation_node
from app.langgraph.cr_extraction.nodes.instrument_node import (
    instrument_node,
)
from app.langgraph.cr_extraction.nodes.reduce_node import reduce_node


def _route_after_validation(state: CrExtractionState) -> str:
    if state.get("cr_operationalization"):
        return "reduce"
    return "instrument_node"


def build_cr_extraction_graph():
    graph = StateGraph(CrExtractionState)
    graph.add_node("population_node", population_node)
    graph.add_node("validation_node", validation_node)
    graph.add_node("instrument_node", instrument_node)
    graph.add_node("reduce", reduce_node)

    graph.add_edge(START, "population_node")
    graph.add_edge("population_node", "validation_node")
    graph.add_conditional_edges(
        "validation_node",
        _route_after_validation,
        {
            "instrument_node": "instrument_node",
            "reduce": "reduce",
        },
    )
    graph.add_edge("instrument_node", "validation_node")
    graph.add_edge("reduce", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_cr_extraction_graph():
    return build_cr_extraction_graph()
