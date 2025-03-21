import streamlit as st


def init_session_state():
    # 세션 스테이트 초기화
    if "app_mode" not in st.session_state:
        reset_session_state()


def reset_session_state():
    st.session_state.app_mode = "input"
    st.session_state.round = 0
    st.session_state.viewing_history = False  # 이력 보기 모드
