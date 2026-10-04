"""
verify_demo_cases.py — Day 7 (Person B). Re-checks the frozen demo cases against a RUNNING node.

  python verify_demo_cases.py                 # uses http://127.0.0.1:8001
  python verify_demo_cases.py http://host:port

Expected values in day7_demo_cases.json were captured from the real model (not hardcoded).
Compared fields: HTTP status, is_fraud, risk_score, risk_status, model_version, model_factors,
counterfactual (all sub-fields except 'reason' text, which is compared too). request_id /
transaction_id are ignored. Exit code 0 = all match, 1 = any mismatch.
"""
import json, sys, pathlib, requests
base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
cases = json.loads((pathlib.Path(__file__).parent / "day7_demo_cases.json").read_text())["cases"]
bad = 0
for c in cases:
    r = requests.post(base + "/predict", json=c["request"], timeout=5)
    ok = r.status_code == c["expected_http_status"]
    if ok and r.status_code == 200:
        got = {k: v for k, v in r.json().items() if k not in ("request_id", "transaction_id")}
        ok = got == c["expected_response"]
    elif ok and r.status_code == 422:
        ok = r.json()["detail"][0]["loc"] == c["expected_error_loc"]
    print(("PASS" if ok else "FAIL"), c["id"], "-", c["title"], f"(HTTP {r.status_code})")
    bad += (not ok)
print(f"\n{len(cases)-bad}/{len(cases)} demo cases match")
sys.exit(1 if bad else 0)
