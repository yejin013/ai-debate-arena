import streamlit as st
from langchain_community.vectorstores import FAISS
from typing import Any, Dict, Optional, List
from workflow.config import get_embeddings
from app.retrieval.search_service import get_search_content
from langchain_core.documents import Document


@st.cache_data
def retrieve_documents(topic: str, language: str = "ko") -> List[Document]:
    documents = []
    wiki_docs = get_search_content(topic, language)
    if wiki_docs:
        documents.extend(wiki_docs)

    return documents


def create_vector_store(documents: List[Document]) -> Optional[FAISS]:
    if not documents:
        return None
    try:
        vector_store = FAISS.from_documents(documents, get_embeddings())
        return vector_store
    except Exception as e:
        st.error(f"Vector DB 생성 중 오류 발생: {str(e)}")
        return None


@st.cache_resource
def _get_topic_vector_store(topic: str) -> Optional[FAISS]:
    documents = retrieve_documents(topic)
    return create_vector_store(documents)


def search_topic(topic: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
    vector_store = _get_topic_vector_store(topic)
    if not vector_store:
        return []

    try:
        results = vector_store.similarity_search(query, k=k)
        return results
    except Exception as e:
        st.error(f"검색 중 오류 발생: {str(e)}")
        return []
