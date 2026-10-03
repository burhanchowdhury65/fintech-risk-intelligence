# Demo script (about 4 minutes)

## Before you start
- Backend and ML node running. `frontend/.env.local`: `NEXT_PUBLIC_USE_MOCK_API=false`, a fresh `DEV_JWT` (it expires after 60 minutes). Restart `npm run dev` (or `npm run build && npm start`) after changing it.
- Browser at 100% zoom. Open DevTools → Network only if you want to show the live call.
- If the backend is down: set `NEXT_PUBLIC_USE_MOCK_API=true` and say clearly that the screen shows sample responses (the header says "Mock mode").

## Flow
1. **Purpose (20 s).** "You enter a transaction. A machine-learning model returns a 0 to 100 risk score, and ARIA explains it." Point to the banner: the model was trained on simulated data, not real financial records.
2. **Normal case (40 s).** Click **Demo: Normal Transaction** → Analyze. Show: Not flagged, Low risk, score `0 / 100`, model version, and the source badge. The badge says `From API` until the backend returns `source_mode: "LIVE"`; it only says `LIVE ANALYSIS` when the backend sends that value. Say: "The score is a relative ranking, not a probability."
3. **Flagged case (40 s).** Click **Demo: Flagged Transaction** → Analyze. Show: Flagged by model, High risk, `99 / 100`, the three factors the model returned (amount unusually high, far from home, unusual hour). Scroll to Model limitations.
3b. **Optional: "What would change this result?" (20 s).** Person B verified that the flagged demo gets a real counterfactual, but it only appears if `/analyze` passes it through. Under the result you should see: "If transaction amount had been 623 instead of 890, the risk score would have been 67 instead of 99" (medium risk). Say: "This is a one-feature illustration over a fixed set of tested values, not a guarantee." Do not say that lowering the amount always fixes it; other transactions can flip through another feature. If no box appears, skip this step. In mock mode the box is marked "Sample data", so do not present it as a live result.
4. **ARIA (60 s).** In the chat click **Analyze: amount 890, shopping_net, 03:15, 240 km** (or type it). Show: ARIA's reply, the result card below it, and the result panel updating to the same request ID. Say: "ARIA explains. The risk model's result is the source of truth, and ARIA cannot change the score."
5. **Cached fallback (30 s).** Click **Demo: Cached Demo** → Analyze. Show the `CACHED DEMO` label. Say: "This one fixed demo input always shows a saved result, clearly labelled CACHED DEMO. It is not calculated just now. Any other transaction is always analyzed live, and a new transaction never gets an old result." (The app shows the saved result for this exact input without calling the backend. The backend's own 3-second cached fallback is not what you see here.)
6. **Failure honesty (optional, 30 s).** With Person A, stop the ML node and click Analyze: the screen says the service is unavailable and shows no result.
7. **Close (20 s).** Limitations and metrics (below).

## Exact demo inputs (confirmed by Person B)
| Case | amount | merchant_category | time | distance | Expected |
|---|---|---|---|---|---|
| Normal | 45.00 | grocery_pos | 2026-09-28 14:30 | (empty) | score 0, low, no factors |
| Flagged | 890.00 | shopping_net | 2026-09-28 03:15 | 240 | score 99, high, 3 factors |
| Cached | 128.50 | grocery_pos | 2026-09-28 14:30 | 3.2 | score 0, low, no factors |

The demo buttons fill these in. `transaction_type` is "purchase" (required by the API, ignored by the model).

## Metrics line (from Person B, held-out test set, run once)
"On about 552,000 held-out transactions, the model caught 93% of real fraud cases (recall) while about 4 in 10 of its fraud alerts were true fraud (precision 41%). That trade-off favours catching more fraud over fewer false alarms." Full numbers: precision 0.41, recall 0.93, F1 0.57, PR-AUC 0.88.

## Do not say
- "87% probability of fraud" (the score is not a probability).
- That the data is real financial data.
- That the factors are a formal explanation method (they are simple rule-based hints).
- That a cached result is a live analysis.
