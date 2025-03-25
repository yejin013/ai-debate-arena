import streamlit as st

from debate import handle_con_round, handle_judge, handle_pro_round
from utils.state_manager import init_session_state, reset_session_state


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

    # 폼 정의
    with st.form("debate_form", border=False):
        # 토론 주제 입력
        st.text_input(
            label="토론 주제를 입력하세요:",
            value="인공지능은 인간의 일자리를 대체할 수 있습니다.",
            key="ui_topic",
        )

        max_rounds = st.slider("토론 라운드 수", min_value=1, max_value=5, value=1)
        st.session_state.max_rounds = max_rounds
        # if st.form_submit_button("토론 시작"):
        #     start_debate()
        st.form_submit_button("토론 시작", on_click=start_debate)


# 토론 시작 함수 정의
def start_debate():

    # 토론 진행
    topic = st.session_state.ui_topic

    # 프로그레스 바를 위한 총 단계 계산 (각 라운드마다 찬성+반대+심판)
    total_steps = (
        st.session_state.max_rounds * 2 + 1
    )  # 각 라운드의 찬성, 반대 + 최종 심판
    current_step = 0
    progress_bar = st.progress(0)

    for i in range(st.session_state.max_rounds):
        handle_pro_round(topic)
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        handle_con_round(topic)
        current_step += 1
        progress_bar.progress(current_step / total_steps)

    handle_judge(topic)
    current_step += 1
    progress_bar.progress(current_step / total_steps)

    display_debate_results()


def display_debate_results():

    topic = st.session_state.ui_topic
    st.header(f"토론 주제: {topic}")

    # 토론 내용 표시
    st.header("토론 진행 상황")
    for i, entry in enumerate(st.session_state.messages):
        round_num = (i // 2) + 1

        if round_num <= st.session_state.max_rounds:
            if i % 2 == 0:
                st.subheader(f"라운드 {round_num} / {st.session_state.max_rounds}")
            st.subheader(entry["role"])
        else:
            st.header("심판")
        st.write(entry["content"])
        st.divider()

    # if st.form_submit_button("새 토론 시작"):
    if st.button("새 토론 시작"):
        reset_session_state()
        st.rerun()


if __name__ == "__main__":

    # session_state 초기화
    init_session_state()

    # UI 렌더링
    render_ui()
