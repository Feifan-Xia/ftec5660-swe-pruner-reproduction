"""Preserve code/reference disagreements without changing official scores."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/paper-workspace/swe-repos/streamlink"
questions = [json.loads(s) for s in (ROOT / "upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl").read_text(encoding="utf-8").splitlines()]

def excerpt(name, start, end):
    p = SOURCE / name
    content = p.read_bytes()
    lines = content.decode().splitlines()
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(content).hexdigest(), "start": start, "end": end,
            "text": "\n".join(f"{i}: {lines[i-1]}" for i in range(start, end+1))}

rows = [
    {"index": 17, "reference": questions[17]["ground_truth"],
     "finding": "The reference says fail_unhandled_requests=True raises CDPError and terminates the session. The normal fallback dispatches fail_request, which sends Fetch.failRequest with BlockedByClient and records the handled ID. The matching test expects fail_request. Generic transport/protocol errors remain possible; the flag alone does not implement the reference's unconditional exception.",
     "source": [excerpt("src/streamlink/webbrowser/cdp/client.py", 363, 377), excerpt("src/streamlink/webbrowser/cdp/client.py", 436, 449), excerpt("tests/webbrowser/cdp/test_client.py", 893, 943)]},
    {"index": 26, "reference": questions[26]["ground_truth"],
     "finding": "The reference describes main_js_url_re and user_id_re scanning the same JavaScript content. The code applies main_js_url_re to the initial HTML response, then replaces res with the downloaded JavaScript response before user_id_re. O(m*n) repeated scans describe a hypothetical workload, not these two searches on one current input. Both generated answers also contain unsupported regex-performance generalizations.",
     "source": [excerpt("src/streamlink/plugins/n13tv.py", 25, 27), excerpt("src/streamlink/plugins/n13tv.py", 123, 148)]}
]
out = {"scope": "Post-hoc source audit of the two lower-scoring development questions. Preserve all official scores, all three questions, and the failed predeclared gate. No corrected aggregate or retroactive exclusion.",
       "source_commit": "ab1f36560005253ca6a290a614730bf18a29a7f9", "rows": rows}
(ROOT / "results/full/development_reference_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("Preserved two code/reference disagreements; official scores unchanged.")
