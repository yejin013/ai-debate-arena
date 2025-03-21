from typing import Any
import uuid
import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langfuse.callback import CallbackHandler


from workflow.state import AgentType, DebateState
from workflow.graph import create_debate_graph


# API 경로를 /api/v1로 변경
router = APIRouter(
    prefix="/api/v1/workflow",
    tags=["workflow"],
    responses={404: {"description": "Not found"}},
)


class WorkflowRequest(BaseModel):
    topic: str
    max_rounds: int = 3
    enable_rag: bool = True


class WorkflowResponse(BaseModel):
    status: str = "success"
    result: Any = None


async def debate_generator(debate_graph, initial_state, langfuse_handler):
    for event in debate_graph.stream(
        initial_state,
        config={"callbacks": [langfuse_handler]},
    ):

        if isinstance(event, dict) and len(event) == 1:
            role = list(event.keys())[0]
            state = event[role]
        else:
            continue

        serializable_state = {
            "role": role,
            "topic": state.get("topic", ""),
            "current_round": state.get("current_round", 0),
            "max_rounds": state.get("max_rounds", 0),
            "prev_node": state.get("prev_node", ""),
            "messages": [],
        }

        if "messages" in state:
            for msg in state["messages"]:
                serializable_msg = {
                    "role": msg.get("role", ""),
                    "content": msg.get("content", ""),
                    "round": msg.get("round", 0),
                }
                serializable_state["messages"].append(serializable_msg)

        event_data = {"type": "update", "data": serializable_state}
        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        print(event_data)

        await asyncio.sleep(0.01)

    yield f"data: {json.dumps({'type': 'end', 'data': {}}, ensure_ascii=False)}\n\n"


# 엔드포인트 경로 수정 (/debate/stream -> 유지)
@router.post("/debate/stream")
async def stream_debate_workflow(request: WorkflowRequest):
    debate_topic = request.topic
    max_rounds = request.max_rounds
    enable_rag = request.enable_rag

    session_id = str(uuid.uuid4())
    debate_graph = create_debate_graph(enable_rag, session_id)

    initial_state: DebateState = {
        "topic": debate_topic,
        "messages": [],
        "current_round": 1,
        "prev_node": AgentType.PRO,
        "max_rounds": max_rounds,
        "docs": {},
    }

    langfuse_handler = CallbackHandler(session_id=session_id)

    # 스트리밍 응답 반환
    return StreamingResponse(
        debate_generator(debate_graph, initial_state, langfuse_handler),
        media_type="text/event-stream",
    )


# 엔드포인트 경로 수정
@router.post("/debate", response_model=WorkflowResponse)
async def run_debate_workflow(request: WorkflowRequest):
    debate_topic = request.topic
    max_rounds = request.max_rounds
    enable_rag = request.enable_rag

    session_id = str(uuid.uuid4())
    debate_graph = create_debate_graph(enable_rag, session_id)

    initial_state: DebateState = {
        "topic": debate_topic,
        "messages": [],
        "current_round": 1,
        "prev_node": AgentType.PRO,
        "max_rounds": max_rounds,
        "docs": {},
    }

    langfuse_handler = CallbackHandler(session_id=session_id)

    response = debate_graph.invoke(
        initial_state,
        config={"callbacks": [langfuse_handler]},
    )
    return WorkflowResponse(status="success", result=response)
