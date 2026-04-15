"""FastAPI entrypoint for BridgeBack backend APIs."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from data.database import init_db
from logging_config import setup_logging
from config import CORS_ORIGINS, API_AUTH_TOKEN
from api.routers.health import router as health_router
from api.routers.chat import router as chat_router
from api.routers.plan import router as plan_router
from api.routers.blocker import router as blocker_router
from api.routers.progress import router as progress_router
from api.routers.notifications import router as notifications_router
from api.routers.auth import router as auth_router

from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from data.database import SessionLocal, DBActionTask
from services.accountability_service import send_pending_action_checkin

scheduler = BackgroundScheduler()

def process_reminders():
    logger.info("Running background reminder check...")
    try:
        with SessionLocal() as db:
            pending_users = db.query(DBActionTask.user_id).filter(DBActionTask.status == "pending").distinct().all()
            for (uid,) in pending_users:
                send_pending_action_checkin(user_id=uid)
    except Exception as e:
        logger.error(f"Error in background scheduler: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(process_reminders, "interval", minutes=60)
    scheduler.start()
    yield
    scheduler.shutdown()

setup_logging()
init_db()

app = FastAPI(title="BridgeBack API", version="1.0.0", lifespan=lifespan)
logger = logging.getLogger("bridgeback.api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(plan_router)
app.include_router(blocker_router)
app.include_router(progress_router)
app.include_router(notifications_router)
app.include_router(auth_router)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    if API_AUTH_TOKEN and request.url.path != "/health":
        provided = request.headers.get("x-api-key", "")
        if provided != API_AUTH_TOKEN:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response
