from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.langgraph.multimodal_extraction.nodes.metadata_node import (
    extract_metadata,
    prepare_retry,
    should_retry,
)
from app.langgraph.multimodal_extraction.nodes.ocr_node import run_ocr
from app.langgraph.multimodal_extraction.nodes.embedding_node import embed_data
from app.langgraph.multimodal_extraction.state import DocumentState


def build_document_graph():
    graph = StateGraph(DocumentState)
    graph.add_node("ocr", run_ocr)
    graph.add_node("extract_metadata", extract_metadata)
    graph.add_node("prepare_retry", prepare_retry)
    graph.add_node("embed", embed_data)

    graph.set_entry_point("ocr")
    graph.add_edge("ocr", "extract_metadata")
    graph.add_conditional_edges(
        "extract_metadata",
        should_retry,
        {"retry": "prepare_retry", "end": "embed"},
    )
    graph.add_edge("prepare_retry", "extract_metadata")
    graph.add_edge("embed", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_document_graph():
    return build_document_graph()
