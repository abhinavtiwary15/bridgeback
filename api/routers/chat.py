from fastapi import APIRouter

from api.dependencies import get_engine_for_user
from api.schemas import ChatRequest, ChatResponse, ReminderResponse
from services.chat_service import process_user_message
from services.accountability_service import send_pending_action_checkin
from llm.plan_generator import generate_structured_action_response

from datetime import datetime, UTC

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def post_chat(payload: ChatRequest):
    engine = get_engine_for_user(payload.user_id, backend=payload.backend)
    result, response = process_user_message(engine=engine, user_id=payload.user_id, user_text=payload.message)
    structured = {}
    if response.updated_profile:
        structured = generate_structured_action_response(response.updated_profile, backend=engine.backend)
    return ChatResponse(
        response_text=result.assistant_text,
        structured_data=structured,
        mode=response.mode,
    )


@router.post("/checkin", response_model=ReminderResponse)
def send_checkin(user_id: str = "default"):
    queued = send_pending_action_checkin(user_id=user_id)
    return ReminderResponse(queued=queued, user_id=user_id, timestamp=datetime.now(UTC))
