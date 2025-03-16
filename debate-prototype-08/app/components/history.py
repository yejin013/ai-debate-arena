import streamlit as st
import requests
import json
from utils.state_manager import reset_session_state, set_debate_to_state

# API 엔드포인트 기본 URL
API_BASE_URL = "http://localhost:8000/api/v1"


def fetch_debate_history():
    """API를 통해 토론 이력 가져오기"""
    try:
        response = requests.get(f"{API_BASE_URL}/debates/")
        if response.status_code == 200:
            debates = response.json()
            # API 응답 형식에 맞게 데이터 변환 (id, topic, date, rounds)
            return [
                (debate["id"], debate["topic"], debate["created_at"], debate["rounds"])
                for debate in debates
            ]
        else:
            st.error(f"토론 이력 조회 실패: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"API 호출 오류: {str(e)}")
        return []


def fetch_debate_by_id(debate_id):
    """API를 통해 특정 토론 데이터 가져오기"""
    try:
        response = requests.get(f"{API_BASE_URL}/debates/{debate_id}")
        if response.status_code == 200:
            debate = response.json()
            topic = debate["topic"]
            # 실제 API 응답 구조에 맞게 변환 필요
            messages = (
                json.loads(debate["messages"])
                if isinstance(debate["messages"], str)
                else debate["messages"]
            )
            docs = (
                json.loads(debate["retrieved_docs"])
                if isinstance(debate["retrieved_docs"], str)
                else debate.get("retrieved_docs", {})
            )
            return topic, messages, docs
        else:
            st.error(f"토론 데이터 조회 실패: {response.status_code}")
            return None, None, None
    except Exception as e:
        st.error(f"API 호출 오류: {str(e)}")
        return None, None, None


def delete_debate_by_id(debate_id):
    """API를 통해 특정 토론 삭제"""
    try:
        response = requests.delete(f"{API_BASE_URL}/debates/{debate_id}")
        if response.status_code == 200:
            st.success("토론이 삭제되었습니다.")
            return True
        else:
            st.error(f"토론 삭제 실패: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"API 호출 오류: {str(e)}")
        return False


def delete_all_debates():
    """API를 통해 모든 토론 삭제"""
    try:
        # 모든 토론 목록 조회
        debates = fetch_debate_history()
        if not debates:
            return True

        # 각 토론 항목 삭제
        success = True
        for debate_id, _, _, _ in debates:
            response = requests.delete(f"{API_BASE_URL}/debates/{debate_id}")
            if response.status_code != 200:
                success = False

        if success:
            st.success("모든 토론이 삭제되었습니다.")
        return success
    except Exception as e:
        st.error(f"API 호출 오류: {str(e)}")
        return False


def render_history_tab():
    st.subheader("이전 토론 이력")

    col1, col2 = st.columns([1, 1])

    # 이력 새로고침 버튼
    with col1:
        if st.button("이력 새로고침", use_container_width=True):
            st.rerun()

    # 전체 이력 삭제 버튼
    with col2:
        if st.button("전체 이력 삭제", type="primary", use_container_width=True):
            if delete_all_debates():
                st.rerun()

    debate_history = fetch_debate_history()

    if not debate_history:
        st.info("저장된 토론 이력이 없습니다.")
    else:
        render_history_list(debate_history)


def render_history_list(debate_history):
    for id, topic, date, rounds in debate_history:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])

            # 토론 정보
            with col1:
                st.write(f"***{topic}***")
                st.caption(f"날짜: {date} | 라운드: {rounds}")

            # 보기 버튼
            with col2:
                if st.button("보기", key=f"view_{id}", use_container_width=True):
                    load_debate_view(id)

            # 삭제 버튼
            with col3:
                if st.button("삭제", key=f"del_{id}", use_container_width=True):
                    if delete_debate_by_id(id):
                        reset_session_state()
                        st.rerun()


def load_debate_view(debate_id):
    # API를 통해 토론 데이터 로딩
    topic, messages, docs = fetch_debate_by_id(debate_id)
    if topic and messages:
        # 세션 스테이트에 토론 데이터 로드
        set_debate_to_state(topic, messages, debate_id, docs)
        st.rerun()
