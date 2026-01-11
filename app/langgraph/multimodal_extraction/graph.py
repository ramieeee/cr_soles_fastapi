from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.langgraph.multimodal_extraction.nodes.metadata import (
    extract_metadata,
    prepare_retry,
    should_retry,
)
from app.langgraph.multimodal_extraction.nodes.ocr import run_ocr
from app.langgraph.multimodal_extraction.state import DocumentState


def build_document_graph():
    graph = StateGraph(DocumentState)
    graph.add_node("ocr", run_ocr)
    graph.add_node("extract_metadata", extract_metadata)
    graph.add_node("prepare_retry", prepare_retry)

    graph.set_entry_point("ocr")
    graph.add_edge("ocr", "extract_metadata")
    graph.add_conditional_edges(
        "extract_metadata",
        should_retry,
        {"retry": "prepare_retry", "end": END},
    )
    graph.add_edge("prepare_retry", "extract_metadata")
    return graph.compile()


@lru_cache(maxsize=1)
def get_document_graph():
    return build_document_graph()
