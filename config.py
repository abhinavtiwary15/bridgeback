"""
BridgeBack — Configuration
FREE LLM options: Groq, Google Gemini, Ollama (local)
No paid API required.
"""

import os

from dotenv import load_dotenv

load_dotenv(override=True)

# ── LLM Backend ───────────────────────────────────────────────────────────────
# FREE options:
#   "groq"    — Free tier: console.groq.com  (fastest, recommended)
#   "gemini"  — Free tier: aistudio.google.com
#   "ollama"  — 100% local, no internet needed (install ollama.ai first)
# Paid options (optional):
#   "claude"  — Anthropic
#   "openai"  — OpenAI

DEFAULT_LLM: str = os.getenv("DEFAULT_LLM", "groq")

# ── Free API Keys ─────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")  # free at console.groq.com
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")  # free at aistudio.google.com

# ── Paid API Keys (optional) ──────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ── Model names ───────────────────────────────────────────────────────────────
GROQ_MODEL: str = "llama-3.1-8b-instant"
GEMINI_MODEL: str = "gemini-flash-latest"
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")

CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
OPENAI_MODEL: str = "gpt-4o"
MAX_TOKENS: int = 1024

# ── Community APIs ────────────────────────────────────────────────────────────
MEETUP_API_KEY: str = os.getenv("MEETUP_API_KEY", "")
USER_LOCATION: str = os.getenv("USER_LOCATION", "")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bridgeback.db")
CORS_ORIGINS: str = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:8501"
)
API_AUTH_TOKEN: str = os.getenv("API_AUTH_TOKEN", "")

# ── Loneliness Score Bands (UCLA scale) ──────────────────────────────────────
SCORE_BANDS = {
    (0, 20): ("minimal", "Healthy social connection"),
    (21, 40): ("mild", "Some social gaps, manageable"),
    (41, 60): ("moderate", "Noticeable isolation — intervention beneficial"),
    (61, 80): ("severe", "Significant withdrawal — active coaching needed"),
    (81, 100): ("acute", "Possible crisis risk — escalation protocols active"),
}

# ── Crisis keywords (Layer 5) ─────────────────────────────────────────────────
CRISIS_KEYWORDS = [
    "suicide",
    "suicidal",
    "kill myself",
    "end my life",
    "want to die",
    "no reason to live",
    "better off dead",
    "self-harm",
    "hurt myself",
    "no one would care",
    "nobody would miss me",
]

# ── Crisis resources by region ────────────────────────────────────────────────
CRISIS_RESOURCES = {
    "IN": [
        ("iCall (India)", "9152987821"),
        ("Vandrevala Foundation", "1860-2662-345"),
        ("AASRA", "9820466627"),
    ],
    "US": [
        ("988 Suicide & Crisis Lifeline", "988"),
        ("Crisis Text Line", "Text HOME to 741741"),
    ],
    "UK": [
        ("Samaritans", "116 123"),
        ("Crisis Text Line UK", "Text SHOUT to 85258"),
    ],
    "DEFAULT": [
        (
            "International Association for Suicide Prevention",
            "https://www.iasp.info/resources/Crisis_Centres/",
        ),
    ],
}

# ── App behaviour ─────────────────────────────────────────────────────────────
APP_TITLE: str = "BridgeBack"
APP_SUBTITLE: str = "Reconnect with real people"
SESSION_CADENCE_DAYS: int = 7  # nudge user to return after N days
MIN_ACTIONS_BEFORE_RETURN: int = (
    1  # user must complete ≥ N actions before re-opening app
)

# ── Accountability / Telegram ───────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
REMINDER_COOLDOWN_HOURS: int = int(os.getenv("REMINDER_COOLDOWN_HOURS", "24"))
FCM_SERVER_KEY: str = os.getenv("FCM_SERVER_KEY", "")
