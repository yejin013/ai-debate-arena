import uuid
import streamlit as st

from utils.state_manager import reset_session_state
from database.repository import save_debate_to_db
from workflow.graph import create_debate_graph
from workflow.state import AgentType, DebateState
from langfuse.callback import CallbackHandler


def render_start_view():
    if st.button("토론 시작"):
        start_debate()


def start_debate():

    debate_topic = st.session_state.ui_debate_topic
    max_rounds = st.session_state.ui_max_rounds
    enable_rag = st.session_state.ui_enable_rag  # RAG 기능 활성화 여부

    session_id = str(uuid.uuid4())
    debate_graph = create_debate_graph(enable_rag, session_id)

    initial_state: DebateState = {
        "topic": debate_topic,
        "messages": [],
        "current_round": 1,
        "prev_node": AgentType.PRO,
        "max_rounds": max_rounds,
        "retrieved_docs": {},
    }

    # 토론 시작
    debate_topic = st.session_state.ui_debate_topic
    st.subheader(f"주제: {debate_topic}")

    with st.spinner("토론이 진행 중입니다... 완료까지 잠시 기다려주세요."):

        langfuse_handler = CallbackHandler(session_id=session_id)

        displayed_messages = set()

        for chunk in debate_graph.stream(
            initial_state,
            config={"callbacks": [langfuse_handler]},
        ):
            if chunk:
                for role, state in chunk.items():
                    st.session_state.debate_messages = state["messages"]
                    st.session_state.retrieved_docs = state["retrieved_docs"]

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
                        st.session_state.debate_active = True
                        st.session_state.viewing_history = False

                        save_debate_to_db(
                            debate_topic,
                            max_rounds,
                            state["messages"],
                            state["retrieved_docs"],  # RAG 결과 저장
                        )
                        # RAG 외부 지식 검색 결과 표시
                        if st.session_state.ui_enable_rag:
                            render_source_materials()

                        render_control_buttons()


def render_debate_view():

    if st.session_state.viewing_history:
        st.info("📚 이전에 저장된 토론을 보고 있습니다.")
        debate_topic = st.session_state.debate_topic
    else:
        debate_topic = st.session_state.ui_debate_topic

    st.subheader(f"주제: {debate_topic}")

    for message in st.session_state["debate_messages"]:
        if message["role"] == AgentType.PRO:
            avatar = "🙆🏻‍♀️"
        elif message["role"] == AgentType.CON:
            avatar = "🙅🏻‍♂"
        elif message["role"] == AgentType.JUDGE:
            avatar = "👩🏻‍⚖️"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
    # RAG 외부 지식 검색 결과 표시
    if st.session_state.ui_enable_rag:
        render_source_materials()

    render_control_buttons()


def render_control_buttons():
    col1, col2 = st.columns(2)

    with col1:
        if st.button("새 토론 시작", use_container_width=True):
            reset_session_state()
            st.rerun()

    if st.session_state.viewing_history and st.session_state.loaded_debate_id:
        with col2:
            if st.button("현재 토론 삭제", use_container_width=True, type="secondary"):
                delete_current_debate()


def delete_current_debate():
    from database.repository import delete_debate_by_id

    if (
        st.session_state.viewing_history
        and st.session_state.loaded_debate_id
        and delete_debate_by_id(st.session_state.loaded_debate_id)
    ):
        st.success("토론이 삭제되었습니다.")
        reset_session_state()
        st.rerun()
    else:
        st.error("토론 삭제에 실패했습니다.")


def render_source_materials():
    if st.session_state.retrieved_docs and (
        st.session_state.retrieved_docs.get(AgentType.PRO)
        or st.session_state.retrieved_docs.get(AgentType.CON)
    ):
        with st.expander("사용된 참고 자료 보기"):
            st.subheader("찬성 측 참고 자료")
            for i, doc in enumerate(
                st.session_state.retrieved_docs.get(AgentType.PRO, [])[:3]
            ):
                st.markdown(f"**문서 {i+1}**")
                st.text(doc[:300] + "..." if len(doc) > 300 else doc)
                st.divider()

            st.subheader("반대 측 참고 자료")
            for i, doc in enumerate(
                st.session_state.retrieved_docs.get(AgentType.CON, [])[:3]
            ):
                st.markdown(f"**문서 {i+1}**")
                st.text(doc[:300] + "..." if len(doc) > 300 else doc)
                st.divider()

            st.subheader("심판 측 참고 자료")
            for i, doc in enumerate(
                st.session_state.retrieved_docs.get(AgentType.JUDGE, [])[:3]
            ):
                st.markdown(f"**문서 {i+1}**")
                st.text(doc[:300] + "..." if len(doc) > 300 else doc)
                st.divider()
