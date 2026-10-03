# Day 07: demo readiness (Person C, frontend)

## What was checked on Day 07 (sandbox, headless Chromium, stub backend)
| Check | Result |
|---|---|
| `npm run lint`, `npm run typecheck`, `npm run build` (mock and live mode) | PASS |
| `npm run dev` startup, console errors and warnings while using the dashboard and chat | PASS (none) |
| Dependency audit, production packages (`npm audit --omit=dev`) | PASS (0 vulnerabilities) |
| Secret scan of the repository (tokens, API keys) | PASS (none found; `.env*` is git-ignored, `.env.example` has no secrets) |
| Dashboard, ARIA chat, counterfactual box, cached demo, errors, timeouts, safe rendering (full suites, mock and live) | PASS |
| Responsive QA, 8 states × 3 widths | PASS (24/24) |
| Very long values (model version, request ID, factor text, counterfactual numbers and label, chat reply) at 360, 768, 1440 px | **Found a bug, fixed, now PASS** |
| Infinite number typed as the amount (`1e400`) | PASS (rejected with a field error) |

## P0 bug found and fixed on Day 07
Very long text with no spaces made the page scroll sideways at every width, because grid columns could not shrink. Fix: the two grid columns now may shrink (`min-w-0`) and result, factor, counterfactual and chat text wraps anywhere. No design change.

## Not verified (needs a person or the real backend)
- Everything against the **real** backend and models. The assistant only used a stub that follows Person A's documented responses.
- Counterfactual with real data (Person B builds it, Person A passes it through).
- Real analysis-through-chat output (Person A has shown only a normal chat so far).
- Keyboard walk with Tab, screen readers, real phones, browsers other than Chromium.
- `npm run build` on the project machine.
- **Deployment was not done.** No staging URL or auth plan exists yet.

## Demo-day runbook
1. Start the backend and the ML node. Generate a fresh token (they last 60 minutes).
2. `frontend/.env.local`: `NEXT_PUBLIC_USE_MOCK_API=false`, `NEXT_PUBLIC_API_BASE_URL=<backend>`, `DEV_JWT=<token>`.
3. `npm run build` then `npm run start` (or `npm run dev`). Open http://localhost:3000. The header should say "Backend status: not checked" (not "Mock mode").
4. Run **Demo: Normal** and **Demo: Flagged** once before the audience arrives. Look for the `LIVE ANALYSIS` badge. If it says `From API`, the backend is not sending `source_mode`; that is still a live result.
5. Follow `docs/demo-script.md`.

## If something breaks during the demo
| Problem | What to do |
|---|---|
| "Could not connect to the analysis service" | Backend not running or wrong URL. Start it, check `NEXT_PUBLIC_API_BASE_URL`, rebuild or restart. |
| Error mentioning the token, or an unexpected-result message in development | Token expired. Generate a new `DEV_JWT`, restart the app. |
| Backend cannot be fixed in time | Set `NEXT_PUBLIC_USE_MOCK_API=true`, restart or rebuild, and say clearly that the screen shows sample data (the header says "Mock mode"). |
| Counterfactual box missing | Normal. It appears only if the backend returns one. Skip that step. |
| ARIA error | Say that the AI assistant is a separate service; the risk result above still works. Use "Try again" once. |

## Owners of what is left
| Item | Owner |
|---|---|
| Real chain test with the real backend and models; real analysis-through-chat output | Person A (and Person C to watch it on screen) |
| Staging URL, deployment auth plan (replace `DEV_JWT`), secret-safe log audit | Person A |
| Counterfactual in the real response; risk bands final or provisional | Person B |
| Backup demo video, `npm run build` on own machine, Tab walk | Person C |
