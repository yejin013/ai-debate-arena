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
    workflow.add_node(AgentType.PRO, pro_agent.get_graph())
    workflow.add_node(AgentType.CON, con_agent.get_graph())
    workflow.add_node(AgentType.JUDGE, judge_agent.get_graph())
    workflow.add_node("INCREMENT_ROUND", round_manager.run)
    workflow.add_edge(AgentType.PRO, AgentType.CON)  # 찬성 → 조건부 라우팅
    workflow.add_edge(AgentType.CON, "INCREMENT_ROUND")  # 반대 → 조건부 라우팅

    workflow.add_conditional_edges(
        "INCREMENT_ROUND",
        lambda s: (
            AgentType.JUDGE if s["current_round"] > s["max_rounds"] else AgentType.PRO
        ),
        [AgentType.JUDGE, AgentType.PRO],
    )

    workflow.set_entry_point(AgentType.PRO)
    workflow.set_finish_point(AgentType.JUDGE)

    # 그래프 컴파일
    return workflow.compile()


if __name__ == "__main__":

    graph = create_debate_graph(True)

    graph_image = graph.get_graph().draw_mermaid_png()

    output_path = "debate_graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)

    import subprocess

    subprocess.run(["open", output_path])

    from langgraph.graph import StateGraph
    from typing import TypedDict

    # 상태 정의
    class GraphState(TypedDict):
        value: int

    ### Subgraph1: 값 * 2 ###
    def double_value(state: GraphState) -> GraphState:
        result = state["value"] * 2
        print(f"[Subgraph1] doubled: {result}")
        return {"value": result}

    subgraph1 = StateGraph(GraphState)
    subgraph1.add_node("double", double_value)
    subgraph1.set_entry_point("double")
    subgraph1.set_finish_point("double")
    compiled_subgraph1 = subgraph1.compile()

    ### Subgraph2: 값 + 10 ###
    def add_ten(state: GraphState) -> GraphState:
        result = state["value"] + 10
        print(f"[Subgraph2] plus 10: {result}")
        return {"value": result}

    subgraph2 = StateGraph(GraphState)
    subgraph2.add_node("add", add_ten)
    subgraph2.set_entry_point("add")
    subgraph2.set_finish_point("add")
    compiled_subgraph2 = subgraph2.compile()

    ### 메인 그래프 ###
    main_graph = StateGraph(GraphState)
    main_graph.add_node("sub1", compiled_subgraph1)
    main_graph.add_node("sub2", compiled_subgraph2)
    main_graph.set_entry_point("sub1")
    main_graph.add_edge("sub1", "sub2")
    main_graph.set_finish_point("sub2")
    main_graph.compile()

    # ✅ Mermaid PNG 이미지로 저장
    graph_image = main_graph.compile().get_graph(xray=2).draw_mermaid_png()
    output_path2 = "debate_graph2.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)
    subprocess.run(["open", output_path2])
