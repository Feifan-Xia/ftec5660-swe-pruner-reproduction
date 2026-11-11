"""Replay a recorded pruning case and execute exact recovery locally for recording."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from observation_store import ObservationStore


def main():
    case_path = ROOT / "runs/recovery/mechanism/case1.json"
    case = json.loads(case_path.read_text(encoding="utf-8"))
    source = case["source"]
    assert hashlib.sha256(source.encode()).hexdigest() == case["source_sha256"]
    pruned = case["prune"]["pruned_code"]
    print("RECORDED SKIMMER OUTPUT + LIVE LOCAL RECOVERY")
    print(f"Source: {case['path']}; saved source SHA-256 verified")
    print(
        "Original goal: Which imported modules and classes does this plugin depend on?"
    )
    print(
        f"Source tokens: {case['prune']['origin_token_cnt']} -> {case['prune']['left_token_cnt']}"
    )
    print("First lines of the recorded pruned observation:")
    print("\n".join(pruned.splitlines()[:8]))
    print(f"New goal: What is the exact value of {case['constant']}?")
    print(f"Exact value visible in pruned text: {case['expected'] in pruned}")

    store = ObservationStore()
    observation_id = store.put(source)
    start, end = max(1, case["target_line"] - 2), case["target_line"] + 2
    print(f"Scripted demonstration range: expand({observation_id}, {start}, {end})")
    recovered = store.expand(observation_id, start, end)
    print(recovered)
    assert recovered == "".join(source.splitlines(keepends=True)[start - 1 : end])
    assert case["expected"] in recovered
    print("PASS: exact original characters recovered; requested constant is visible.")
    print(json.dumps(store.reads, indent=2))
    print(
        "The agent-selected ranges and answers are retained in mechanism/recoverable/."
    )


if __name__ == "__main__":
    main()
