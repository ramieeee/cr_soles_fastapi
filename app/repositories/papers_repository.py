from __future__ import annotations

from typing import Any, Sequence

from pgvector.sqlalchemy import Vector  # 타입/바인딩 보조
from pgvector.psycopg import register_vector
from sqlalchemy import text
from sqlalchemy.orm import Session


def find_similar_papers(
    db: Session,
    *,
    embedding: Sequence[float],
    limit: int = 10,
    min_similarity: float | None = None,
) -> list[dict[str, Any]]:
    # 핵심: embedding을 문자열로 만들지 말고, "그대로" 바인딩
    sql = """
        SELECT
            id, title, authors, journal, year, abstract, pdf_url,
            ingestion_source, ingestion_timestamp,
            1 - (embedding <=> (:embedding)::vector) AS similarity
        FROM soles.papers
        WHERE embedding IS NOT NULL
    """

    params: dict[str, Any] = {
        "embedding": list(map(float, embedding)),
        "limit": int(limit),
    }

    if min_similarity is not None:
        sql += " AND (1 - (embedding <=> (:embedding)::vector)) >= :min_similarity"
        params["min_similarity"] = float(min_similarity)

    sql += " ORDER BY embedding <=> (:embedding)::vector LIMIT :limit"

    result = db.execute(text(sql), params)
    return [dict(row) for row in result.mappings().all()]
