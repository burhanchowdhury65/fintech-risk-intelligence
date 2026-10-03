# Test report (Person C, frontend). Day 05, updated on Day 06

**Environments.** `Stub` = a local fake backend that follows Person A's documented responses (it is NOT the real backend). `Real` = the real backend and models. Every `Stub` result below was observed in a headless Chromium run against a production build. Nothing in the `Real` column was observed by the assistant.

## Endpoint status

| Endpoint | Frontend use | Status |
|---|---|---|
| `POST /analyze` | Dashboard form, via `/api/analyze` proxy (adds `DEV_JWT`) | Wired. Stub: working. Real: not verified here (Person C reported OK). |
| `POST /aria/chat` | ARIA chat, via `/api/aria/chat` proxy | Wired to the confirmed contract. Stub: working. Real: not verified here. Person A has not captured a real successful analysis-through-chat output. |
| `GET /health` | Not used (header badge is a placeholder; feature freeze) | Exists per Person A. |
| `GET /health/dependencies` | Not used | Schema TBD (Person A). |
| `GET /analysis/{request_id}` | Not used | Not confirmed by Person A. |
| `POST /auth/login` | Not used. Local dev uses a generated `DEV_JWT` | Contract TBD (Person A). |

## Test cases

| # | Test case | Input / setup | Expected | Actual | Status | Owner if not PASS |
|---|---|---|---|---|---|---|
| 1 | Normal transaction (dashboard) | Demo Normal | Result card: Not flagged, Low risk, score `/ 100`, model version, source badge | As expected (Stub) | PASS (Stub) | Real: Person C to confirm |
| 2 | Flagged transaction (dashboard) | Demo Flagged | Flagged, High risk, factors from the response only | As expected (Stub) | PASS (Stub) | Real: Person C to confirm |
| 3 | Invalid input, client | Negative amount | Field error, no result | As expected | PASS | |
| 4 | Invalid input, server | Stub returns 422 `INVALID_INPUT` | "Check the values you entered", no result | As expected (Stub) | PASS (Stub) | |
| 5 | Timeout, dashboard | Upstream slower than the proxy limit (`PROXY_TIMEOUT_MS=3000`, stub 6 s) | Loading ends, "took too long", old result gone, Analyze usable again | As expected (Stub) | PASS (Stub) | Real timeout: Person A |
| 6 | Timeout, real backend | Slow real ML node | Same as #5 | Person A reports a real 504 `ML_NODE_TIMEOUT` test passed. Frontend did not observe it. | BLOCKED | Person C to see it on the real backend |
| 7 | Node unavailable | Stub returns 503 `ML_NODE_UNAVAILABLE` | Error panel with reference ID, no result | As expected (Stub) | PASS (Stub) | Real: Person A (stop the ML node) |
| 8 | Node unavailable, real | Real ML node stopped | Same as #7 | Person A reports a real 503 `ML_NODE_UNAVAILABLE` test passed. Frontend did not observe it. | BLOCKED | Person C to see it on the real backend |
| 9 | Backend unreachable | Backend stopped | "Could not connect", no result | As expected (Stub) | PASS (Stub) | |
| 10 | Cached demo | Demo Cached (mock and live mode) | `CACHED DEMO`, no network call, edited input is never cached | As expected | PASS | |
| 11 | Malformed response | Missing `risk_status` or `is_fraud` | Controlled error, no card | As expected (Stub) | PASS (Stub) | |
| 12 | ARIA analysis | Chat: "Analyze: amount 890, shopping_net, 03:15, 240 km" | Reply + result card from `tool_result`; result panel updated and says it came from chat | As expected (Stub) | PASS (Stub) | Real: Person A, Person C |
| 13 | ARIA normal chat | "What can you help me with?" | Reply, no card, dashboard unchanged | As expected (Stub) | PASS (Stub) | |
| 14 | ARIA ML rejects input | Stub 422 `INVALID_INPUT` | "Couldn't use those details", no Try again, no card | As expected (Stub) | PASS (Stub) | |
| 15 | ARIA server error / unknown LLM error | Stub 500; stub 503 with unknown code | Friendly error, Try again, no card, no raw message | As expected (Stub) | PASS (Stub) | |
| 16 | ARIA timeout | Stub slower than proxy limit | Generic error (not "risk service"), Try again, dashboard untouched | As expected (Stub) | PASS (Stub) | Real latency: Person A |
| 17 | ARIA both LLMs fail, safe fallback | Real failure | Use backend's safe fallback shape | Shape not defined | BLOCKED | Person A |
| 18 | Malformed `tool_result` | Missing `risk_status` | Error, no card, no dashboard update | As expected (Stub) | PASS (Stub) | |
| 19 | Request ID consistency | Chat analysis | Chat card ID equals dashboard "Technical details" ID | `stub-aria-1` in both (Stub) | PASS (Stub) | Real: Person A, Person C |
| 20 | Safe rendering | Reply containing `<img onerror>` and `<script>` | Shown as plain text, no script runs | As expected (Stub) | PASS (Stub) | |
| 21 | Empty / repeated submit | Whitespace, double send, double Analyze | Rejected; one request only | As expected | PASS | |
| 22 | No stale result | Analyze A, then B fails | A is not shown for B | As expected | PASS | |
| 23 | Result vs probability wording | All results | Score shown as `/ 100`, "not a probability" | As expected | PASS | |
| 24 | Layout | 360, 768, 1440 px | No horizontal overflow | No overflow measured; 360 and 1440 viewed | PASS | 768 not viewed |
| 25 | Lint, typecheck, build | `npm run lint`, `typecheck`, `build` (mock and live mode) | No errors | No errors (sandbox) | PASS | Person C to run on own machine |
| 26 | Keyboard walk, screen reader | Tab through the page | Visible focus everywhere | Not run | BLOCKED | Person C |
| 27 | Source badge | Response with `source_mode` LIVE, CACHED, and an unknown value | `LIVE ANALYSIS`; `CACHED DEMO` plus "saved demo result" note; unknown shows "From API", never LIVE | As expected (Stub) | PASS (Stub) | |
| 28 | Backend 3 s cached fallback | Exact cached demo input with a slow ML node | `CACHED DEMO` label | Person A reports a real 200 with `source_mode: "CACHED"`. Frontend label verified only with a stub. | BLOCKED | Person C to see it on the real backend |
| 29 | ARIA real analysis-through-chat | Chat message that runs the analysis tool | Reply plus non-null `tool_result` card | Person A's only real example is a normal chat (`tool_result: null`). No real analysis-through-chat output has been shown. | BLOCKED | Person A |
| 31 | Counterfactual box, found true | Stub returns a counterfactual (amount) | One sentence with the response's numbers, the original score from the result, optional status and reason, the limitation note; no "Sample data" in live mode | As expected (Stub) | PASS (Stub) | |
| 32 | Counterfactual with zero values, other feature | Stub: hour 3 → 0, new score 0 | Zeros shown, not treated as missing | As expected (Stub) | PASS (Stub) | |
| 33 | Counterfactual not found, absent, or incomplete | `found:false`; field absent; `found:true` missing a value | No box; result still shown; no crash | As expected (Stub) | PASS (Stub) | |
| 34 | Counterfactual label missing | Only `changed_feature` | Readable fallback from the feature name; no band badge or reason line | As expected (Stub) | PASS (Stub) | |
| 35 | Counterfactual stale / failed / new transaction / chat result | Edit form; 503; analyze a transaction without one; chat analysis | Box disappears each time; never shown for another transaction | As expected (Stub) | PASS (Stub) | |
| 36 | Counterfactual through the real backend | Flagged demo via real `/analyze` | Sentence with real numbers | Person B shows a real ML-node response (amount 890 → 623, score 99 → 67). The full Frontend → Backend → ML path with Person A passing the field through was not seen. | BLOCKED | Person A (pass-through), Person C to watch it |
| 41 | Counterfactual, Person B's real response shape | Stub replays the real payload: extra fields, `found:true` with amount, and `found:false` with all other fields null | "If transaction amount had been 623 instead of 890, the risk score would have been 67 instead of 99." plus "With that change: medium risk"; the backend reason that repeats the sentence is hidden; null object shows no box; score type and request ID in Technical details | As expected (Stub) | PASS (Stub) | |
| 37 | Very long values | Model version, request ID, factor, counterfactual label and numbers, chat reply, all with no spaces | No horizontal overflow at 360, 768, 1440 px | Overflow found at all widths; fixed with `min-w-0` and wrapping; now none (Stub) | PASS (Stub) | |
| 38 | Infinite amount | Type `1e400` | Field error, no request | As expected | PASS | |
| 39 | Dev-mode console | `npm run dev`, use dashboard and chat | No errors or hydration warnings | None | PASS | |
| 40 | Dependency audit | `npm audit --omit=dev` | No known vulnerabilities | 0 found | PASS | |
| 30 | Responsive QA, 8 states × 3 widths | See `docs/day6-qa-report.md` | No overflow, clipping, small tap targets or small text | 24/24 clean | PASS | |

## Known gaps (all backend or verification, none are open UI features)
- Person A: real `/aria/chat` success output, dedicated LLM-failure response, latency numbers (frontend timeouts are provisional: proxy 30 s analyze, 60 s ARIA; browser 40 s and 70 s), `source_mode`, `score_type`, `explanation`, and a login flow to replace `DEV_JWT`.
- Person B: risk bands (0–39, 40–69, 70–100) are still provisional.
- Person C: run `npm run build` and the real-backend checks on the project machine.

## Feature freeze (Day 05, still in force)
No new UI features were added on Day 05. Changes were limited to fixes: ARIA timeouts are no longer labelled as an ML-node timeout, and an optional `PROXY_TIMEOUT_MS` server variable lets QA trigger timeouts quickly. Not built because of the freeze: backend health badge (`/health`), analysis lookup (`/analysis/{request_id}`), Bangla/English toggle, Sector Node.
