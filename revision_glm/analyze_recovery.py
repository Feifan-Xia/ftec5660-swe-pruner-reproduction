"""Identify newly exposed nonblank lines in each autonomous expansion."""

import json
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    rows = read(ROOT / "results/glm/cells.json")
    records = []
    for row in rows:
        if row["mode"] != "recovery":
            continue
        directory = ROOT / row["path"]
        store_path = directory / "observations.json"
        if not store_path.exists():
            continue
        store = read(store_path)
        displays = {}
        successful = list(store["reads"])
        for path in (directory / "trajectories/streamlink").glob("*.traj.json"):
            for event in read(path)["events"]:
                if event.get("type") == "ObservationEvent":
                    observation = event.get("observation", {})
                    text = observation.get("content", "")
                    if observation.get("pruned") and "original_output" in observation:
                        observation_id = (
                            "obs_"
                            + hashlib.sha256(
                                observation["original_output"].encode()
                            ).hexdigest()[:16]
                        )
                        displays[observation_id] = observation["output"]
                    found = re.search(
                        r"Original output saved as (obs_[0-9a-f]+),", text
                    )
                    if found:
                        displays[found[1]] = text
                action = event.get("action", {})
                if action.get("kind") != "ExpandAction":
                    continue
                key = (action["observation_id"], action["start"], action["end"])
                match = next(
                    (
                        r
                        for r in successful
                        if (r["observation_id"], r["start"], r["end"]) == key
                    ),
                    None,
                )
                if match is None:
                    continue
                successful.remove(match)
                previous = displays.get(key[0])
                original = store["observations"][key[0]].splitlines()
                returned = original[key[1] - 1 : key[2]]
                nonblank = [
                    line.strip()
                    for line in returned
                    if (
                        line.split("\t", 1)[1] if re.match(r"^\s*\d+\t", line) else line
                    ).strip()
                ]
                shown = (
                    {line.strip() for line in previous.splitlines()}
                    if previous is not None
                    else set()
                )
                novel = [line for line in nonblank if line not in shown]
                records.append(
                    {
                        "index": row["index"],
                        "repeat": row["repeat"],
                        "attempt": row["attempt"],
                        "path": row["path"],
                        "score": row["score"],
                        **match,
                        "prior_display_found": previous is not None,
                        "nonblank_returned_lines": len(nonblank),
                        "lines_absent_from_previous_display": (
                            len(novel) if previous is not None else None
                        ),
                        "absent_line_examples": novel[:12],
                    }
                )
    output = {
        "scope": "Exact stripped-line comparison with the latest display of the same observation ID. This measures newly exposed text, not causal use by the model.",
        "reads": records,
        "successful_reads": len(records),
        "reads_exposing_new_lines": sum(
            (r["lines_absent_from_previous_display"] or 0) > 0 for r in records
        ),
        "unmatched_prior_displays": sum(not r["prior_display_found"] for r in records),
    }
    (ROOT / "results/glm/recovery_trace_analysis.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )
    print({k: v for k, v in output.items() if k not in ["scope", "reads"]})


if __name__ == "__main__":
    main()
