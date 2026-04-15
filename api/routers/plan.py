from fastapi import APIRouter, HTTPException

from api.schemas import PlanResponse, PlanActionDTO, ActionUpdateRequest
from data.database import get_action_tasks, complete_action_task, block_action_task
from services.accountability_service import generate_micro_step

router = APIRouter(prefix="/plan", tags=["plan"])


@router.get("", response_model=PlanResponse)
def get_plan(user_id: str = "default"):
    rows = get_action_tasks(user_id=user_id, limit=100)
    actions = [
        PlanActionDTO(
            action_id=row.action_id,
            target=row.target,
            action_text=row.action_text,
            status=row.status,
            blocker_reason=row.blocker_reason or "",
            micro_step=row.micro_step or "",
        )
        for row in rows
    ]
    return PlanResponse(user_id=user_id, actions=actions)


@router.post("/action")
def update_action(payload: ActionUpdateRequest):
    if payload.status == "completed":
        ok = complete_action_task(payload.action_id, user_id=payload.user_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Action not found")
        return {"ok": True, "status": "completed"}

    micro_step = generate_micro_step(payload.blocker_reason)
    ok = block_action_task(
        payload.action_id,
        blocker_reason=payload.blocker_reason,
        micro_step=micro_step,
        user_id=payload.user_id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"ok": True, "status": "blocked", "micro_step": micro_step}
