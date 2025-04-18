from workflow.agents.agent import Agent
from workflow.state import AgentType
from typing import Dict, Any


class ConAgent(Agent):

    def __init__(self, k: int = 2, session_id: str = None):
        super().__init__(
            system_prompt="당신은 논리적이고 설득력 있는 반대 측 토론자입니다. 찬성 측 주장에 대해 적극적으로 반박하세요.",
            role=AgentType.CON,
            k=k,
            session_id=session_id,
        )

    def _create_prompt(self, state: Dict[str, Any]) -> str:

        if state["current_round"] == 1:
            return self._create_first_round_prompt(state)
        else:
            return self._create_rebuttal_prompt(state)

    def _create_first_round_prompt(self, state: Dict[str, Any]) -> str:

        # 찬성 측 마지막 메시지를 가져옴
        previous_messages = [m for m in state["messages"] if m["role"] == AgentType.PRO]
        last_pro_message = previous_messages[-1]["content"] if previous_messages else ""

        return f"""
            당신은 '{state['topic']}'에 대해 반대 입장을 가진 토론자입니다.
            다음은 이 주제와 관련된 정보입니다:
                {state.get("context", "")}
            찬성 측의 다음 주장에 대해 반박하고, 반대 입장을 제시해주세요:
            찬성 측 주장: "{last_pro_message}"
            2 ~ 3문단, 각 문단은 100자내로 작성해주세요.
            """

    def _create_rebuttal_prompt(self, state: Dict[str, Any]) -> str:

        # 찬성 측 마지막 메시지를 가져옴
        pro_messages = [m for m in state["messages"] if m["role"] == AgentType.PRO]
        last_pro_message = pro_messages[-1]["content"] if pro_messages else ""

        return f"""
            당신은 '{state['topic']}'에 대해 반대 입장을 가진 토론자입니다.
            다음은 이 주제와 관련된 정보입니다:
                {state.get("context", "")}
            찬성 측의 최근 주장에 대해 반박하고, 반대 입장을 더 강화해주세요:
            찬성 측 주장: "{last_pro_message}"
            
            2 ~ 3문단, 각 문단은 100자내로 작성해주세요.
            논리적이고 구체적인 근거를 제시하세요.
            """
