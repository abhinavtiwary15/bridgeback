# BridgeBack API Deployment

## Local API

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Compose (API + Postgres)

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Production Notes

- Set `DATABASE_URL` to Postgres (recommended for production).
- Set your LLM provider keys in environment variables.
- Set Twilio and FCM variables for reminders and push.
- Set `API_AUTH_TOKEN` and pass `x-api-key` from clients.
- Restrict `CORS_ORIGINS` to explicit trusted domains.
- For Flutter client, provide:
  - `--dart-define=API_BASE_URL=https://your-api-host`
  - `--dart-define=API_AUTH_TOKEN=your_token`
