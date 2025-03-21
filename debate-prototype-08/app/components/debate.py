import streamlit as st
import requests
import json

from utils.state_manager import reset_session_state


# API 엔드포인트 설정
API_BASE_URL = "http://localhost:8000/api/v1"


class AgentType:
    PRO = "PRO_AGENT"
    CON = "CON_AGENT"
    JUDGE = "JUDGE_AGENT"


# API를 통해 토론 결과를 데이터베이스에 저장
def save_debate_to_db(topic, rounds, messages, docs=None):
    """API를 통해 토론 결과를 데이터베이스에 저장"""
    try:
        # API 요청 데이터 준비
        debate_data = {
            "topic": topic,
            "rounds": rounds,
            "messages": (
                json.dumps(messages) if not isinstance(messages, str) else messages
            ),
            "docs": (
                json.dumps(docs)
                if docs and not isinstance(docs, str)
                else (docs or "{}")
            ),
        }

        response = requests.post(f"{API_BASE_URL}/debates/", json=debate_data)

        if response.status_code == 200 or response.status_code == 201:
            st.success("토론이 성공적으로 저장되었습니다.")
            return response.json().get("id")  # 저장된 토론 ID 반환
        else:
            st.error(f"토론 저장 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"API 호출 오류: {str(e)}")
        return None
