from functools import lru_cache

from langgraph.graph import END, StateGraph, START
from app.langgraph.cr_extraction.state import CrExtractionState
from app.langgraph.cr_extraction.nodes.cr_extraction_node import cr_extraction_node
from app.langgraph.cr_extraction.nodes.validation_node import validation_node
from app.langgraph.cr_extraction.nodes.reduce_node import reduce_node
from app.langgraph.cr_extraction.nodes.next_page_node import next_page_node
from app.langgraph.cr_extraction.nodes.stream_invoke_test import (
    stream_invoke_test1 as test_node1,
    stream_invoke_test2 as test_node2,
)


def _route_next(state: CrExtractionState) -> str:
    pages = state.get("pages_content") or []
    page_index = int(state.get("current_page_index") or 0)
    return "next_page" if page_index < (len(pages) - 1) else "reduce"


def build_cr_extraction_graph():
    graph = StateGraph(CrExtractionState)
    graph.add_node("stream_invoke_test1", test_node1)
    graph.add_node("stream_invoke_test2", test_node2)

    graph.add_edge(START, "stream_invoke_test1")
    graph.add_edge("stream_invoke_test1", "stream_invoke_test2")
    graph.add_edge("stream_invoke_test2", END)
    # graph.add_node("cr_extraction_node", cr_extraction_node)
    # graph.add_node("validation_node", validation_node)
    # graph.add_node("next_page", next_page_node)
    # graph.add_node("reduce", reduce_node)

    # graph.add_edge(START, "cr_extraction_node")
    # graph.add_edge("cr_extraction_node", "validation_node")
    # graph.add_conditional_edges(
    #     "validation_node",
    #     _route_next,
    #     {
    #         "next_page": "next_page",
    #         "reduce": "reduce",
    #     },
    # )
    # graph.add_edge("next_page", "cr_extraction_node")
    # graph.add_edge("reduce", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_cr_extraction_graph():
    return build_cr_extraction_graph()
