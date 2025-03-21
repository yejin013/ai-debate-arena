import json
import requests
import streamlit as st
from app.components.debate import API_BASE_URL, AgentType, save_debate_to_db
from components.sidebar import render_sidebar
from utils.state_manager import init_session_state, reset_session_state


def display_message(message, displayed_messages):
    agent_type = message.get("role", "")
    role = agent_type
    current_round = message.get("round", 0)

    if agent_type not in [AgentType.PRO, AgentType.CON, AgentType.JUDGE]:
        return False

    msg_id = f"{current_round}_{role}"

    # 이미 표시된 메시지인 경우 무시
    if msg_id in displayed_messages:
        return False

    if role == AgentType.PRO:
        avatar = "🙆🏻‍♀️"
    elif role == AgentType.CON:
        avatar = "🙅🏻‍♂"
    elif role == AgentType.JUDGE:
        avatar = "👩🏻‍⚖️"

    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

    return msg_id


def check_debate_complete(all_messages, topic, max_rounds, docs):

    if any(m.get("role") == AgentType.JUDGE for m in all_messages):
        st.session_state.debate_active = True
        st.session_state.viewing_history = False

        # 완료된 토론 정보 저장
        save_debate_to_db(
            topic,
            max_rounds,
            all_messages,
            docs,
        )

        # 참고 자료 표시
        if st.session_state.docs:
            render_source_materials()

        if st.button("새 토론 시작"):
            reset_session_state()
            st.session_state.app_mode = "input"
            st.rerun()

        return True

    return False


def process_event_data(event_data, debate_topic, max_rounds, displayed_messages):

    # 이벤트 종료
    if event_data.get("type") == "end":
        return True, displayed_messages, {}, []

    # 새로운 메세지
    if event_data.get("type") == "update":

        # state 데이터 추출
        state_data = event_data.get("data", {})
        docs = {}
        all_messages = []

        # 메시지 및 문서 업데이트
        if "messages" in state_data:
            all_messages = state_data["messages"]
            st.session_state.debate_messages = all_messages

        # 검색된 문서 업데이트 (있을 경우)
        if "docs" in state_data:
            docs = state_data["docs"]
            st.session_state.docs = docs

        # 새 메시지 표시
        for message in all_messages:
            msg_id = display_message(message, displayed_messages)
            if msg_id:
                displayed_messages.add(msg_id)

        # 토론 완료 체크
        if check_debate_complete(all_messages, debate_topic, max_rounds, docs):
            return True, displayed_messages, docs, all_messages

    return False, displayed_messages, docs, all_messages


def process_streaming_response(response, debate_topic, max_rounds, displayed_messages):
    for chunk in response.iter_lines():
        if not chunk:
            continue

        # 'data: ' 접두사 제거
        line = chunk.decode("utf-8")

        # line의 형태는 'data: {"type": "update", "data": {}}'
        if not line.startswith("data: "):
            continue

        data_str = line[6:]  # 'data: ' 부분 제거

        try:
            # JSON 데이터 파싱
            event_data = json.loads(data_str)

            # 이벤트 데이터 처리
            is_complete, displayed_messages, _, _ = process_event_data(
                event_data, debate_topic, max_rounds, displayed_messages
            )

            if is_complete:
                break

        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {e}")


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

    # 토론 시작
    st.subheader(f"주제: {topic}")

    with st.spinner("토론이 진행 중입니다... 완료까지 잠시 기다려주세요."):
        # API 요청 데이터
        data = {
            "topic": topic,
            "max_rounds": max_rounds,
            "enable_rag": enabled_rag,
        }

        try:
            # 스트리밍 API 호출
            response = requests.post(
                f"{API_BASE_URL}/workflow/debate/stream",
                json=data,
                stream=True,
                headers={"Content-Type": "application/json"},
            )

            # stream=True로 설정하여 스트리밍 응답 처리
            # iter_lines() 또는 Iter_content()로 청크단위로 Read

            if response.status_code != 200:
                st.error(f"API 오류: {response.status_code} - {response.text}")
                return

            displayed_messages = set()

            # 스트리밍 응답 처리
            process_streaming_response(response, topic, max_rounds, displayed_messages)

        except requests.RequestException as e:
            st.error(f"API 요청 오류: {str(e)}")


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

    current_mode = st.session_state.app_mode

    if current_mode == "debate":
        start_debate()


if __name__ == "__main__":
    # 세션 상태 초기화
    init_session_state()

    render_ui()
