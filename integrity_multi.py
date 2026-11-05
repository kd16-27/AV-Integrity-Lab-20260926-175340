"""Cross-platform, offline, multi-file semantic JSON integrity checker.

Tracks file additions/removals and nested value changes without reporting values.
The baseline itself is sensitive and must be stored securely, outside Git.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys


class ScopeError(ValueError):
    pass


def _safe(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ScopeError(f"Unsafe relative path: {name!r}")
    p = root / name
    if not p.resolve().is_relative_to(root.resolve()):
        raise ScopeError(f"Path escapes project: {name}")
    candidate = p
    while candidate != root:
        if candidate.is_symlink():
            raise ScopeError(f"Symlink not permitted: {name}")
        candidate = candidate.parent
    return p


def _hash(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _pointer(part: str) -> str:
    return part.replace("~", "~0").replace("/", "~1")


def flatten(value: object, path: str = "") -> dict[str, str]:
    """Hash leaves (and empty containers), keyed by JSON pointer."""
    if isinstance(value, dict) and value:
        result = {}
        for k, item in value.items():
            result.update(flatten(item, path + "/" + _pointer(k)))
        return result
    if isinstance(value, list) and value:
        result = {}
        for i, item in enumerate(value):
            result.update(flatten(item, path + "/" + str(i)))
        return result
    return {path or "/": _hash(value)}


def load_scope(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("files", []), list) or not isinstance(data.get("directories", []), list):
        raise ScopeError("Scope requires files and directories arrays")
    if not data.get("files") and not data.get("directories"):
        raise ScopeError("Scope needs at least one file or directory")
    if not all(isinstance(s, str) and s for s in data.get("files", []) + data.get("directories", [])):
        raise ScopeError("Scope paths must be nonempty strings")
    return {"files": data.get("files", []), "directories": data.get("directories", [])}


def snapshot(root: Path, scope: dict) -> dict[str, dict[str, str]]:
    root = root.resolve(strict=True)
    candidates: set[Path] = set()
    for name in scope["files"]:
        p = _safe(root, name)
        if p.exists():
            candidates.add(p)
    for name in scope["directories"]:
        directory = _safe(root, name)
        if not directory.is_dir():
            continue
        for p in directory.rglob("*.json"):
            _safe(root, p.relative_to(root).as_posix())
            candidates.add(p)
    output = {}
    for p in sorted(candidates):
        if not p.is_file() or p.suffix.lower() != ".json":
            raise ScopeError(f"Only regular JSON files supported: {p}")
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        output[p.relative_to(root).as_posix()] = flatten(data)
    return output


def compare(before: dict, after: dict) -> list[dict]:
    changes = []
    for name in sorted(before.keys() | after.keys()):
        if name not in before:
            changes.append({"file": name, "path": "/", "change": "ADDED_FILE"})
        elif name not in after:
            changes.append({"file": name, "path": "/", "change": "REMOVED_FILE"})
        else:
            left, right = before[name], after[name]
            for pointer in sorted(left.keys() | right.keys()):
                if left.get(pointer) == right.get(pointer):
                    continue
                kind = "ADDED" if pointer not in left else "REMOVED" if pointer not in right else "MODIFIED"
                changes.append({"file": name, "path": pointer, "change": kind})
    return changes


def run(mode: str, root: Path, scope: dict, baseline_path: Path, report_path: Path | None = None, replace: bool = False) -> dict:
    current = snapshot(root, scope)
    now = datetime.now(timezone.utc).isoformat()
    if mode == "baseline":
        if baseline_path.exists() and not replace:
            raise ScopeError("Baseline exists; use --replace-baseline to deliberately reset it")
        baseline = {"schema_version": 3, "created_at_utc": now, "scope": scope, "snapshot": current}
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
        return {"status": "BASELINED", "files": len(current)}
    if mode != "check":
        raise ScopeError("Mode must be baseline or check")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if baseline.get("schema_version") != 3 or baseline.get("scope") != scope or not isinstance(baseline.get("snapshot"), dict):
        raise ScopeError("Invalid baseline or scope changed")
    changes = compare(baseline["snapshot"], current)
    report = {"schema_version": 3, "checked_at_utc": now, "status": "CHANGED" if changes else "PASS", "files": len(current), "changes": changes,
              "note": "Only file paths, JSON pointers, and change types are emitted; values are not exported."}
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("baseline", "check"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--scope", type=Path, default=Path("scope.example.json"))
    parser.add_argument("--baseline", type=Path, default=Path("reports/multi-baseline.json"))
    parser.add_argument("--report", type=Path, default=Path("reports/multi-check.json"))
    parser.add_argument("--replace-baseline", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        resolve = lambda p: p if p.is_absolute() else root / p
        result = run(args.mode, root, load_scope(resolve(args.scope)), resolve(args.baseline), resolve(args.report), args.replace_baseline)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Integrity validation error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "CHANGED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
