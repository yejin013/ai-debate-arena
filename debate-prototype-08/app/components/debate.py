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


def save_debate_to_db(topic, rounds, messages, retrieved_docs=None):
    """API를 통해 토론 결과를 데이터베이스에 저장"""
    try:
        # API 요청 데이터 준비
        debate_data = {
            "topic": topic,
            "rounds": rounds,
            "messages": (
                json.dumps(messages) if not isinstance(messages, str) else messages
            ),
            "retrieved_docs": (
                json.dumps(retrieved_docs)
                if retrieved_docs and not isinstance(retrieved_docs, str)
                else (retrieved_docs or "{}")
            ),
        }

        # API POST 요청
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


def delete_current_debate():
    """API를 통해 현재 토론 삭제"""
    if st.session_state.viewing_history and st.session_state.loaded_debate_id:
        try:
            # API DELETE 요청
            response = requests.delete(
                f"{API_BASE_URL}/debates/{st.session_state.loaded_debate_id}"
            )

            if response.status_code == 200:
                st.success("토론이 삭제되었습니다.")
                reset_session_state()
                st.rerun()
            else:
                st.error(f"토론 삭제 실패: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"API 호출 오류: {str(e)}")
    else:
        st.error("삭제할 토론이 선택되지 않았습니다.")


def display_message(message, displayed_messages):
    """개별 메시지 표시"""
    agent_type = message.get("role", "")
    role = agent_type
    current_round = message.get("round", 0)

    if agent_type not in [AgentType.PRO, AgentType.CON, AgentType.JUDGE]:
        return False

    msg_id = f"{current_round}_{role}"
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


def check_debate_complete(all_messages, topic, max_rounds, retrieved_docs):
    """토론 완료 여부 확인 및 처리"""
    if any(m.get("role") == AgentType.JUDGE for m in all_messages):
        st.session_state.debate_active = True
        st.session_state.viewing_history = False

        # 완료된 토론 정보 저장
        save_debate_to_db(
            topic,
            max_rounds,
            all_messages,
            retrieved_docs,
        )

        # RAG 결과 표시
        if st.session_state.ui_enable_rag:
            render_source_materials()

        render_control_buttons()
        return True

    return False


def process_event_data(event_data, debate_topic, max_rounds, displayed_messages):
    """이벤트 데이터 처리"""
    if event_data.get("type") == "end":
        return True, displayed_messages, {}, []

    if event_data.get("type") == "update":
        state_data = event_data.get("data", {})
        retrieved_docs = {}
        all_messages = []

        # 메시지 및 문서 업데이트
        if "messages" in state_data:
            all_messages = state_data["messages"]
            st.session_state.debate_messages = all_messages

        # 검색된 문서 업데이트 (있을 경우)
        if "retrieved_docs" in state_data:
            retrieved_docs = state_data["retrieved_docs"]
            st.session_state.retrieved_docs = retrieved_docs

        # 새 메시지 표시
        for message in all_messages:
            msg_id = display_message(message, displayed_messages)
            if msg_id:
                displayed_messages.add(msg_id)

        # 토론 완료 체크
        if check_debate_complete(
            all_messages, debate_topic, max_rounds, retrieved_docs
        ):
            return True, displayed_messages, retrieved_docs, all_messages

    return False, displayed_messages, retrieved_docs, all_messages


def start_debate():
    """토론 시작 및 실시간 진행"""
    debate_topic = st.session_state.ui_debate_topic
    max_rounds = st.session_state.ui_max_rounds
    enable_rag = st.session_state.ui_enable_rag  # RAG 기능 활성화 여부

    # 토론 시작
    st.subheader(f"주제: {debate_topic}")

    with st.spinner("토론이 진행 중입니다... 완료까지 잠시 기다려주세요."):
        # API 요청 데이터
        data = {
            "topic": debate_topic,
            "max_rounds": max_rounds,
            "enable_rag": enable_rag,
        }

        try:
            # 스트리밍 API 호출
            response = requests.post(
                f"{API_BASE_URL}/workflow/debate/stream",
                json=data,
                stream=True,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                st.error(f"API 오류: {response.status_code} - {response.text}")
                return

            displayed_messages = set()

            # 스트리밍 응답 처리
            process_streaming_response(
                response, debate_topic, max_rounds, displayed_messages
            )

        except requests.RequestException as e:
            st.error(f"API 요청 오류: {str(e)}")


def process_streaming_response(response, debate_topic, max_rounds, displayed_messages):
    """스트리밍 응답 처리"""
    for chunk in response.iter_lines():
        if not chunk:
            continue

        # 'data: ' 접두사 제거
        line = chunk.decode("utf-8")
        if not line.startswith("data: "):
            continue

        data_str = line[6:]  # 'data: ' 부분 제거

        try:
            event_data = json.loads(data_str)
            is_complete, displayed_messages, _, _ = process_event_data(
                event_data, debate_topic, max_rounds, displayed_messages
            )

            if is_complete:
                break

        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {e}")


def render_start_view():
    if st.button("토론 시작"):
        start_debate()


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
