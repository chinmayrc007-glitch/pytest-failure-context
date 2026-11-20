# Architecture and design

## Goal

Turn a failed pytest run into a small, source-grounded context pack that helps a developer or coding assistant move from the failing test to the most relevant local production definitions without dumping the repository.

## Runtime flow

1. **Opt-in registration** — pytest loads the `pytest11` entry point, but the collector is registered only when `--failure-context` is supplied.
2. **Failure capture** — the collector observes pytest setup/call/teardown reports, stores node ID, short error message, and traceback frame locations, and filters paths outside the repository or common dependency directories.
3. **Scope mapping** — `PythonProject` indexes Python modules under the repository and uses AST line ranges to find the enclosing function, method, or class for each traceback frame.
4. **Dependency resolution** — the resolver examines references used inside that scope and follows only statically supported relationships: explicit imports/re-exports, module attributes, relative imports, same-file function calls, lexical same-class calls, and the narrow imported-class instance/inheritance pattern.
5. **Context expansion** — directly selected function definitions may contribute one additional level of their own imports/helpers. Expansion is bounded and deduplicated.
6. **Source extraction** — exact current-source function bodies are included; classes are rendered as compact outlines with method signatures.
7. **Optional bundle provenance** — if an UnvibeCode repository-context bundle is supplied, the plugin includes its metadata and compares saved numbered lines with the current source. Stale sections are flagged. Graph links and radius selections are not used as Python dependency truth.
8. **Bounded report** — approximate token, maximum-definition, and soft-time limits constrain output. Omitted context is noted. The report includes UTC generation time and Python/pytest versions.
9. **Safe output lifecycle** — an opted-in run removes the previous report at the configured destination so a later passing run cannot leave old failure evidence looking current. On failure, the new report is written to a temporary sibling and atomically replaced.

## Main components

- `plugin.py`: pytest options, failure collection, traceback frame projection, report assembly, budget handling, and atomic report output.
- `resolver.py`: source indexing, AST parsing, scope discovery, import resolution, helper/method resolution, inheritance traversal, and definition extraction.
- `bundle.py`: read-only UnvibeCode bundle parser and stale-section comparison.
- `verify_plugin.py`: disposable-project integration harness that asserts externally visible behavior.

## Design choices

### Current source is authoritative

Saved analysis artifacts can be stale or graph edges can be uncertain. The plugin reads current Python source for code resolution and uses bundle exports only for provenance/freshness reporting. This avoids presenting a stale chunk or a speculative graph edge as a verified dependency.

### Conservative resolution over speculative reach

Ambiguous duplicate definitions are not guessed. Runtime type inference, arbitrary fixtures/factories, dynamic dispatch, reflection, and general call-graph analysis are explicitly out of scope. The narrow inherited-method resolver was added after the Flask #5917 backtest exposed a concrete gap.

### Bounded output

The context pack is designed for review and downstream AI consumption. It is not a full repository export. Token/definition/soft-time caps and one-hop dependency expansion prevent unbounded expansion, and omission notes make truncation visible.

## Current limitations

See `KNOWN_LIMITATIONS.md` for the full risk register. In particular, the resolver is Python-focused, precision/recall is not yet independently established, the time cap is soft, and the historical Flask bundle was from a different snapshot (292/482 chunks flagged stale in the pre-fix worktree).
