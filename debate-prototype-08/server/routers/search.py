from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel

# 기존 검색 서비스를 활용하기 위한 임포트 경로 설정
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from retrieval.search_service import get_search_content

router = APIRouter(prefix="/api/v1", tags=["search"])


class SearchResult(BaseModel):
    content: str
    source: str
    topic: str
    query: str


@router.get("/search/", response_model=List[SearchResult])
def search(
    topic: str,
    language: str = "ko",
    search_type: str = Query("general", enum=["pro", "con", "general"]),
    max_results: int = 5,
):
    """주제에 대한 검색 결과를 제공합니다"""
    documents = get_search_content(
        topic=topic, language=language, search_type=search_type, max_results=max_results
    )

    results = []
    for doc in documents:
        results.append(
            SearchResult(
                content=doc.page_content,
                source=doc.metadata.get("source", ""),
                topic=doc.metadata.get("topic", ""),
                query=doc.metadata.get("query", ""),
            )
        )

    return results
