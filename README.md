---
title: BridgeBack
emoji: 🌉
colorFrom: green
colorTo: yellow
sdk: docker
pinned: false
license: mit
short_description: AI-powered loneliness & reconnection platform
---

# 🌉 BridgeBack

**An AI-powered loneliness intervention & human reconnection platform.**

BridgeBack is NOT an AI companion. It is a loneliness diagnostician and human-connection coach
that helps you identify who in your life you've drifted from — and generates specific,
actionable steps to reconnect with real people.

> The AI is engineered to minimise its own usage.
> Its success metric is how quickly you stop needing it.

---

## What it does

- **Layer 1 — NLP Profiling**: Analyses your messages to produce a loneliness score (0–100,
  calibrated against the UCLA Loneliness Scale), extract relationship signals, and detect
  drift patterns.

- **Layer 2 — LLM Conversation Engine**: Warm, empathetic coaching that actively redirects
  you toward real humans instead of itself. Supports Groq, Gemini, Ollama, Claude, and OpenAI.

- **Layer 3 — Reconnection Plan Generator**: Specific, named outreach actions with
  suggested message drafts and local community event matches.

- **Layer 4 — Progress Tracker**: Week-by-week loneliness score chart, connection count,
  streak tracker, and relationship health map.

- **Layer 5 — Crisis Detection**: Scans for acute distress signals. Immediately provides
  regional crisis resources and encourages human contact.

---

## Setup (local)

```bash
git clone https://github.com/YOUR_USERNAME/bridgeback.git
cd bridgeback
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
# Edit .env with your API keys
streamlit run app.py
```

## Setup (Hugging Face Spaces)

1. Fork or upload this repo to a new HF Space (SDK: Streamlit)
2. In your Space → **Settings → Repository secrets**, add:
   - one of `GROQ_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
   - `DEFAULT_LLM` — `groq`, `gemini`, `ollama`, `claude`, or `openai`
   - `USER_LOCATION` — your city (for event matching)
3. The Space will build and deploy automatically.

---

## Design philosophy

Every feature in BridgeBack flows from one principle:

> **The app should be used less over time, not more.**

- Features that increase engagement are anti-features.
- The reward system celebrates real-world social actions, not app sessions.
- Crisis situations are immediately referred out — never managed by the AI.
- All loneliness scoring is private to the user.

---

## What BridgeBack is NOT

- ❌ Not a therapy app
- ❌ Not an AI companion
- ❌ Not a social network
- ❌ Not a crisis hotline
- ❌ Not a journaling app

## What BridgeBack IS

- ✅ A loneliness diagnostic tool
- ✅ A relationship drift detector
- ✅ A personalised reconnection action planner
- ✅ A community event matcher
- ✅ A longitudinal social health tracker
- ✅ An AI coach that actively resists being used as a substitute for human connection

---

## Tech stack

| Layer | Tech |
|---|---|
| NLP scoring | spaCy, sentence-transformers (optional), rule-based fallback |
| LLM | Groq / Gemini / Ollama / Claude / OpenAI (configurable) |
| Database | SQLite via SQLAlchemy |
| Community events | Meetup API + Nominatim (OpenStreetMap) |
| Frontend | Streamlit |
| Charts | Plotly |

---

*Built with care. Designed to be needed less.*
