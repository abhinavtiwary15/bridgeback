from fastapi import APIRouter

from api.schemas import BlockerRequest, BlockerResponse
from services.accountability_service import apply_checkin_reply
from services.gate_service import get_gate_state

router = APIRouter(prefix="/blocker", tags=["blocker"])


@router.get("/gate")
def gate_state(user_id: str = "default"):
    state = get_gate_state(user_id=user_id)
    return {
        "active": state.active,
        "action_id": state.action_id,
        "action_text": state.action_text,
    }


@router.post("", response_model=BlockerResponse)
def submit_blocker(payload: BlockerRequest):
    result = apply_checkin_reply(user_id=payload.user_id, reply_text=payload.reply_text)
    return BlockerResponse(
        handled=result.handled,
        status=result.status,
        micro_step=result.micro_step,
    )
