# Risk Intelligence: Frontend

Next.js (App Router) + TypeScript + Tailwind CSS v4 frontend for the Fintech Risk Intelligence project.

## Run

Needs Node.js 20.9 or newer.

```bash
npm install
cp .env.example .env.local   # then edit it (see "Environment variables")
npm run dev                  # http://localhost:3000
```

The default is **mock mode**: sample data, no backend needed, clearly labelled "Mock mode" and "Mock result".

## Environment variables

| Name | Where | Meaning |
|---|---|---|
| `NEXT_PUBLIC_USE_MOCK_API` | `.env.local` | `false` = use the real backend. Anything else = mock mode. |
| `NEXT_PUBLIC_API_BASE_URL` | `.env.local` | Backend URL, default `http://127.0.0.1:8000`. |
| `DEV_JWT` | `.env.local` (server only) | Development token for live mode. Never commit it. Expires in 60 minutes. |
| `PROXY_TIMEOUT_MS` | `.env.local` | QA only: shortens the proxy timeout. |

**Important:** `NEXT_PUBLIC_*` values are fixed when the app is built. After changing them, restart `npm run dev`, or run `npm run build` again before `npm run start`. `.env.local` is ignored by git; only `.env.example` is committed.

**Deployment warning:** the `/api/analyze` and `/api/aria/chat` routes add `DEV_JWT` to every request they forward. They are for local development and a controlled demo only. Do not put them on a public URL with a real token.

## Scripts

- `npm run dev`: development server
- `npm run build` / `npm run start`: production build and server
- `npm run lint`: ESLint
- `npm run typecheck`: TypeScript check

## Structure

- `app/`: routes, layout, global styles and design tokens (`globals.css`)
- `components/ui`: Button, Card, Badge
- `components/layout`, `transaction`, `risk`, `aria`: feature components
- `lib/types/api.ts`: API types (source: Person A's API contract)
- `lib/config.ts`: API base URL

## Mock mode (Day 2)

`NEXT_PUBLIC_USE_MOCK_API` is on unless set to `false`. All sample data lives in `lib/mock/`; the UI calls only `lib/api/analyze.ts`.
Live mode is wired for `POST /analyze` only; confirm the TBD fields in `lib/types/api.ts` as they lock.

## Live mode (real backend, dev only)

1. Start the backend on `http://127.0.0.1:8000` and generate a dev token (see Person A).
2. In `.env.local`: `NEXT_PUBLIC_USE_MOCK_API=false` and `DEV_JWT=<token>`.
3. Restart `npm run dev`. The browser calls `/api/analyze`, which forwards to the backend with the token.

## ARIA chat

- **Mock mode** (default): `lib/mock/mockAria.ts` gives template replies and `lib/mock/parseTransaction.ts` reads details from text. Labelled "Preview".
- **Live mode** (`NEXT_PUBLIC_USE_MOCK_API=false`): `lib/api/aria.ts` calls `/api/aria/chat`, a server proxy (adds `DEV_JWT`) to backend `POST /aria/chat` with `{ message, language }`. Response: `{ reply, provider, session_id, tool_result }`.
  - A result card is shown only for a valid, non-null `tool_result` (same fields as `/analyze`). The reply text is never parsed.
  - A chat analysis also updates the result panel, which then says it came from the chat (the form is not changed, because `tool_result` has no inputs).
  - Still TBD with Person A: error shape when both LLM providers fail, latency (timeouts are provisional: 60 s proxy, 70 s browser), `source_mode`, follow-up for missing fields.
- Chat is kept in memory only (nothing is stored in the browser).

## Counterfactual insight box

`components/risk/CounterfactualBox.tsx` shows "What Would Change This Result?" under the result card when the response has `counterfactual.found === true`. `lib/api/counterfactual.ts` validates the object (incomplete objects are dropped). The type is `Counterfactual` in `lib/types/api.ts`. In mock mode only the flagged demo carries a counterfactual: a copy of the real output Person B confirmed for that input (marked "Sample data"). A backend `reason` that only repeats the two values is hidden.

## Docs

`docs/day5-test-report.md` (test cases and status), `docs/day6-qa-report.md` (responsive QA), `docs/demo-script.md`, `docs/known-limitations.md`, `docs/demo/` (screenshots, mock mode), `docs/day7-demo-readiness.md` (final status, demo-day runbook, what is left and who owns it).

## Status

Day 6: dashboard (form, demo inputs, loading, success, cached demo, validation and service errors) and ARIA chat, in mock mode and in live mode through the dev proxies. No login screen yet (`DEV_JWT`, development only). See `docs/known-limitations.md`.
