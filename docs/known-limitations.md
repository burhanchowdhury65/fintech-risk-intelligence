# Known Limitations

- Local development uses a generated `DEV_JWT` for authentication.
- `DEV_JWT` is for development/demo use only and should not be deployed to a public URL.
- The current local demo does not include a production login screen.
- The ML/Risk node must be available for live analysis.
- If the ML/Risk node times out, only the predefined exact-match demo transaction receives the cached fallback response.
- Other transactions return a timeout/service error instead of using arbitrary cached results.
- LLM provider fallback depends on the configured secondary provider and API key.
- Secret values such as JWTs and API keys must not be committed to Git or printed in logs.
- Demo behavior depends on the local environment configuration and running backend/model services.
