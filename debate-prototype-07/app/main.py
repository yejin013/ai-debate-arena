import uuid
import streamlit as st
from components.sidebar import render_sidebar
from workflow.state import AgentType, DebateState
from workflow.graph import create_debate_graph
from database.session import db_session
from utils.state_manager import init_session_state, reset_session_state
from database.repository import debate_repository
from langfuse.callback import CallbackHandler


def render_input_form():

    with st.form("debate_form", border=False):
        # 토론 주제 입력
        st.text_input(
            label="토론 주제를 입력하세요:",
            value="인공지능은 인간의 일자리를 대체할 수 있습니다.",
            key="ui_topic",
        )

        max_rounds = st.slider("토론 라운드 수", min_value=1, max_value=5, value=1)
        st.session_state.max_rounds = max_rounds
        st.form_submit_button(
            "토론 시작",
            on_click=lambda: st.session_state.update({"app_mode": "debate"}),
        )


def start_debate():

    topic = st.session_state.ui_topic
    max_rounds = st.session_state.max_rounds

    enabled_rag = st.session_state.get("ui_enable_rag", False)
    # 그래프 생성
    debate_graph = create_debate_graph(enabled_rag)

    # 초기 상태 설정
    initial_state: DebateState = {
        "topic": topic,
        "messages": [],
        "current_round": 1,
        "max_rounds": max_rounds,
        "prev_node": "START",  # 이전 노드 START로 설정
        "docs": {},  # RAG 결과 저장
    }

    # 토론 시작
    with st.spinner("토론이 진행 중입니다... 완료까지 잠시 기다려주세요."):

        session_id = str(uuid.uuid4())
        langfuse_handler = CallbackHandler(session_id=session_id)

        displayed_messages = set()

        for chunk in debate_graph.stream(
            initial_state,
            config={"callbacks": [langfuse_handler]},
        ):
            if chunk:
                for role, state in chunk.items():
                    st.session_state.messages = state["messages"]
                    st.session_state.docs = state["docs"]

                    for message in state["messages"]:

                        if role not in [
                            AgentType.PRO,
                            AgentType.CON,
                            AgentType.JUDGE,
                        ]:
                            continue

                        msg_id = f"{message['current_round']}_{message['role']}"
                        if msg_id in displayed_messages:
                            continue

                        if message["role"] == AgentType.PRO:
                            avatar = "🙆🏻‍♀️"
                        elif message["role"] == AgentType.CON:
                            avatar = "🙅🏻‍♂"
                        elif message["role"] == AgentType.JUDGE:
                            avatar = "👩🏻‍⚖️"
                        with st.chat_message(message["role"], avatar=avatar):
                            st.markdown(message["content"])

                        displayed_messages.add(msg_id)
                    if role == AgentType.JUDGE:
                        st.session_state.app_mode = "results"
                        st.session_state.viewing_history = False

                        # 토론 결과 저장 (docs 추가)
                        debate_repository.save(
                            topic,
                            max_rounds,
                            state["messages"],
                            state["docs"],  # RAG 결과 저장
                        )

    # 토론 결과 모드로 전환
    st.session_state.app_mode = "results"
    st.rerun()


# 참고 자료 표시
def render_source_materials():

    with st.expander("사용된 참고 자료 보기"):
        st.subheader("찬성 측 참고 자료")
        for i, doc in enumerate(st.session_state.docs.get(AgentType.PRO, [])[:3]):
            st.markdown(f"**문서 {i+1}**")
            st.text(doc[:300] + "..." if len(doc) > 300 else doc)
            st.divider()

        st.subheader("반대 측 참고 자료")
        for i, doc in enumerate(st.session_state.docs.get(AgentType.CON, [])[:3]):
            st.markdown(f"**문서 {i+1}**")
            st.text(doc[:300] + "..." if len(doc) > 300 else doc)
            st.divider()

        st.subheader("심판 측 참고 자료")
        for i, doc in enumerate(st.session_state.docs.get(AgentType.JUDGE, [])[:3]):
            st.markdown(f"**문서 {i+1}**")
            st.text(doc[:300] + "..." if len(doc) > 300 else doc)
            st.divider()


def display_debate_results():

    if st.session_state.viewing_history:
        st.info("📚 이전에 저장된 토론을 보고 있습니다.")
        topic = st.session_state.loaded_topic
    else:
        topic = st.session_state.ui_topic

    # 토론 주제 표시
    st.header(f"토론 주제: {topic}")

    for message in st.session_state.messages:

        role = message["role"]
        if role not in [
            AgentType.PRO,
            AgentType.CON,
            AgentType.JUDGE,
        ]:
            continue

        if message["role"] == AgentType.PRO:
            avatar = "🙆🏻‍♀️"
        elif message["role"] == AgentType.CON:
            avatar = "🙅🏻‍♂"
        elif message["role"] == AgentType.JUDGE:
            avatar = "👩🏻‍⚖️"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    if role == AgentType.JUDGE:
        st.session_state.debate_active = True
        st.session_state.viewing_history = False

    # 참고 자료 표시
    if st.session_state.docs:
        render_source_materials()

    if st.button("새 토론 시작"):
        reset_session_state()
        st.session_state.app_mode = "input"
        st.rerun()


def render_ui():
    # 페이지 설정
    st.set_page_config(page_title="AI 토론", page_icon="🤖")

    # 제목 및 소개
    st.title("🤖 AI 토론 - 멀티 에이전트")
    st.markdown(
        """
        ### 프로젝트 소개
        이 애플리케이션은 3개의 AI 에이전트(찬성, 반대, 심판)가 사용자가 제시한 주제에 대해 토론을 진행합니다.
        각 AI는 서로의 의견을 듣고 반박하며, 마지막에는 심판 AI가 토론 결과를 평가합니다.
        """
    )

    render_sidebar()

    current_mode = st.session_state.get("app_mode")

    if current_mode == "debate":
        start_debate()
    if current_mode == "results":
        display_debate_results()


if __name__ == "__main__":
    # 세션 상태 초기화
    init_session_state()

    db_session.initialize()

    render_ui()
