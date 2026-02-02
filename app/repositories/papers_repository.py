from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import select, literal
from sqlalchemy.orm import Session

from app.models.papers import Papers
from app.models.extractions import Extractions
from app.models.evaluations import Evaluations
from app.models.agents_logs import AgentLogs


def find_similar_papers(
    db: Session,
    *,
    embedding: Sequence[float],
    limit: int = 10,
    min_similarity: float | None = None,
) -> list[dict[str, Any]]:
    # 핵심: embedding을 문자열로 만들지 말고, "그대로" 바인딩
    embedding_vector = list(map(float, embedding))
    distance = Papers.embedding.cosine_distance(embedding_vector)
    similarity = (literal(1.0) - distance).label("similarity")

    query = (
        select(
            Papers.id,
            Papers.title,
            Papers.authors,
            Papers.journal,
            Papers.year,
            Papers.abstract,
            Papers.pdf_url,
            Papers.ingestion_source,
            Papers.ingestion_timestamp,
            similarity,
        )
        .where(Papers.embedding.isnot(None))
        .order_by(distance)
        .limit(int(limit))
    )

    if min_similarity is not None:
        query = query.where(similarity >= float(min_similarity))

    result = db.execute(query)
    return [dict(row) for row in result.mappings().all()]


def list_papers(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[Papers]:
    query = select(Papers).offset(int(offset)).limit(int(limit))
    result = db.execute(query)
    return result.scalars().all()


def create_paper(
    db: Session,
    *,
    title: str,
    authors: list[str] | None = None,
    journal: str | None = None,
    year: int | None = None,
    abstract: str | None = None,
    pdf_url: str | None = None,
    ingestion_source: str | None = None,
    embedding: list[float] | None = None,
) -> Papers:
    paper = Papers(
        title=title,
        authors=authors or [],
        journal=journal,
        year=year,
        abstract=abstract,
        pdf_url=pdf_url,
        ingestion_source=ingestion_source,
        embedding=embedding,
    )
    db.add(paper)
    db.flush()
    return paper


def create_extraction(
    db: Session,
    *,
    paper_id,
    extraction_version: str,
    metadata_jsonb: dict | None = None,
    study_design_jsonb: dict | None = None,
    sample_jsonb: dict | None = None,
    outcomes_jsonb: dict | None = None,
    risk_of_bias_jsonb: dict | None = None,
    status: str = "success",
) -> Extractions:
    extraction = Extractions(
        paper_id=paper_id,
        extraction_version=extraction_version,
        metadata_jsonb=metadata_jsonb,
        study_design_jsonb=study_design_jsonb,
        sample_jsonb=sample_jsonb,
        outcomes_jsonb=outcomes_jsonb,
        risk_of_bias_jsonb=risk_of_bias_jsonb,
        status=status,
    )
    db.add(extraction)
    db.flush()
    return extraction


def create_evaluation(
    db: Session,
    *,
    extraction_id,
    evaluator_id: str,
    agreement_scores: dict | None = None,
    notes: str | None = None,
) -> Evaluations:
    evaluation = Evaluations(
        extraction_id=extraction_id,
        evaluator_id=evaluator_id,
        agreement_scores=agreement_scores,
        notes=notes,
    )
    db.add(evaluation)
    db.flush()
    return evaluation


def create_agent_log(
    db: Session,
    *,
    agent_name: str,
    paper_id=None,
    extraction_id=None,
    raw_output: str | None = None,
    cleaned_output: dict | None = None,
    input_text: str | None = None,
    node_name: str | None = None,
    prompt_hash: str | None = None,
    model_name: str | None = None,
) -> AgentLogs:
    log = AgentLogs(
        paper_id=paper_id,
        extraction_id=extraction_id,
        agent_name=agent_name,
        raw_output=raw_output,
        cleaned_output=cleaned_output,
        input=input_text,
        node_name=node_name,
        prompt_hash=prompt_hash,
        model_name=model_name,
    )
    db.add(log)
    db.flush()
    return log
