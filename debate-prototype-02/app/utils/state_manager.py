import streamlit as st


def init_session_state():
    if "app_mode" not in st.session_state:
        reset_session_state()


def reset_session_state():
    st.session_state.app_mode = "input"
    st.session_state.round = 1
    st.session_state.max_rounds = 1
    st.session_state.messages = []
