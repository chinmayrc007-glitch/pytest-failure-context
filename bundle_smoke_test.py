"""Run V4's AST resolver against a real repository and UnvibeCode bundle.

Usage (PowerShell):
  py .\bundle_smoke_test.py "C:\\path\\to\\analysis-run" "C:\\path\\to\\repo"

The report is saved as smoke_out_v4.txt beside this script. No repository files
are modified. Bundle graph links and wide precomputed selections are measured but
not trusted as the Python resolver's source of truth.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

from pytest_failure_context.bundle import load_bundle
from pytest_failure_context.resolver import PythonProject


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_path", help="bundle directory, result folder, or ZIP")
    parser.add_argument("repository_root", help="current source repository root")
    parser.add_argument("--limit-examples", type=int, default=12)
    args = parser.parse_args()

    output: list[str] = []

    def emit(value: str = "") -> None:
        output.append(value)
        print(value)

    root = Path(args.repository_root).resolve()
    bundle = load_bundle(args.bundle_path)
    if not bundle.loaded:
        emit("ERROR: could not load a readable UnvibeCode bundle")
        for warning in bundle.warnings:
            emit(f"  {warning}")
        return 2

    started = time.perf_counter()
    project = PythonProject(root)
    checked, stale, stale_examples = bundle.stale_status(root)
    emit(f"bundle: {bundle.requested_path}")
    emit(f"repository: {root}")
    emit(f"loaded in {time.perf_counter() - started:.3f}s | chunks {bundle.chunk_count} | "
         f"files {bundle.source_files} | connections {bundle.connection_count} | "
         f"selections {bundle.selections_count}")
    emit(f"stale saved chunks: {stale}/{checked}")
    for example in stale_examples:
        emit(f"  stale: {example}")

    connection_file: Counter[str] = Counter()
    connection_type: Counter[str] = Counter()
    connection_confidence: Counter[str] = Counter()
    try:
        bundle_root = Path(args.bundle_path)
        if bundle_root.is_file() and bundle_root.suffix.lower() == ".zip":
            import zipfile
            with zipfile.ZipFile(bundle_root) as zf:
                names = zf.namelist()
                target = next(n for n in names if n.endswith("connections.jsonl"))
                rows = [json.loads(x) for x in zf.read(target).decode("utf-8").splitlines() if x.strip()]
        else:
            if not (bundle_root / "connections.jsonl").is_file():
                nested = bundle_root / "flask-repository-context"
                bundle_root = nested if (nested / "connections.jsonl").is_file() else bundle_root
            rows = [json.loads(x) for x in (bundle_root / "connections.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        for row in rows:
            connection_file[str(row.get("source_file") or "")] += 1
            connection_type[str(row.get("relationship") or "unknown")] += 1
            connection_confidence[str(row.get("confidence") or "unknown")] += 1
    except Exception as exc:
        emit(f"connection summary unavailable: {type(exc).__name__}")

    emit("connection rows by relationship: " + json.dumps(dict(connection_type), sort_keys=True))
    emit("connection rows by confidence: " + json.dumps(dict(connection_confidence), sort_keys=True))

    # Describe the bundle's precomputed selections, but do not include them directly
    # in failure packs because the audit found broad scopes and false inclusions.
    try:
        selection_path = bundle_root / "selections.jsonl"
        selections = [json.loads(x) for x in selection_path.read_text(encoding="utf-8").splitlines() if x.strip()]
        for radius in ("0", "1", "2"):
            values = []
            included = []
            for row in selections:
                scope = (row.get("scopes") or {}).get(radius)
                if scope:
                    values.append(int(scope.get("estimated_tokens") or 0))
                    included.extend(scope.get("included_files") or [])
            median = statistics.median(values) if values else 0
            emit(f"selection radius {radius}: rows {len(values)} | median estimated tokens {median:.0f} | "
                 f"distinct included files {len(set(included))}")
    except Exception as exc:
        emit(f"selection summary unavailable: {type(exc).__name__}")

    # Evaluate every function/method AST scope in the current repository. This is a
    # different population from the bundle's function chunks and includes methods.
    function_scopes = list(project.all_function_scopes())
    counts_by_folder: dict[str, Counter[str]] = defaultdict(Counter)
    reason_counts: Counter[str] = Counter()
    resolved_examples: list[str] = []
    unresolved_examples: list[str] = []
    resolved_total = 0
    definition_total = 0
    resolution_times: list[float] = []
    for scope in function_scopes:
        t0 = time.perf_counter()
        try:
            resolutions = project.resolve_scope(scope)
        except Exception as exc:
            resolutions = []
            unresolved_examples.append(f"{scope.module.relpath}::{scope.name}: resolver error {type(exc).__name__}")
        resolution_times.append(time.perf_counter() - t0)
        folder = Path(scope.module.relpath).parts[0] if Path(scope.module.relpath).parts else "root"
        if resolutions:
            resolved_total += 1
            definition_total += len(resolutions)
            counts_by_folder[folder]["resolved"] += 1
            for item in resolutions:
                reason = item.reason.split(" ", 1)[0]
                reason_counts[reason] += 1
            if len(resolved_examples) < args.limit_examples:
                first = resolutions[0]
                resolved_examples.append(
                    f"{scope.module.relpath}::{scope.name} -> "
                    f"{first.definition.path}::{first.definition.name} ({first.reason})")
        else:
            counts_by_folder[folder]["unresolved"] += 1
            if len(unresolved_examples) < args.limit_examples:
                unresolved_examples.append(f"{scope.module.relpath}::{scope.name}")
        counts_by_folder[folder]["total"] += 1

    emit(f"AST scopes analysed: {len(function_scopes)} (functions and methods in current source)")
    emit(f"scopes with >=1 resolved definition: {resolved_total}/{len(function_scopes)} "
         f"({(resolved_total / len(function_scopes) * 100) if function_scopes else 0:.1f}%)")
    emit(f"resolved definition references: {definition_total}")
    emit("resolution reasons: " + json.dumps(dict(reason_counts), sort_keys=True))
    med = statistics.median(resolution_times) if resolution_times else 0
    p95 = sorted(resolution_times)[int((len(resolution_times) - 1) * 0.95)] if resolution_times else 0
    emit(f"resolution time per scope: median {med * 1000:.3f} ms | p95 {p95 * 1000:.3f} ms")
    emit("by top-level folder:")
    for folder, count in sorted(counts_by_folder.items()):
        emit(f"  {folder}: {count['resolved']}/{count['total']} resolved; "
             f"{count['unresolved']} without referenced definitions")
    emit("successful resolution examples:")
    for example in resolved_examples:
        emit(f"  {example}")
    emit("unresolved examples:")
    for example in unresolved_examples:
        emit(f"  {example}")
    emit("policy: current-source AST is the Python dependency authority; bundle links are audit metadata only")
    emit("policy: selections.jsonl scopes are measured but not copied into context packs")

    report_path = Path(__file__).resolve().with_name("smoke_out_v4.txt")
    report_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    emit(f"saved report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
