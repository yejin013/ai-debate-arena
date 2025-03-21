from workflow.state import DebateState, AgentType
from workflow.node import increment_round, pro_agent, con_agent, judge_agent, retriever
from langgraph.graph import StateGraph, END


def create_debate_graph(enable_rag) -> StateGraph:
    # 그래프 생성
    workflow = StateGraph(DebateState)

    # 기존 노드 추가
    workflow.add_node(AgentType.PRO, pro_agent)
    workflow.add_node(AgentType.CON, con_agent)
    workflow.add_node(AgentType.JUDGE, judge_agent)
    workflow.add_node("INCREMENT_ROUND", increment_round)

    if not enable_rag:

        workflow.add_edge(AgentType.PRO, AgentType.CON)
        workflow.add_edge(AgentType.CON, "INCREMENT_ROUND")
        workflow.add_edge(AgentType.JUDGE, END)

        workflow.add_conditional_edges(
            "INCREMENT_ROUND",
            lambda s: (
                AgentType.JUDGE
                if s["current_round"] > s["max_rounds"]
                else AgentType.PRO
            ),
            [AgentType.JUDGE, AgentType.PRO],
        )

        workflow.set_entry_point(AgentType.PRO)
        workflow.add_edge(AgentType.JUDGE, END)

    else:

        def retriever_router(state: DebateState) -> str:
            prev_node = state["prev_node"]
            if prev_node == "START":
                # 시작 노드에서는 PRO 에이전트로 시작
                return AgentType.PRO
            elif prev_node == AgentType.PRO:
                # 이전 노드가 PRO 에이전트인 경우 CON 에이전트로 이동
                return AgentType.CON
            elif prev_node == AgentType.CON:
                # 이전 노드가 CON 에이전트인 경우 라운드 증가
                if state["current_round"] > state["max_rounds"]:
                    return AgentType.JUDGE
                # 아직 라운드가 남은 경우 PRO 에이전트로 이동
                return AgentType.PRO
            else:
                print(f"WARNING: Unexpected speaker role: {prev_node}")

        workflow.add_edge(AgentType.PRO, "RETRIEVER")
        workflow.add_edge(AgentType.CON, "INCREMENT_ROUND")
        workflow.add_edge("INCREMENT_ROUND", "RETRIEVER")

        workflow.add_node("RETRIEVER", retriever)
        workflow.add_conditional_edges(
            "RETRIEVER",
            retriever_router,
            [AgentType.PRO, AgentType.CON, AgentType.JUDGE],
        )

        workflow.set_entry_point("RETRIEVER")
        workflow.add_edge(AgentType.JUDGE, END)

    return workflow.compile()


if __name__ == "__main__":

    graph = create_debate_graph(True)

    graph_image = graph.get_graph().draw_mermaid_png()

    output_path = "debate_graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)

    import subprocess

    subprocess.run(["open", output_path])
