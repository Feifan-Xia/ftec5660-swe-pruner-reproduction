"""Refresh the overinclusive whole-key bound after all paid requests settle."""
import hashlib
import json
import os
import sqlite3
import socket
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / "runs/full"
auth_path = folder / "budget_authorization.json"
auth = json.loads(auth_path.read_text(encoding="utf-8"))
ledger = folder / "formal_usage.jsonl"
rows = [json.loads(s) for s in ledger.read_text(encoding="utf-8").splitlines()]
assert time.time() - max(r["time"] + r["seconds"] for r in rows) > 60
# Caller must drain and stop its meter first. Reject a live service so a new
# reservation cannot race the snapshot used to reconcile the account.
port_guard = socket.socket()
if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
    port_guard.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
port_guard.bind(("127.0.0.1", 8879))
db = sqlite3.connect("file:" + str(Path.home() / ".cc-switch/cc-switch.db") + "?mode=ro", uri=True)
cfg = json.loads(db.execute("select settings_config from providers where id=?", ("fbd4c8ff-5c35-476d-9a5c-0b065f897e20",)).fetchone()[0])
db.close()
with httpx.Client(trust_env=False, proxy="http://127.0.0.1:7898", timeout=20) as client:
    response = client.get("https://openrouter.ai/api/v1/key", headers={"Authorization": "Bearer " + cfg["auth"]["OPENAI_API_KEY"]})
    response.raise_for_status()
    data = response.json()["data"]
assert data.get("limit_reset") is None and not data.get("byok_usage")
retained = auth["account_bound_reconciliation"]["historical_conservative_retained_usd"] - auth["historical_overlap_reconciliation"]["deduplicated_known_historical_charges_usd"]
known_current = sum(r.get("usage", {}).get("cost", 0) or 0 for r in rows)
known_historical = auth["historical_overlap_reconciliation"]["deduplicated_known_historical_charges_usd"]
assert data["usage"] >= known_current + known_historical - 1e-8, "Account receipt has not settled or scope differs"
gross = sum(r["cost"] for r in rows)
old = auth["prior_stage_conservative_usd"] + gross
new = retained + data["usage"]
record = {"time": time.time(), "key_lifetime_usage": data["usage"], "historical_unresolved_and_non_OR_bound_retained": retained,
          "known_current_receipts": known_current, "known_historical_receipts": known_historical,
          "old_project_bound": old, "new_project_bound": new, "released_bound": max(0, old-new),
          "ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
          "covered_request_ids": [r["request_id"] for r in rows],
          "basis": "Entire same-key lifetime usage bounds all project OR generations, including post-send failures. Retain historical unresolved/non-OR allowance. No individual failed request is assigned zero. Meter stopped; at least 60 seconds since last request."}
if new < old:
    auth["prior_stage_conservative_usd"] -= old-new
    auth["meter_limit_usd"] += old-new
    auth.setdefault("account_bound_refreshes", []).append(record)
    assert abs(auth["prior_stage_conservative_usd"] + auth["meter_limit_usd"] + auth["margin_usd"] - 12) < 1e-8
    temp = auth_path.with_suffix(".tmp")
    temp.write_text(json.dumps(auth, indent=2), encoding="utf-8"); os.replace(temp, auth_path)
target = ROOT / "results/full/account_bound_refresh.json"
target.write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in record.items() if k != "covered_request_ids"}, indent=2))
