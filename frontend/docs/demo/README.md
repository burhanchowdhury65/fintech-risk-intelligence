# Demo screenshots

**These screenshots were taken in mock mode** (the header says "Mock mode: sample data" and result badges say "Mock result"). They use the approved synthetic demo transactions and show every screen and state, but they are **not** real model output. The numbers on the ARIA screenshot (score 90) come from the mock text matching, not from the model.

Before the final demo, replace the ones marked "recapture" with live captures from the real backend.

| File | Screen / state | Recapture with real backend? |
|---|---|---|
| `01-dashboard-and-disclosure.png` | Main dashboard and the synthetic-data disclosure | No (identical in live mode, except the header badge) |
| `02-transaction-input-form.png` | Input form with the demo selector, Normal demo loaded | No |
| `03-successful-analysis-normal.png` | Normal result: not flagged, low risk, score `/ 100`, model version | **Yes** |
| `04-flagged-score-factors-limitations.png` | Flagged result with factors and the limitations text | **Yes** |
| `05-aria-chat-structured-result.png` | ARIA chat with a structured result card | **Yes** (real ARIA reply and `tool_result`) |
| `06-loading-state.png` | Loading state | No |
| `07-service-error-state.png` | Service unavailable, no result shown | **Yes** (stop the ML node) |
| `08-cached-demo-state.png` | `CACHED DEMO` label | No |
| `09-validation-error-state.png` | Invalid input feedback | No |
| `10-mobile-360-full-page.png`, `11-mobile-360-result.png` | 360 px phone layout | Optional |

Not captured: the counterfactual box. The real backend does not return one yet, and the only data available is an invented sample.

## How to capture real screenshots
1. Start the backend and ML node. Set `.env.local`: `NEXT_PUBLIC_USE_MOCK_API=false`, `DEV_JWT=<fresh token>`. Restart the app.
2. Open http://localhost:3000. The header must NOT say "Mock mode", and results should say `LIVE ANALYSIS` (or `From API`).
3. Use the exact inputs in `docs/demo-script.md` (the demo buttons fill them in).
4. Capture with the browser: DevTools → Ctrl+Shift+P → "Capture node screenshot" (select the card) or "Capture full size screenshot".
5. Do not include the token, the Network tab headers, or your `.env.local` in any screenshot.
6. Save under the same names in this folder.
