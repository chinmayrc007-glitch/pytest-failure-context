# V4.2 change log and evidence boundaries

## V4 — original design

1. Use current Python source AST as the authority for Python imports and definitions.
2. Match referenced names inside the failing function body, not import lines or surrounding module-level text.
3. Resolve explicit project-local `from ... import symbol`, module aliases, unique same-file helpers, and lexical same-class `self`/`cls` calls.
4. Extract individual function definitions and compact class outlines.
5. Treat bundle metadata as provenance/stale-section information; do not treat connection confidence or radius selections as proof of dependency.
6. Bound dependency expansion and output by configured budgets.

## V4.1 — imported instance-method resolution

The historical Flask issue #5917 backtest exposed a gap: a failing test instantiated `Flask` and called `app.add_url_rule`, but V4 emitted the imported `Flask` class outline without the inherited method implementation. V4.1 supports a narrow static pattern: a local variable assigned from an explicitly imported class constructor, followed by a method call on that variable. It follows unique, locally resolvable base classes (for example `Flask` → `App`) and includes the inherited method definition.

This is not general Python type inference. Factories, pytest fixtures, dynamically assigned types, proxies, descriptors, metaclasses, and complex control-flow reassignments remain outside the supported scope.

## V4.2 — reliability and test coverage

- Clear a previous, recognizable failure-context report at the configured output path at the start of an opted-in run, so a later passing run cannot leave old failure evidence looking current; preserve unrelated pre-existing files and warn.
- Write failing-run reports through a temporary sibling file and atomic replacement to reduce partial output if the process is interrupted.
- Add UTC generation time and Python/pytest runtime versions to each report for reproducibility.
- Expand synthetic verification from 23 to 34 checks, adding fixture setup and teardown failures, multiple failures, stale report cleanup on a passing rerun, tight token/definition/time limits, corrupt-bundle fallback, relative package imports, ambiguous duplicate definitions, and exclusion of external/out-of-repository frames.
- Document the time cap as a soft assembly deadline, not a hard process timeout.
- Add security/privacy guidance: reports can include source snippets and exception messages and must be reviewed before sharing externally.

## Evidence update

- V4.2 synthetic verification: 40/40 checks passed in the isolated build environment (Python 3.13.5, pytest 9.0.2). This is separate from the user's Windows environment, where V4.1's 23 checks and targeted integration runs were performed.
- Flask smoke analysis (V4 baseline): 856 function/method scopes analysed; 341 had at least one resolved definition; 465 references were found. The report records 150 imported-symbol, 167 module-attribute, 112 same-class, and 36 same-file references. Median per-scope resolution was 1.764 ms; p95 was 10.778 ms. These are coverage/performance measurements, not precision measurements.
- Real Flask pytest integration: targeted tests demonstrated imported-symbol resolution (`get_debug_flag`), module-attribute resolution (`helpers.get_debug_flag`), same-file helper resolution, same-class method resolution, class outline extraction, production-frame capture for `App.add_url_rule`, `_endpoint_from_view_func` resolution when executed, multiple-failure reporting, and no report for passing tests.
- Historical issue #5917: the regression was reproduced on parent commit `d3b78fd1`; the expected OPTIONS header was missing. On fix commit `12e95c93`, Flask's official `test_provide_automatic_options_attr_enable` test passed (1 passed, pytest 8.4.2). V4.1's pre-fix context pack included `App.add_url_rule` from `src/flask/sansio/app.py`, `Flask.test_client`, `_endpoint_from_view_func`, and the `Flask` class outline.
- The historical V4.1 report hit its configured time cap and stated that remaining frames were omitted. It still included the relevant `App.add_url_rule` implementation. Do not describe this as exhaustive context capture.
- The historical bundle marked 292/482 chunks stale against the older pre-fix checkout. The report disclosed this; it did not use stale saved code as current source.

## What this prototype does not claim

- It does not prove UnvibeCode's graph improves Python dependency discovery over AST.
- It does not claim language-agnostic support or production readiness.
- It does not claim a measured precision/recall score; the 60-row sample is preliminary and stratified.
- It does not claim all frames are always included when time or token limits are reached.
- The newly added V4.2 synthetic checks have not yet been rerun on the user's Windows/Python 3.14 environment; that final local confirmation is still recommended.

## Version lineage caveat

The V3 source ZIP was not uploaded in this working session. V4 was rebuilt from the available V2 source and V3 audit findings. V4.1 and V4.2 are follow-on versions. Keep the V2/V3 folders separately as historical comparison artifacts.
