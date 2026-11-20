# Validation results and evidence ledger — V4.2

This file separates observed outputs from interpretation. Do not merge coverage metrics with accuracy metrics.

## A. V4.2 synthetic verification

**Observed in the isolated build environment:** `verify_out_v4_2.txt` reports 40/40 checks passed under Python 3.13.5 and pytest 9.0.2 after editable installation.

Checks cover:

- baseline/loaded-disabled/enabled exit-code preservation;
- opt-in behavior, output creation, and exact failing-scope extraction;
- explicit imported symbols, module attributes, relative imports, same-file helpers, same-class methods, and inherited instance methods;
- class outline extraction and exclusion of unused imports;
- ambiguous duplicate definitions are not guessed;
- fixture setup and teardown failure reports;
- multiple failing tests in one report;
- stale prior report removal after a subsequent passing run;
- token, definition-count, and time-limit omission notes;
- stale/corrupt/missing bundle handling and current-source fallback;
- exclusion of external/out-of-repository frames;
- ASCII-safe terminal summary and pytest11 entry-point registration.

**Environment qualification:** this 40-check run was executed in the build environment (Python 3.13.5, pytest 9.0.2). The user's Windows environment previously passed V4.1's 23-check suite and the targeted Flask integration tests. V4.2's added checks should be rerun on Windows before final submission if time permits.

## B. Flask repository smoke analysis (V4 baseline)

| Metric | Observed result |
|---|---:|
| Bundle load time | 1.513 s |
| Saved chunks | 482 |
| Files in bundle | 102 |
| Connection rows | 403 |
| Precomputed selections | 102 |
| Python function/method scopes analysed | 856 |
| Scopes with >=1 resolved definition | 341 (39.8%) |
| Resolved definition references | 465 |
| Imported-symbol references | 150 |
| Module-attribute references | 167 |
| Same-class references | 112 |
| Same-file helper references | 36 |
| Median per-scope resolution | 1.764 ms |
| p95 per-scope resolution | 10.778 ms |

**Interpretation:** 39.8% is the fraction of analysed scopes with at least one resolved definition. It is not precision, recall, or a measure of how many failures the tool can solve. The 465 items are candidate references, not 465 independently human-verified correct dependencies.

## C. Real Flask pytest integration scenarios

The user ran targeted tests on the local Flask checkout and observed reports containing:

- `get_debug_flag` from an explicit import;
- `helpers.get_debug_flag` from a module alias;
- a same-file `local_helper` definition;
- a same-class `_helper` method;
- a `Flask` class outline with method signatures;
- production traceback/source for `App.add_url_rule` and its `wrapper_func` decorator wrapper;
- `_endpoint_from_view_func` when endpoint inference was actually executed;
- a combined report for two failures in one pytest run;
- `1 passed`, exit code 0, and no new report when the test passed (V4.1 behavior; V4.2 also removes an older report at the same configured path).

## D. Historical Flask issue #5917

- **Pre-fix commit:** `d3b78fd18a8d9e224cb9ef58a23cec9b1ffc9ce9` (parent of the fix).
- **Fix commit:** `12e95c93` (`fix provide_automatic_options override (#5917)`).
- **Before fix:** the reconstructed regression test failed because the OPTIONS response's Allow header contained only `GET` and `HEAD`, not `OPTIONS`.
- **After fix:** Flask's official test `tests/test_basic.py::test_provide_automatic_options_attr_enable` passed: `1 passed in 0.24s` on pytest 8.4.2.
- **V4.1 context retrieval:** the pre-fix historical report included the failing test, `Flask` class outline, `Flask.test_client`, `App.add_url_rule` from `src/flask/sansio/app.py`, `_endpoint_from_view_func` from `src/flask/sansio/scaffold.py`, and `FlaskClient`. This demonstrates retrieval of the method modified by the historical fix.
- **Qualification:** the historical context run printed `time cap reached; remaining failures omitted`. The bundle was from a different snapshot and 292/482 saved chunks were flagged stale. This demonstrates staleness reporting but means this run should not be described as exhaustive context capture.

## E. Precision audit status

A 60-row stratified sample (up to 15 rows per resolution method) was generated. An AI-assisted preliminary screen was created, but this is not an independent human-labelled ground-truth audit. No precision/recall percentage is reported.

## F. Reproduction commands

```powershell
# Install the plugin
py -m pip install -e .

# Run the synthetic regression harness
py .\verify_plugin.py

# Run a failing test with context generation
py -m pytest --failure-context --failure-context-bundle "C:\path\to\analysis-run"

# Run Flask smoke analysis
py .\bundle_smoke_test.py "C:\path\to\analysis-run" "C:\path\to\flask"
```

## G. Built wheel and pytest entry-point auto-discovery

The 0.0.6 wheel was built with `pip wheel --no-deps --no-build-isolation`. It was installed from the local wheel in the build environment, and pytest discovered the plugin through the registered `pytest11` entry point without an explicit `-p` flag. A temporary repository's intentionally failing test produced a context report containing the failing test and same-file helper; pytest retained exit code 1. See `evidence/wheel_autoload_demo.md`.
