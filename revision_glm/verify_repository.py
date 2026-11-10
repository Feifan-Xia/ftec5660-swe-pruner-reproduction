"""Verify the read-only agent snapshot against the pinned Git archive (run in WSL)."""

import hashlib
import io
import json
import os
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    repository = ROOT / "data/streamlink"
    snapshot = Path(
        os.environ.get(
            "FTEC_CLEAN_REPO",
            str(Path.home() / "ftec5660-swe-pruner/glm-repository/streamlink"),
        )
    )
    selection = json.loads(
        (ROOT / "configs/task_selection.json").read_text(encoding="utf-8")
    )
    revision = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", selection["repo_commit"]], text=True
    ).strip()
    archive = subprocess.check_output(
        ["git", "-C", str(repository), "archive", revision]
    )
    errors, hashes, links = [], {}, {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source:
            target = snapshot / member.name
            if member.isfile():
                expected = source.extractfile(member).read()
                hashes[member.name] = hashlib.sha256(expected).hexdigest()
                if not target.is_file() or target.read_bytes() != expected:
                    errors.append(member.name)
            elif member.issym():
                links[member.name] = member.linkname
                if not target.is_symlink() or os.readlink(target) != member.linkname:
                    errors.append(member.name)
    extra = sorted(
        str(p.relative_to(snapshot))
        for p in snapshot.rglob("*")
        if p.is_file()
        and str(p.relative_to(snapshot)) not in hashes
        and str(p.relative_to(snapshot)) not in links
    )
    result = {
        "status": "PASS" if not errors and not extra else "FAIL",
        "revision": revision,
        "files": len(hashes),
        "mismatches": errors,
        "extra_files": extra,
        "symlinks": links,
        "file_sha256": hashes,
    }
    output = ROOT / "results/glm/repository_snapshot_audit.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print({k: v for k, v in result.items() if k != "file_sha256"})
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
