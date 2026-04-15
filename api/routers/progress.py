from fastapi import APIRouter

from api.schemas import ProgressPoint, ProgressResponse
from data.database import get_action_status_counts
from tracking.tracker import (
    generate_weekly_insight,
    get_score_history,
    get_streak,
    get_total_connections,
)

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ProgressResponse)
def get_progress(user_id: str = "default"):
    history = [ProgressPoint(**point) for point in get_score_history(user_id)]
    return ProgressResponse(
        user_id=user_id,
        history=history,
        streak=get_streak(user_id),
        total_connections=get_total_connections(user_id),
        insight=generate_weekly_insight(user_id),
        action_status=get_action_status_counts(user_id),
    )
