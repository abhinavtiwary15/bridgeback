"""Notification service with Telegram Bot + safe mock fallback."""

from __future__ import annotations

import logging
import requests
from dataclasses import dataclass

from config import (
    TELEGRAM_BOT_TOKEN,
    FCM_SERVER_KEY,
)

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    status: str
    provider_message_id: str = ""
    error: str = ""


def _is_telegram_ready() -> bool:
    return bool(TELEGRAM_BOT_TOKEN)


def send_telegram_message(message: str, chat_id: str | None = None) -> NotificationResult:
    """
    Send Telegram message via Telegram Bot API when configured.
    Falls back to a mock success when credentials/chat_id are missing.
    """
    if not _is_telegram_ready() or not chat_id:
        logger.info("Telegram credentials or chat_id missing. Mocking Telegram send.")
        return NotificationResult(status="mocked", provider_message_id="mock-telegram")

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        resp = requests.post(url, json=payload, timeout=10)
        
        if resp.ok:
            data = resp.json()
            return NotificationResult(status="sent", provider_message_id=str(data.get("result", {}).get("message_id", "")))
        else:
            return NotificationResult(status="failed", error=resp.text)
    except Exception as exc:
        logger.exception("Telegram API send failed")
        return NotificationResult(status="failed", error=str(exc))


def send_push_notification(device_tokens: list[str], title: str, body: str) -> NotificationResult:
    """
    Push notification send path.
    Uses FCM HTTP v1 server-key fallback for lightweight setup.
    If no key/tokens, returns mocked status.
    """
    if not device_tokens or not FCM_SERVER_KEY:
        return NotificationResult(status="mocked", provider_message_id="mock-fcm")

    ok_count = 0
    try:
        for token in device_tokens:
            payload = {
                "to": token,
                "notification": {"title": title, "body": body},
                "data": {"channel": "accountability"},
            }
            resp = requests.post(
                "https://fcm.googleapis.com/fcm/send",
                json=payload,
                headers={"Authorization": f"key={FCM_SERVER_KEY}", "Content-Type": "application/json"},
                timeout=10,
            )
            if resp.ok:
                ok_count += 1
        if ok_count:
            return NotificationResult(status="sent", provider_message_id=f"fcm:{ok_count}")
        return NotificationResult(status="failed", error="No push notifications were delivered")
    except Exception as exc:
        logger.exception("Push notification send failed")
        return NotificationResult(status="failed", error=str(exc))
