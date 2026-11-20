# 4-minute demo runbook

## Before the demo

1. Install in editable mode: `py -m pip install -e .`.
2. Confirm the `failure_context` pytest11 entry point is registered.
3. Run `py verify_plugin.py` and show the 40/40 result from the prepared build environment; if presenting from another machine, rerun it there and report that machine's actual result.
4. Confirm the installed wheel is discovered without an explicit `-p` option (see `evidence/wheel_autoload_demo.md`).
5. Use a disposable clone or temporary test folder; do not create deliberate failures in a production checkout.

## Demo sequence

### 1. Show opt-in and report lifecycle (35 seconds)

Explain that the plugin does nothing unless `--failure-context` is supplied. Show that a passing run removes a stale report from a prior opted-in run and generates no new failure report.

### 2. Show a failing test and generated context (50 seconds)

Run a small failing test that calls an imported project function. Show the Markdown output: failing function, traceback line, source definition, and source location.

### 3. Show resolution patterns (60 seconds)

Briefly show the verified patterns: direct import, module alias, same-file helper, same-class method, and the V4.1 inherited instance method (`Flask` → `App.add_url_rule`).

### 4. Show multiple failures and bounds (45 seconds)

Show a two-failure report, a collection-error report, and the omission note when a very small time/token/definition cap is used.

### 5. Show UnvibeCode provenance and privacy boundary (30 seconds)

Explain that the optional bundle adds provenance and stale-section warnings; current source is authoritative. Reports are local files containing source snippets and exception messages, so inspect them before sharing.

### 6. Close with evidence (20 seconds)

Mention 40/40 synthetic checks in the isolated build environment, Flask smoke metrics, and historical issue #5917. State that precision/recall and second-repository generalization remain open validation tasks.

## Avoid claiming

- 100% precision/recall.
- Language-agnostic or multi-language support.
- Full runtime call-graph or type-inference capability.
- Production readiness from the current prototype evidence.
- A hard wall-clock limit: the time cap is a soft assembly deadline.
