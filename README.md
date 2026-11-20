# pytest-failure-context

**An opt-in pytest plugin that creates bounded Markdown context packs from failed tests.**

The prototype uses current Python source as the authority for dependency resolution. An optional UnvibeCode repository-context bundle contributes provenance and stale-section warnings; graph edges and broad saved selections are not treated as proof of Python dependencies.

## Why

When a test fails, developers often need to move from a traceback to the relevant code definitions. This plugin experiments with gathering a focused, bounded set of source context locally, without changing pytest’s test result.

## Features

- Opt-in via `--failure-context` (disabled by default).
- Extracts the failing Python scope using traceback file/line information.
- Resolves selected project-local imports, relative imports, re-exports, module attributes, unique local helpers, and a narrow imported-class/inheritance method pattern.
- Includes function definitions and compact class outlines.
- Optional UnvibeCode bundle metadata and freshness checks; current source remains authoritative.
- Approximate token, definition and soft time limits with omission notes.
- Removes a prior recognized report at the start of an opted-in run; failing reports are written using a temporary file and atomic replacement.
- Contains context-generation errors so they do not intentionally change pytest’s exit status.

## Install (development)

From the repository root:

```powershell
py -m pip install -e .
```

Confirm pytest discovers the plugin:

```powershell
py -c "from importlib.metadata import entry_points; print([(e.name, e.value) for e in entry_points(group='pytest11') if e.name == 'failure_context'])"
```

Expected entry point:

```text
('failure_context', 'pytest_failure_context.plugin')
```

## Run verification

```powershell
py .\verify_plugin.py
```

The synthetic harness covers opt-in behavior, exit-code preservation, resolution scenarios, fixture setup/teardown failures, multiple failures, bundle staleness/corruption, report freshness, output bounds, and frame filtering. The recorded V4.2 run is **40/40 checks passed**; this is a synthetic integration-check result, not an accuracy benchmark. See `VALIDATION_RESULTS.md` and `VALIDATION_MATRIX.md`.

## Use in a project

```powershell
py -m pytest --failure-context
```

Optional bundle input:

```powershell
py -m pytest --failure-context --failure-context-bundle "C:\path\to\unvibecode-analysis-run"
```

Default report path:

```text
.failure-context/failure_context.md
```

Options:

```text
--failure-context-budget 4000
--failure-context-time-cap 3.0
--failure-context-max-definitions 30
--failure-context-out .failure-context/failure_context.md
```

The time cap is soft: source indexing and initial bundle parsing/freshness checks are not interruptible mid-operation. Reports can omit later frames/definitions and disclose omissions.

## Historical Flask investigation

The prototype was evaluated against a historical Flask regression associated with issue/PR #5917 using separate worktrees. This is a focused case study, not a broad benchmark. The bundle used was from a different snapshot, and stale sections were explicitly reported. See the supporting validation documents for details and qualifications.

## Limitations and privacy

This is a Python/pytest prototype—not a complete call graph, general type inference engine, or dynamic-dispatch resolver. Ambiguous and dynamic patterns may remain unresolved. No statistically defensible precision/recall score has been established.

Generated reports can contain source excerpts, paths, test names, and exception messages. **Review reports for secrets or sensitive data before sharing.** See `KNOWN_LIMITATIONS.md` and `SECURITY_AND_PRIVACY.md`.

## Version

V4.2 reliability candidate; package version 0.0.6. V4.2 focused on report freshness, atomic output, runtime metadata, and expanded synthetic regression checks.
