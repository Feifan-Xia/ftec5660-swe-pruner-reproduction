"""Frozen 131-observation skimmer fidelity experiment; local GPU, no paid API."""
import hashlib
import json
import time
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "runs/full/diagnostics/author_all_replay"


def main():
    FOLDER.mkdir(parents=True, exist_ok=True)
    questions = [json.loads(s)["question"] for s in (ROOT / "upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl").read_text(encoding="utf-8").splitlines()]
    indices = json.loads((ROOT / "revision_precision/protocol.json").read_text(encoding="utf-8"))["question_indices"]
    archive = ROOT / "runs/author_evidence/swepruner-sweqa-reproduce.zip"
    jobs = []
    with zipfile.ZipFile(archive) as z:
        ts = {t["question"]: (name, t) for name in z.namelist() if name.startswith("traj-full-glm-pruner/streamlink/") and name.endswith(".traj.json") for t in [json.loads(z.read(name))]}
        for index in indices:
            member, t = ts[questions[index]]
            for n, e in enumerate(t["events"]):
                o = e.get("observation", {})
                if o.get("pruned"):
                    jobs.append(dict(index=index, event=n, member=member, observation=o))
    assert len(jobs) == 131
    protocol = {"version": 1, "question_indices": indices, "observations": 131, "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "threshold": .5, "parameter_dtype": "torch.float32", "input_padding": 8192,
                "inputs": "Every saved pruned observation and exact author hint from all eight fixed questions, including unchanged, small, and timeout outputs.",
                "primary_metrics": ["exact text agreement", "weighted raw-output token compression", "per-question compression"],
                "scope": "Teacher-forced component fidelity. Author actions and hints fixed; autonomous end-to-end token saving and answer quality require separate online tests.",
                "selection": "All 131 eligible observations fixed before replay; no outcome-dependent omissions; infrastructure retries preserve failed records.",
                "paid_api_calls": 0}
    target = FOLDER / "protocol.json"
    if target.exists(): assert json.loads(target.read_text(encoding="utf-8")) == protocol
    else: target.write_text(json.dumps(protocol, indent=2), encoding="utf-8")
    with httpx.Client(trust_env=False, timeout=600) as client:
        health = client.get("http://127.0.0.1:8000/health").json()
        assert health["dtype"] == "torch.float32" and health["input_padding"] == 8192, health
        (FOLDER / "service_health.json").write_text(json.dumps(health, indent=2), encoding="utf-8")
        records = []
        for j in jobs:
            target = FOLDER / f'q{j["index"]}_e{j["event"]}.json'
            o = j["observation"]; info = o["prune_info"]
            request = {"query": info["context_focus_question"], "code": o["original_output"], "threshold": .5}
            signature = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
            if target.exists():
                row = json.loads(target.read_text(encoding="utf-8")); assert row["request_sha256"] == signature
            else:
                started = time.time()
                r = client.post("http://127.0.0.1:8000/prune", json=request); r.raise_for_status(); result = r.json()
                row = {k: j[k] for k in ["index", "event", "member"]}
                row.update(request_sha256=signature, seconds=time.time()-started, author_raw=info["origin_token_cnt"], author_kept=info["left_token_cnt"],
                           local_raw=result["origin_token_cnt"], local_kept=result["left_token_cnt"], exact_text=result["pruned_code"] == o["output"],
                           local_error=result.get("error_msg"), local_output=result["pruned_code"], author_output_sha256=hashlib.sha256(o["output"].encode()).hexdigest())
                target.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
            records.append(row)
            print(f'{len(records)}/131 q{j["index"]} e{j["event"]} exact={row["exact_text"]} kept={row["local_kept"]}/{row["author_kept"]}', flush=True)
    def summarize(rows):
        result = {k: sum(r[k] for r in rows) for k in ["author_raw", "author_kept", "local_raw", "local_kept"]}
        result.update(n=len(rows), exact_text_count=sum(r["exact_text"] for r in rows), local_error_count=sum(bool(r["local_error"]) for r in rows))
        for source in ["author", "local"]:
            result[source + "_compression_percent"] = 100 * (1 - result[source + "_kept"] / result[source + "_raw"])
        return result
    out = {"protocol": protocol, "summary": summarize(records), "per_question": [{"index": i, **summarize([r for r in records if r["index"] == i])} for i in indices], "records": records}
    (ROOT / "results/full/author_all_observations_replay.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
