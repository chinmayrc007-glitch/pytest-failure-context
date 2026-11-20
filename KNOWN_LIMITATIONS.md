# Known limitations and risk register

| Area | Current boundary | Risk / next validation |
|---|---|---|
| Language support | Python/pytest only | Non-Python parsers and triggers are not implemented or validated. |
| Imports | Explicit project-local imports, re-exports, relative imports, and module aliases | Star imports, dynamic imports, runtime monkey-patching, and unusual source layouts may be unresolved. |
| Instance methods | Simple local assignment from explicitly imported class; static local inheritance | Fixtures, factories, reassignments, proxies, descriptors, metaclasses, and complex control flow are not inferred. |
| Dynamic dispatch | Static definition selection | Runtime override may differ from statically selected base method. |
| Resolution accuracy | 465 candidate references measured; 60-row stratified sample prepared | No final human-labelled ground-truth precision/recall estimate yet. |
| Context size | Approximate token, definition-count, and soft time caps | Later frames or definitions can be omitted; report must be reviewed for omission notes. Source indexing and initial bundle freshness checks are not interruptible mid-operation. |
| Bundle freshness | Saved chunks are compared with current source | Historical snapshots may show many stale chunks; this is disclosed, not silently merged. |
| Bundle graph | Provenance/freshness only for Python context | Graph edges and broad selections are not treated as verified dependencies. |
| Performance | Flask smoke timing reported | Performance on larger repos and repeated CI runs still needs measurement. |
| Backtesting | One historical Flask regression issue #5917 | Additional historical issues and a second independent repository remain necessary. |
| Secret handling | Reports contain selected source snippets and exception messages | No automatic secret redaction; review the Markdown report before sharing it outside the development team. |
| Output lifecycle | Previous configured report is removed at start of an opted-in run; report is atomically replaced on failure | A user who points `--failure-context-out` at an important existing file can cause it to be removed; use a dedicated report path. |

## Safe interpretation

The current evidence justifies describing this as a working prototype with targeted demonstrated behavior. It does not justify a guarantee that every relevant dependency is found or that every included definition is the runtime implementation. The time cap is a soft deadline, not a hard wall-clock guarantee.
