import streamlit as st


def init_session_state():
    if "app_mode" not in st.session_state:
        reset_session_state()


def reset_session_state():
    st.session_state.app_mode = "input"  # app 진행 상태
    st.session_state.round = 1  # 현재 라운드
    st.session_state.max_rounds = 1  # 총 라운드 수
    st.session_state.messages = []  # 토론 메세지 리스트
