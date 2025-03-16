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

        def increment_round_router(state: DebateState) -> str:
            if state["current_round"] > state["max_rounds"]:
                return AgentType.JUDGE
            return AgentType.PRO

        def agent_router(state: DebateState) -> str:
            prev_node = state["prev_node"]

            if prev_node == AgentType.PRO:
                return AgentType.CON
            elif prev_node == AgentType.CON:
                return "INCREMENT_ROUND"
            else:
                print(f"WARNING: Unexpected speaker role: {prev_node}")
                return AgentType.PRO

        workflow.add_conditional_edges(AgentType.PRO, agent_router)
        workflow.add_conditional_edges(AgentType.CON, agent_router)
        workflow.add_conditional_edges("INCREMENT_ROUND", increment_round_router)
        workflow.add_edge(AgentType.JUDGE, END)

        workflow.set_entry_point(AgentType.PRO)
    else:

        def increment_round_router(state: DebateState) -> str:
            return "RETRIEVER"  # Agent 대신 RAG 노드로 이동

        def agent_router(state: DebateState) -> str:
            prev_node = state["prev_node"]

            if prev_node == AgentType.PRO:
                return "RETRIEVER"  # Agent 대신 RAG 노드로 이동
            elif prev_node == AgentType.CON:
                return "INCREMENT_ROUND"
            else:
                print(f"WARNING: Unexpected speaker role: {prev_node}")
                return AgentType.PRO

        def retriever_router(state: DebateState) -> str:
            prev_node = state["prev_node"]
            if prev_node == "START":
                return AgentType.PRO
            elif prev_node == AgentType.PRO:
                return AgentType.CON
            elif prev_node == AgentType.CON:
                if state["current_round"] > state["max_rounds"]:
                    return AgentType.JUDGE
                return AgentType.PRO
            else:
                print(f"WARNING: Unexpected speaker role: {prev_node}")

        workflow.add_conditional_edges(AgentType.PRO, agent_router)
        workflow.add_conditional_edges(AgentType.CON, agent_router)
        workflow.add_conditional_edges("INCREMENT_ROUND", increment_round_router)
        workflow.add_edge(AgentType.JUDGE, END)

        workflow.add_node("RETRIEVER", retriever)
        workflow.add_conditional_edges("RETRIEVER", retriever_router)

        workflow.set_entry_point("RETRIEVER")

    return workflow.compile()
