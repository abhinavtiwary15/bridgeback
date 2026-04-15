# BridgeBack Production Readiness Checklist

## 1) Secrets and Environment

- [ ] Use `.env.production.example` as baseline.
- [ ] Set `API_AUTH_TOKEN` (long random secret).
- [ ] Set strict `CORS_ORIGINS` (no wildcard in production).
- [ ] Set `DATABASE_URL` to Postgres.
- [ ] Set at least one LLM provider key.
- [ ] Set Twilio/FCM credentials if reminders and push are enabled.

## 2) Backend Deployment

- [ ] Build image: `docker build -t bridgeback-api .`
- [ ] Run health check: `GET /health` returns `200`.
- [ ] Verify authenticated endpoint access:
  - no `x-api-key` => `401`
  - valid `x-api-key` => success
- [ ] Confirm request timing header `X-Process-Time-Ms` is present.

## 3) Database

- [ ] Ensure Postgres is reachable from API runtime.
- [ ] Start API once to create tables.
- [ ] Validate writes to `sessions`, `messages`, `action_tasks`, `reminder_events`.
- [ ] Verify action gate behavior survives restart (DB-backed context hydration).

## 4) Mobile/Web Client Config

- [ ] Build/run Flutter with:
  - `--dart-define=API_BASE_URL=https://your-api-host`
  - `--dart-define=API_AUTH_TOKEN=your_token`
- [ ] Verify chat shows assistant text from `response_text`.
- [ ] Verify blocker gate and Mark Done flow.

## 5) Notifications

- [ ] Register a device token from client (`/notifications/device-token`).
- [ ] Trigger check-in and verify:
  - reminder event row written
  - Twilio send status (`sent`/`failed`/`mocked`)
  - push send status (`sent`/`failed`/`mocked`)

## 6) CI/CD

- [ ] `release-pipeline.yml` green on:
  - backend tests (Postgres service)
  - Flutter analyze/test
  - Flutter web build
  - Android APK build

## 7) Operational Controls

- [ ] Rotate `API_AUTH_TOKEN` and API keys regularly.
- [ ] Set log retention/monitoring for API and error events.
- [ ] Add rate limiting/WAF before public exposure.
- [ ] Restrict admin/debug access paths in production.
