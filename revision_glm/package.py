"""Create a byte-preserved, secret-checked submission archive for the revised study."""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def credential_literals():
    values = []
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                if any(word in key.upper() for word in ["KEY", "TOKEN", "SECRET"]):
                    values.append(value.strip().strip("\"'"))
    if os.getenv("OPENROUTER_API_KEY"):
        values.append(os.environ["OPENROUTER_API_KEY"])
    database = Path.home() / ".cc-switch/cc-switch.db"
    if database.exists():
        connection = sqlite3.connect("file:" + str(database) + "?mode=ro", uri=True)
        for provider_id in [
            "fbd4c8ff-5c35-476d-9a5c-0b065f897e20",
            "1e6c5741-eb82-40e7-9204-ea67d50d7e68",
        ]:
            row = connection.execute(
                "select settings_config from providers where id=?", (provider_id,)
            ).fetchone()
            if row:
                value = json.loads(row[0]).get("auth", {}).get("OPENAI_API_KEY")
                if value:
                    values.append(value)
        connection.close()
    return [value.encode() for value in set(values) if len(value) >= 16]


def main():
    subprocess.run(
        [sys.executable, str(ROOT / "revision_glm/audit.py")], check=True, cwd=ROOT
    )
    if subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True
    ).strip():
        raise RuntimeError("Commit the reviewed tracked changes before packaging")
    for name in ["SWE-Pruner_report_zh.pdf", "SWE-Pruner_report_en.pdf"]:
        if not (ROOT / "report/glm" / name).exists():
            raise RuntimeError("Both final reports are required")
    secrets = credential_literals()
    history = subprocess.check_output(
        ["git", "log", "--all", "-p", "--format="], cwd=ROOT
    )
    if any(secret in history for secret in secrets):
        raise RuntimeError(
            "Configured credential found in Git history; inspect without printing it"
        )
    tracked = subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True
    ).splitlines()
    paths = []
    for name in tracked:
        if name in ["PROJECT_STATUS.md", "DEBUG_DIARY.md"]:
            continue
        if name.startswith("report/") and not name.startswith("report/glm/"):
            continue
        if name.startswith("results/") and not name.startswith("results/glm/"):
            continue
        if "/layout_preview/" in name or "preview_page" in name:
            continue
        paths.append(ROOT / name)
    paths += [path for path in (ROOT / "runs/glm/pinned").rglob("*") if path.is_file()]
    for name in [
        "attention_validation.json",
        "attention_fusion_only_partial.json",
        "pruner_numerical_validation.json",
        "integration_check.json",
        "integration_observations.json",
        "usage.jsonl",
        "judge_usage.jsonl",
        "formal_usage.jsonl",
        "model_catalog_entry.json",
        "judge_catalog_entry.json",
        "formal_model_catalog.json",
    ]:
        path = ROOT / "runs/glm" / name
        if path.exists():
            paths.append(path)
    for name in ["STOP_REASON.json", "runtime_manifest.json"]:
        path = ROOT / "runs/glm/formal" / name
        if path.exists():
            paths.append(path)
    for name in [
        "formal/recovery/q30_r0/attempt0/console.log",
        "formal/recovery/q30_r0/attempt0/qualification.json",
        "pilot/pruner/q17_r0/console.log",
    ]:
        path = ROOT / "runs/glm" / name
        if path.exists():
            paths.append(path)
    aliases = {
        "third_party/SWE-Pruner-LICENSE": ROOT / "upstream/LICENSE",
        "third_party/Streamlink-LICENSE": ROOT / "data/streamlink/LICENSE",
        "legacy/deepseek_budget_audit.json": ROOT / "results/evidence_audit.json",
    }
    tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    history_path = release / f"glm-history-{tag}.bundle"
    subprocess.run(
        ["git", "bundle", "create", str(history_path), "--all"], cwd=ROOT, check=True
    )
    subprocess.run(
        ["git", "bundle", "verify", str(history_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    aliases["repository-history.bundle"] = history_path
    entries = {path.relative_to(ROOT).as_posix(): path for path in paths}
    entries.update({name: path for name, path in aliases.items() if path.exists()})
    manifest = []
    archive = release / f"SWE-Pruner-GLM-submission-{tag}.zip"
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for name, path in sorted(entries.items()):
            if name.startswith("runs/network_glm/") or (
                Path(name).name.startswith(".env") and Path(name).name != ".env.example"
            ):
                raise RuntimeError("Private configuration entered the allowlist")
            data = path.read_bytes()
            if any(secret in data for secret in secrets):
                raise RuntimeError("Configured credential found in " + name)
            output.writestr(name, data)
            digest = hashlib.sha256(data).hexdigest()
            manifest.append(
                {
                    "path": name,
                    "bytes": len(data),
                    "sha256": digest,
                    "source_sha256": digest,
                }
            )
        metadata = {
            "draft": False,
            "git_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "experiment_revision": json.loads(
                (ROOT / "runs/glm/pinned/formal/runtime_manifest.json").read_text()
            )["git_revision"],
            "transformation": "All included source, reports and raw evidence retain their exact local bytes. Private proxy configuration, databases, API keys, model weights and unrelated historical reports are excluded.",
            "files": manifest,
        }
        output.writestr("MANIFEST.json", json.dumps(metadata, indent=2).encode())
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_bundle.py"), str(archive)],
        check=True,
        cwd=ROOT,
    )
    (release / "LATEST_GLM.json").write_text(
        json.dumps(
            {
                "archive": str(archive),
                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "files": len(manifest),
            },
            indent=2,
        )
    )
    print(
        f"Created {archive} ({archive.stat().st_size/2**20:.2f} MiB, {len(manifest)} files)"
    )


if __name__ == "__main__":
    main()
