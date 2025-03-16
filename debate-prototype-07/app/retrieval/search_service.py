import streamlit as st
from langchain.schema import Document
from typing import List, Literal
from retrieval.query_generator import improve_search_query
from duckduckgo_search import DDGS


def get_search_content(
    topic: str,
    language: str = "ko",
    search_type: Literal["pro", "con", "general"] = "general",
    max_results: int = 5,
) -> List[Document]:
    """
    DuckDuckGo 검색 엔진을 사용하여 주제에 관한 정보를 검색합니다.
    """
    try:
        # LLM을 사용하여 검색어 개선
        improved_queries = improve_search_query(topic, search_type, language)
        documents = []

        ddgs = DDGS()

        # 각 개선된 검색어에 대해 검색 수행
        for query in improved_queries:
            try:
                # 검색 수행
                results = ddgs.text(
                    query,
                    region=language if language in ["us", "uk", "kr"] else "kr",
                    safesearch="moderate",
                    timelimit="y",  # 최근 1년 내 결과
                    max_results=max_results,
                )

                print(query)

                if not results:
                    continue

                # 검색 결과 처리
                for result in results:
                    title = result.get("title", "")
                    body = result.get("body", "")
                    url = result.get("href", "")

                    print(title)
                    if body:
                        documents.append(
                            Document(
                                page_content=body,
                                metadata={
                                    "source": url,
                                    "section": "content",
                                    "topic": title,
                                    "query": query,
                                },
                            )
                        )

            except Exception as e:
                st.warning(f"검색 중 오류 발생: {str(e)}")

        return documents

    except Exception as e:
        st.error(f"검색 서비스 오류 발생: {str(e)}")
        return []
