from typing import TypedDict, List, Dict, Any, Optional


class InferenceStep(TypedDict):
    page: int
    focus: str  # what the model should focus on in this step, e.g. "population", "risk of bias", etc.
    memory: str  # relevant extracted info from previous steps to keep in context
    evidence: dict[str, Any]
    confidence: Optional[float]


class Evidence(TypedDict, total=False):
    page: int
    quote: str
    confidence: float


class Objects(TypedDict, total=False):
    population: Dict[str, Any]
    cr_operationalization: Dict[str, Any]
    biomarkers: Dict[str, Any]
    study_design: Dict[str, Any]
    outcomes: Dict[str, Any]


class CrExtractionState(TypedDict, total=False):

    # ---------- Input ----------
    paper_id: str
    pages_text: List[str]  # OCR cleaned text per page
    current_page_index: int

    # ---------- Core extracted objects ----------
    population: Dict[str, Any]
    cr_operationalization: Dict[str, Any]
    biomarkers: Dict[str, Any]
    study_design: Dict[str, Any]
    outcomes: Dict[str, Any]

    # ---------- Instrument routing ----------
    detected_instruments: List[str]
    instrument_routes_completed: List[str]

    # ---------- Proxy tall store ----------
    proxies_normalized: List[Dict[str, Any]]

    # ---------- Evidence store ----------
    evidence_store: Dict[str, List[Evidence]]

    # ---------- Confidence ----------
    field_confidence: Dict[str, float]
    global_confidence: float

    # ---------- Control flags ----------
    missing_fields: List[str]
    retry_focus: List[str]
    attempts: int
    max_attempts: int

    extraction_complete: bool

    # ---------- Versioning ----------
    extraction_version: str
