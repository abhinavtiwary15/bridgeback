from fastapi import APIRouter

from api.schemas import DeviceTokenRequest
from data.database import upsert_device_token

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/device-token")
def register_device_token(payload: DeviceTokenRequest):
    upsert_device_token(payload.user_id, payload.token, payload.platform)
    return {"ok": True}
