# BridgeBack — Deployment Guide

## Overview

BridgeBack can be deployed in two ways:
1. **GitHub** — version-controlled source repo with CI/CD
2. **Hugging Face Spaces** — live public demo (free tier, Streamlit)

---

## Part 1: GitHub Setup

### Step 1 — Create the repository

```bash
# In your terminal, from the bridgeback/ folder
git init
git add .
git commit -m "Initial commit: BridgeBack v1.0"
```

Go to https://github.com/new and create a new repository called `bridgeback`.

```bash
git remote add origin https://github.com/YOUR_USERNAME/bridgeback.git
git branch -M main
git push -u origin main
```

### Step 2 — Add GitHub Secrets (for CI)

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `OPENAI_API_KEY` | Your OpenAI key (optional) |

### Step 3 — Verify CI runs

After pushing, go to **Actions** tab — the CI workflow will run automatically and test your NLP layer.

---

## Part 2: Hugging Face Spaces Deployment

### Step 1 — Create a Space

1. Go to https://huggingface.co/spaces
2. Click **Create new Space**
3. Fill in:
   - **Space name**: `bridgeback`
   - **License**: MIT
   - **SDK**: Streamlit
   - **Visibility**: Public (or Private)
4. Click **Create Space**

### Step 2 — Push your code to the Space

HF Spaces uses a Git remote. Add it alongside your GitHub remote:

```bash
# Add HF Spaces as a second remote
git remote add space https://huggingface.co/spaces/YOUR_HF_USERNAME/bridgeback

# Push to HF Spaces
git push space main
```

Or you can link the Space directly to your GitHub repo:
- In your Space → **Settings → Repository** → Link GitHub repo

### Step 3 — Set Secrets in HF Spaces

Go to your Space → **Settings → Repository secrets → New secret**

Add these (same as GitHub):

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `OPENAI_API_KEY` | Your OpenAI key (optional) |
| `DEFAULT_LLM` | `claude` |
| `USER_LOCATION` | Your city (e.g. `Jamshedpur`) |

> HF Spaces injects these as environment variables at runtime — the app reads them via `python-dotenv` + `os.getenv`.

### Step 4 — Watch the build

The Space will:
1. Install `requirements.txt`
2. Download the spaCy model (`en_core_web_sm`)
3. Start `streamlit run app.py`

Build logs are visible in the **Logs** tab of your Space.

---

## Part 3: Keeping GitHub and HF Spaces in sync

Set up a GitHub Action to auto-deploy to HF Spaces on every push to `main`.

Add this file: `.github/workflows/deploy_hf.yml`

```yaml
name: Deploy to HF Spaces

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          lfs: true

      - name: Push to HF Spaces
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          git remote add space https://YOUR_HF_USERNAME:$HF_TOKEN@huggingface.co/spaces/YOUR_HF_USERNAME/bridgeback
          git push space main --force
```

Add `HF_TOKEN` (your HF write token from https://huggingface.co/settings/tokens) to GitHub Secrets.

---

## Local Development

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/bridgeback.git
cd bridgeback

# Install
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
streamlit run app.py
```

Open http://localhost:8501

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes (if using Claude) | — | Anthropic API key |
| `OPENAI_API_KEY` | Yes (if using OpenAI) | — | OpenAI API key |
| `DEFAULT_LLM` | No | `claude` | `claude` or `openai` |
| `MEETUP_API_KEY` | No | — | For real event data |
| `USER_LOCATION` | No | — | City for event matching |
| `DATABASE_URL` | No | `sqlite:///bridgeback.db` | DB connection string |

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'anthropic'"**
→ Run `pip install -r requirements.txt`

**"Can't load en_core_web_sm"**
→ Run `python -m spacy download en_core_web_sm`

**Score not appearing**
→ Type at least 2–3 sentences in the chat. The NLP needs enough text to score.

**HF Space crashes on startup**
→ Check the Logs tab. Most common cause: missing `ANTHROPIC_API_KEY` secret.

**Events showing mock data**
→ Normal if `MEETUP_API_KEY` is empty. Set it + `USER_LOCATION` for real events.
