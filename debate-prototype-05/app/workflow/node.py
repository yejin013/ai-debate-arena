from retrieval.vector_store import create_vector_store, search_topic
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from workflow.config import get_llm
from app.workflow.state import DebateState, AgentType


# 찬성 측 에이전트 노드
def pro_agent(state: DebateState) -> DebateState:
    # 시스템 프롬프트 설정
    system_prompt = "당신은 논리적이고 설득력 있는 찬성 측 토론자입니다."

    # 메시지 준비
    messages = [SystemMessage(content=system_prompt)]

    # 기존 대화 기록 추가
    for message in state["messages"]:
        if message["role"] == "assistant":
            messages.append(AIMessage(content=message["content"]))
        else:
            messages.append(
                HumanMessage(content=f"{message['role']}: {message['content']}")
            )

    context = state.get("contexts", {}).get(AgentType.PRO, "")

    # 프롬프트 구성
    if state["current_round"] == 1:
        prompt = f"""
        당신은 '{state['topic']}'에 대해 찬성 입장을 가진 토론자입니다.
        다음은 이 주제와 관련된 정보입니다:
            {context}
        논리적이고 설득력 있는 찬성 측 주장을 제시해주세요.
        가능한 경우 제공된 정보에서 구체적인 근거를 인용하세요.
        2 ~ 3문단, 각 문단은 100자내로 작성해주세요.
        """
    else:
        # 이전 발언자의 마지막 메시지를 가져옴
        previous_messages = [m for m in state["messages"] if m["role"] == AgentType.CON]
        if previous_messages:
            last_con_message = previous_messages[-1]["content"]
            prompt = f"""
            당신은 '{state['topic']}'에 대해 찬성 입장을 가진 토론자입니다.
            다음은 이 주제와 관련된 정보입니다:
                {context}
            반대 측의 다음 주장에 대해 반박하고, 찬성 입장을 더 강화해주세요:
            반대 측 주장: "{last_con_message}"

            2 ~ 3문단, 각 문단은 100자내로 작성해주세요.
            """

    # LLM에 요청
    messages.append(HumanMessage(content=prompt))
    response = get_llm().invoke(messages)

    # 상태 업데이트
    new_state = state.copy()
    new_state["messages"].append({"role": AgentType.PRO, "content": response.content})
    new_state["prev_node"] = AgentType.PRO
    return new_state


# 반대 측 에이전트 노드
def con_agent(state: DebateState) -> DebateState:
    """반대 측 에이전트 함수"""
    # 시스템 프롬프트 설정
    system_prompt = "당신은 논리적이고 설득력 있는 반대 측 토론자입니다. 찬성 측 주장에 대해 적극적으로 반박하세요."

    # 메시지 준비
    messages = [SystemMessage(content=system_prompt)]

    # 기존 대화 기록 추가
    for message in state["messages"]:
        if message["role"] == "assistant":
            messages.append(AIMessage(content=message["content"]))
        else:
            messages.append(
                HumanMessage(content=f"{message['role']}: {message['content']}")
            )

    # 프롬프트 구성
    context = state.get("contexts", {}).get(AgentType.CON, "")

    # 찬성 측 마지막 메시지를 가져옴
    previous_messages = [m for m in state["messages"] if m["role"] == AgentType.PRO]
    last_pro_message = previous_messages[-1]["content"]
    prompt = f"""
    당신은 '{state['topic']}'에 대해 반대 입장을 가진 토론자입니다.
    다음은 이 주제와 관련된 정보입니다:
        {context}
    찬성 측의 다음 주장에 대해 반박하고, 반대 입장을 제시해주세요:
    찬성 측 주장: "{last_pro_message}"
    2 ~ 3문단, 각 문단은 100자내로 작성해주세요.
    """

    # LLM에 요청
    messages.append(HumanMessage(content=prompt))
    response = get_llm().invoke(messages)

    # 상태 업데이트
    new_state = state.copy()
    new_state["messages"].append({"role": AgentType.CON, "content": response.content})
    new_state["prev_node"] = AgentType.CON
    return new_state


# 심판 에이전트 노드
def judge_agent(state: DebateState) -> DebateState:
    """심판 에이전트 함수"""
    # 시스템 프롬프트 설정
    system_prompt = "당신은 공정하고 논리적인 토론 심판입니다. 양측의 주장을 면밀히 검토하고 객관적으로 평가해주세요."

    # 메시지 준비
    messages = [SystemMessage(content=system_prompt)]

    # 프롬프트 구성
    context = state.get("contexts", {}).get(AgentType.JUDGE, "")

    prompt = f"""
    다음은 '{state['topic']}'에 대한 찬반 토론입니다. 각 측의 주장을 분석하고 평가해주세요.
    다음은 이 주제와 관련된 객관적인 정보입니다:
        {context}
    토론 내용:
    """
    for message in state["messages"]:
        agentType_text = AgentType.to_korean(message["role"])
        prompt += f"\n\n{agentType_text}: {message['content']}"

    prompt += """
    
    위 토론을 분석하여 다음을 포함하는 심사 평가를 해주세요:
    1. 양측 주장의 핵심 요약
    2. 각 측이 사용한 주요 논리와 증거의 강점과 약점
    3. 전체 토론의 승자와 그 이유
    4. 양측 모두에게 개선점 제안
    """

    # LLM에 요청
    messages.append(HumanMessage(content=prompt))
    response = get_llm().invoke(messages)

    # 상태 업데이트
    new_state = state.copy()
    new_state["messages"].append({"role": AgentType.JUDGE, "content": response.content})
    return new_state


def increment_round(state: DebateState) -> DebateState:
    new_state = state.copy()
    new_state["current_round"] = state["current_round"] + 1
    return new_state


# 검색 노드
def retriever(state: DebateState) -> DebateState:

    RETRIEVAL_K = 2

    # 이전 노드로 부터 검색 할 에이전트 타입 결정
    prev_node = state["prev_node"]

    if state["current_round"] > state["max_rounds"]:
        agentType = AgentType.JUDGE
    else:
        if prev_node == "START":
            # 시작 노드면 찬성 에이전트 검색
            agentType = AgentType.PRO
        else:
            # 이전 노드가 PRO면 CON 검색, CON이면 PRO로 검색
            agentType = AgentType.CON if prev_node == AgentType.PRO else AgentType.PRO

    topic = state["topic"]

    # 검색 쿼리 생성
    query = topic
    if agentType == AgentType.PRO:
        query += " 찬성 장점 이유 근거"
    elif agentType == AgentType.CON:
        query += " 반대 단점 이유 근거"
    elif agentType == AgentType.JUDGE:
        query += " 평가 기준 객관적 사실"

    # 관련 정보 검색
    retrieved_docs = search_topic(topic, query, k=RETRIEVAL_K)

    # 검색 결과를 컨텍스트로 변환
    context = ""
    for i, doc in enumerate(retrieved_docs):
        source = doc.metadata.get("source", "Unknown")
        section = doc.metadata.get("section", "")
        context += f"[문서 {i + 1}] 출처: {source}"
        if section:
            context += f", 섹션: {section}"
        context += f"\n{doc.page_content}\n\n"

    new_state = state.copy()

    # 에이전트별 컨텍스트 저장
    if "contexts" not in new_state:
        new_state["contexts"] = {}
    new_state["contexts"][agentType] = context

    # 검색된 문서 저장
    if "retrieved_docs" not in new_state:
        new_state["retrieved_docs"] = {}
    new_state["retrieved_docs"][agentType] = (
        [doc.page_content for doc in retrieved_docs] if retrieved_docs else []
    )

    return new_state
