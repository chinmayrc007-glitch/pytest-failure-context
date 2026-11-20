"""Local verification for the V4.1 pytest failure-context prototype with imported-instance method and inheritance resolution.

Run after `py -m pip install -e .`:
    py verify_plugin.py

The tests use a temporary src-layout repository. They verify current-source AST
resolution, imported definitions, module attributes, local helpers, class outlines,
exit-code preservation, opt-in behaviour, stale-bundle warnings and entry-point
registration. This is still a synthetic test suite, not a substitute for the Flask
smoke test or a historical backtest.
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from importlib.metadata import entry_points
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = "pytest_failure_context.plugin"
RUNS = 5


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_project(root: Path, failing: bool) -> None:
    write(root / "pytest.ini", "[pytest]\ntestpaths = tests\n")
    write(root / "src/app/__init__.py", "")
    write(root / "src/app/tax.py", "def tax_rate():\n    return 0.20\n")
    write(root / "src/app/helpers.py", "def surcharge(value):\n    return value * 0.1\n")
    write(root / "src/app/decoy.py", "def Ghost():\n    return 'not used'\n")
    write(root / "src/app/pricing.py", '''from app.tax import tax_rate
import app.helpers as helpers


def _normalise(items):
    return [item for item in items if item > 0]


def total(items):
    clean = _normalise(items)
    subtotal = sum(clean)
    return subtotal * (1 + tax_rate()) + helpers.surcharge(subtotal)
''')
    write(root / "src/app/service.py", '''class BaseCalculator:
    def inherited(self):
        return "from base"


class Calculator(BaseCalculator):
    """Small calculator used to test outline extraction."""

    def calculate(self, value):
        return value * 2

    def reset(self):
        return 0
''')
    expected = "999" if failing else "13.0"
    inherited_expected = "wrong" if failing else "from base"
    write(root / "tests/test_pricing.py", f'''from app.pricing import total
from app.decoy import Ghost
from app.service import Calculator


def test_total():
    assert total([10]) == {expected}


def test_calculator():
    assert Calculator().calculate(3) == {"7" if failing else "6"}


def test_inherited_method():
    calculator = Calculator()
    assert calculator.inherited() == "{inherited_expected}"
''')


def make_bundle(root: Path, bundle: Path) -> None:
    chunks = []
    chunk_id = 0
    for file in sorted(root.rglob("*.py")):
        if "__pycache__" in file.parts:
            continue
        rel = file.relative_to(root).as_posix()
        source_lines = file.read_text(encoding="utf-8").split("\n")
        numbered = "\n".join(f"{i:>6} | {line}" for i, line in enumerate(source_lines, 1))
        chunks.append({
            "chunk_id": f"chunk_{chunk_id}", "file": rel, "language": "python",
            "line_range": {"start_line": 1, "end_line": len(source_lines)},
            "kind": "whole_file", "estimated_tokens": max(1, len(numbered) // 4),
            "numbered_code": numbered,
        })
        chunk_id += 1
    bundle.mkdir(parents=True, exist_ok=True)
    write(bundle / "manifest.json", json.dumps({
        "schema_version": "shipreadyv2.repository_context_bundle.v1",
        "repository": root.name, "source_files": len(chunks),
        "atomic_code_sections": len(chunks), "verified_cross_file_connections": 0,
        "skipped_files": [], "contents": {"chunks.jsonl": "test fixture"},
    }, indent=2))
    write(bundle / "chunks.jsonl", "\n".join(json.dumps(x) for x in chunks) + "\n")
    write(bundle / "connections.jsonl", "")
    write(bundle / "selections.jsonl", "")
    write(bundle / "unresolved_relationships.jsonl", "")


def run(root: Path, extra: list[str], load_plugin: bool = True) -> tuple[int, float, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + str(HERE / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTHONUTF8"] = "1"
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    if load_plugin:
        cmd += ["-p", PLUGIN]
    cmd += ["tests"] + extra
    started = time.perf_counter()
    result = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True)
    return result.returncode, time.perf_counter() - started, result.stdout + result.stderr


def main() -> int:
    try:
        import pytest  # noqa: F401
    except ImportError:
        print("pytest is not installed. Run: py -m pip install pytest")
        return 2

    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))
        print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))

    with tempfile.TemporaryDirectory(prefix="failure_context_v4_") as temp:
        base = Path(temp)
        failing = base / "failing"
        failing.mkdir()
        make_project(failing, True)
        bundle = base / "bundle"
        make_bundle(failing, bundle)
        pack = failing / ".failure-context/failure_context.md"

        base_rc, _, _ = run(failing, [], load_plugin=False)
        off_rc, _, _ = run(failing, [], load_plugin=True)
        check("baseline failing test has non-zero exit", base_rc == 1, str(base_rc))
        check("loaded but disabled plugin preserves pytest result", off_rc == base_rc,
              f"{base_rc} vs {off_rc}")
        check("no output file when plugin is not opted in", not pack.exists())

        on_rc, _, on_output = run(failing, ["--failure-context",
                                            "--failure-context-bundle", str(bundle)])
        text = pack.read_text(encoding="utf-8") if pack.is_file() else ""
        check("enabled plugin preserves pytest exit code", on_rc == base_rc,
              f"{base_rc} vs {on_rc}")
        check("pack written when enabled", bool(text))
        check("pack names failing test", "tests/test_pricing.py" in text)
        check("pack includes exact failing test function", "def test_total" in text)
        check("report records UTC generation and runtime metadata",
              "Generated (UTC):" in text and "Runtime: Python" in text and "pytest `" in text)
        check("atomic report write leaves no temporary file",
              not list(pack.parent.glob(f".{pack.name}.*.tmp")))
        check("pack resolves imported production function", "def total(items)" in text)
        check("pack resolves named import used by function", "def tax_rate" in text)
        check("pack resolves module attribute used by function", "def surcharge" in text)
        check("pack resolves same-file helper", "def _normalise" in text)
        check("unused imported decoy is excluded", "def Ghost" not in text)
        check("class is rendered as an outline", "class Calculator" in text and "def reset" in text)
        check("inherited instance method resolves through imported class base",
              "BaseCalculator.inherited" in text and "def inherited(self)" in text)
        check("bundle metadata and freshness are included",
              "shipreadyv2.repository_context_bundle.v1" in text and "0/" in text)
        check("terminal summary line printed", "failure-context:" in on_output)
        summary = next((x for x in on_output.splitlines() if x.startswith("failure-context:")), "")
        check("terminal summary is ASCII only", all(ord(c) < 128 for c in summary))

        # A source edit after bundle generation must be flagged as stale, but the
        # emitted definition must still come from current source.
        pricing = failing / "src/app/pricing.py"
        pricing_text = pricing.read_text(encoding="utf-8").replace("return subtotal *", "# changed after saved review\n    return subtotal *")
        pricing.write_text(pricing_text, encoding="utf-8")
        stale_rc, _, _ = run(failing, ["--failure-context", "--failure-context-bundle", str(bundle)])
        stale_pack = pack.read_text(encoding="utf-8") if pack.is_file() else ""
        check("stale saved section is flagged", "Stale section:" in stale_pack)
        check("stale bundle does not change pytest exit code", stale_rc == base_rc)
        check("current source is used after stale review", "changed after saved review" in stale_pack)

        corrupt_rc, _, corrupt_out = run(failing, ["--failure-context",
                                                  "--failure-context-bundle", str(base / "missing-bundle")])
        check("missing bundle falls back to current-source AST", corrupt_rc == base_rc and "AST-only" in corrupt_out)

        passing = base / "passing"
        passing.mkdir()
        make_project(passing, False)
        pass_rc, _, _ = run(passing, ["--failure-context"])
        check("all passing tests keep exit code zero and write no file",
              pass_rc == 0 and not (passing / ".failure-context").exists(), str(pass_rc))

        # A prior failure report must not survive an opted-in passing run.
        stale_report = passing / ".failure-context/failure_context.md"
        write(stale_report, "# Failure context\n<!-- generated by pytest-failure-context -->\nOLD REPORT FROM A PREVIOUS FAILURE\n")
        cleanup_rc, _, _ = run(passing, ["--failure-context"])
        check("passing rerun removes stale prior report", cleanup_rc == 0 and not stale_report.exists(),
              str(cleanup_rc))

        disabled_stale = passing / ".failure-context/failure_context.md"
        write(disabled_stale, "# Failure context\n<!-- generated by pytest-failure-context -->\nDISABLED RUN SHOULD NOT DELETE\n")
        disabled_cleanup_rc, _, _ = run(passing, [], load_plugin=False)
        check("disabled plugin leaves prior report untouched",
              disabled_cleanup_rc == 0 and disabled_stale.is_file(), str(disabled_cleanup_rc))

        protected_file = passing / "important_notes.md"
        write(protected_file, "# Do not delete this user document\n")
        protect_rc, _, protect_output = run(
            passing, ["--failure-context", "--failure-context-out", "important_notes.md"])
        check("unrecognized pre-existing output file is preserved",
              protect_rc == 0 and protected_file.read_text(encoding="utf-8") == "# Do not delete this user document\n",
              str(protect_rc))
        check("preserved user file is reported to the terminal",
              "not a recognized failure-context report" in protect_output)

        # Fixture setup and teardown failures are first-class pytest failures.
        setup_root = base / "setup_failure"
        write(setup_root / "pytest.ini", "[pytest]\ntestpaths = tests\n")
        write(setup_root / "tests/test_setup.py", '''import pytest

@pytest.fixture
def broken_fixture():
    raise RuntimeError("setup exploded")

def test_setup_failure(broken_fixture):
    assert broken_fixture
''')
        setup_rc, _, _ = run(setup_root, ["--failure-context"])
        setup_pack = setup_root / ".failure-context/failure_context.md"
        setup_text = setup_pack.read_text(encoding="utf-8") if setup_pack.is_file() else ""
        check("fixture setup error creates a context report",
              setup_rc == 1 and "test_setup_failure" in setup_text and "broken_fixture" in setup_text,
              str(setup_rc))

        teardown_root = base / "teardown_failure"
        write(teardown_root / "pytest.ini", "[pytest]\ntestpaths = tests\n")
        write(teardown_root / "tests/test_teardown.py", '''import pytest

@pytest.fixture
def broken_teardown():
    yield 1
    raise RuntimeError("teardown exploded")

def test_teardown_failure(broken_teardown):
    assert broken_teardown == 1
''')
        teardown_rc, _, _ = run(teardown_root, ["--failure-context"])
        teardown_pack = teardown_root / ".failure-context/failure_context.md"
        teardown_text = teardown_pack.read_text(encoding="utf-8") if teardown_pack.is_file() else ""
        check("fixture teardown error creates a context report",
              teardown_rc == 1 and "test_teardown_failure" in teardown_text,
              str(teardown_rc))

        multi_root = base / "multiple_failures"
        write(multi_root / "pytest.ini", "[pytest]\ntestpaths = tests\n")
        write(multi_root / "tests/test_multiple.py", '''def test_first_failure():
    assert 1 == 2

def test_second_failure():
    raise RuntimeError("second failure")
''')
        multi_rc, _, _ = run(multi_root, ["--failure-context"])
        multi_pack = multi_root / ".failure-context/failure_context.md"
        multi_text = multi_pack.read_text(encoding="utf-8") if multi_pack.is_file() else ""
        check("multiple failed tests appear in one report",
              multi_rc == 1 and "test_first_failure" in multi_text and "test_second_failure" in multi_text,
              str(multi_rc))

        budget_rc, _, _ = run(failing, ["--failure-context", "--failure-context-budget", "1"])
        budget_text = pack.read_text(encoding="utf-8") if pack.is_file() else ""
        check("tight token budget is disclosed without changing pytest result",
              budget_rc == base_rc and ("budget reached" in budget_text or "omitted" in budget_text),
              str(budget_rc))

        defs_rc, _, _ = run(failing, ["--failure-context", "--failure-context-max-definitions", "0"])
        defs_text = pack.read_text(encoding="utf-8") if pack.is_file() else ""
        check("zero definition cap is disclosed without changing pytest result",
              defs_rc == base_rc and "definition cap reached (0)" in defs_text, str(defs_rc))

        time_rc, _, _ = run(failing, ["--failure-context", "--failure-context-time-cap", "0"])
        time_text = pack.read_text(encoding="utf-8") if pack.is_file() else ""
        check("zero time cap is disclosed without changing pytest result",
              time_rc == base_rc and "time cap reached" in time_text, str(time_rc))

        corrupt_bundle = base / "corrupt_bundle"
        write(corrupt_bundle / "manifest.json", "{ definitely not json")
        write(corrupt_bundle / "chunks.jsonl", "not-json\n")
        corrupt_bundle_rc, _, _ = run(
            failing, ["--failure-context", "--failure-context-bundle", str(corrupt_bundle)])
        corrupt_bundle_text = pack.read_text(encoding="utf-8") if pack.is_file() else ""
        check("corrupt bundle falls back to AST-only and preserves pytest result",
              corrupt_bundle_rc == base_rc and "UnvibeCode bundle: unavailable" in corrupt_bundle_text
              and "def total(items)" in corrupt_bundle_text,
              str(corrupt_bundle_rc))

        relative_root = base / "relative_import"
        write(relative_root / "pytest.ini", "[pytest]\ntestpaths = tests\n")
        write(relative_root / "src/pkg/__init__.py", "")
        write(relative_root / "src/pkg/helpers.py", "def normalise(value):\n    return value + 1\n")
        write(relative_root / "src/pkg/service.py", "from .helpers import normalise\n\ndef calculate(value):\n    return normalise(value)\n")
        write(relative_root / "tests/test_relative.py", "from pkg.service import calculate\n\ndef test_relative_import():\n    assert calculate(1) == 99\n")
        relative_rc, _, _ = run(relative_root, ["--failure-context"])
        relative_pack = relative_root / ".failure-context/failure_context.md"
        relative_text = relative_pack.read_text(encoding="utf-8") if relative_pack.is_file() else ""
        check("relative package import resolves current-source definition",
              relative_rc == 1 and "def normalise(value)" in relative_text, str(relative_rc))

        ambiguous_root = base / "ambiguous_import"
        write(ambiguous_root / "pytest.ini", "[pytest]\ntestpaths = tests\n")
        write(ambiguous_root / "src/app/__init__.py", "")
        write(ambiguous_root / "src/app/helpers.py", "def run(value):\n    return value\n\ndef run(value):\n    return value + 1\n")
        write(ambiguous_root / "tests/test_ambiguous.py", "from app.helpers import run\n\ndef test_ambiguous():\n    assert run(1) == 99\n")
        ambiguous_rc, _, _ = run(ambiguous_root, ["--failure-context"])
        ambiguous_pack = ambiguous_root / ".failure-context/failure_context.md"
        ambiguous_text = ambiguous_pack.read_text(encoding="utf-8") if ambiguous_pack.is_file() else ""
        check("ambiguous duplicate definition is not guessed",
              ambiguous_rc == 1 and "def run(value)" not in ambiguous_text, str(ambiguous_rc))

        collection_root = base / "collection_failure"
        write(collection_root / "pytest.ini", "[pytest]\ntestpaths = tests\n")
        write(collection_root / "tests/test_collection_error.py", "def test_syntax_error(:\n    pass\n")
        collection_rc, _, _ = run(collection_root, ["--failure-context"])
        collection_pack = collection_root / ".failure-context/failure_context.md"
        collection_text = collection_pack.read_text(encoding="utf-8") if collection_pack.is_file() else ""
        check("collection syntax error creates a context report",
              collection_rc != 0 and "test_collection_error.py" in collection_text and "collect" in collection_text,
              str(collection_rc))

        # Frames from dependencies and outside the repository must be excluded.
        from pytest_failure_context.plugin import _project_frames
        projected = _project_frames([
            (str(failing / "tests/test_pricing.py"), 1),
            (str(base / "site-packages/dependency.py"), 10),
            (str(base.parent / "outside.py"), 20),
        ], failing, failing)
        check("external and out-of-repository frames are excluded",
              projected == [("tests/test_pricing.py", 1)], repr(projected))

    try:
        registered = any(ep.name == "failure_context" and ep.value == PLUGIN
                         for ep in entry_points(group="pytest11"))
    except Exception:
        registered = False
    check("pytest11 entry point registered (requires editable install)", registered,
          "run `py -m pip install -e .` if false")

    failures = [name for name, ok, _ in results if not ok]
    print(f"\nChecks: {len(results) - len(failures)}/{len(results)} passed")
    print("ALL CHECKS PASSED" if not failures else "FAILED: " + ", ".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
