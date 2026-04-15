# BridgeBack Flutter Client

## Run

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

For iOS simulator/web, replace base URL with your reachable backend host.

## Structure

- `lib/core` shared routing, theme, API client, session provider
- `lib/features/onboarding` onboarding and consent
- `lib/features/chat` coaching + blocker gate
- `lib/features/plan` action lifecycle controls
- `lib/features/progress` score and action metrics
- `lib/features/settings` local app settings
