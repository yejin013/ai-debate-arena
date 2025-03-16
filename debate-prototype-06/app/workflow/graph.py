from workflow.agents.con_agent import ConAgent
from workflow.agents.judge_agent import JudgeAgent
from workflow.agents.pro_agent import ProAgent
from workflow.agents.round_manager import RoundManager
from workflow.state import DebateState, AgentType
from langgraph.graph import StateGraph, END


def create_debate_graph(enable_rag: bool = True, session_id: str = ""):

    # 그래프 생성
    workflow = StateGraph(DebateState)

    # 에이전트 인스턴스 생성 - enable_rag에 따라 검색 문서 수 결정
    k_value = 2 if enable_rag else 0
    pro_agent = ProAgent(k=k_value, session_id=session_id)
    con_agent = ConAgent(k=k_value, session_id=session_id)
    judge_agent = JudgeAgent(k=k_value, session_id=session_id)
    round_manager = RoundManager()

    # 노드 추가
    workflow.add_node(AgentType.PRO, pro_agent.run)
    workflow.add_node(AgentType.CON, con_agent.run)
    workflow.add_node(AgentType.JUDGE, judge_agent.run)
    workflow.add_node("INCREMENT_ROUND", round_manager.run)

    def increment_round_router(state: DebateState) -> str:
        if state["current_round"] > state["max_rounds"]:
            return AgentType.JUDGE  # 최대 라운드 도달 시 심판으로
        return AgentType.PRO  # 아니면 새 라운드 시작 (찬성부터)

    def agent_router(state: DebateState) -> str:
        prev_node = state["prev_node"]

        if prev_node == AgentType.PRO:
            return AgentType.CON  # 찬성 다음은 반대
        elif prev_node == AgentType.CON:
            return "INCREMENT_ROUND"  # 반대 다음은 라운드 증가
        else:
            # 예상치 못한 경우 처리
            print(f"WARNING: Unexpected previous node: {prev_node}")
            return AgentType.PRO  # 기본값은 찬성으로

    workflow.add_conditional_edges(AgentType.PRO, agent_router)  # 찬성 → 조건부 라우팅
    workflow.add_conditional_edges(AgentType.CON, agent_router)  # 반대 → 조건부 라우팅
    workflow.add_conditional_edges(
        "INCREMENT_ROUND", increment_round_router
    )  # 라운드 증가 → 조건부 라우팅
    workflow.add_edge(AgentType.JUDGE, END)  # 심판 → 종료

    # 시작점 설정 - 찬성 에이전트부터 시작
    workflow.set_entry_point(AgentType.PRO)

    # 그래프 컴파일
    return workflow.compile()
