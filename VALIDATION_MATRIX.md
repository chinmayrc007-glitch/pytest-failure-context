# V4.2 validation matrix

`verify_plugin.py` runs disposable temporary repositories and checks the following externally visible behaviors. Captured output is in `verify_out_v4_2.txt`.

| # | Check | Expected behavior |
|---:|---|---|
| 1 | Baseline failing project | pytest returns non-zero |
| 2 | Plugin loaded but disabled | Exit code matches baseline |
| 3 | Disabled plugin output | No context file is created |
| 4 | Plugin enabled | Exit code still matches baseline |
| 5 | Failure pack creation | Markdown file is written |
| 6 | Failing node identity | Node ID/path appears in report |
| 7 | Failing scope extraction | Exact failing test function is included |
| 8 | Imported production function | Current-source function definition is included |
| 9 | Named import | Used imported symbol resolves |
| 10 | Module attribute | Module alias attribute resolves |
| 11 | Same-file helper | Unique local helper resolves |
| 12 | Unused import decoy | Unused imported definition is excluded |
| 13 | Class outline | Class is compactly outlined |
| 14 | Inherited instance method | Imported class → local base class method resolves |
| 15 | Bundle metadata | Schema and freshness metadata appear |
| 16 | Terminal summary | Summary line appears |
| 17 | Terminal summary encoding | Summary is ASCII-safe |
| 18 | Stale bundle section | Stale section is flagged |
| 19 | Stale bundle result safety | pytest exit code is preserved |
| 20 | Current-source preference | Changed current source, not stale saved content, is emitted |
| 21 | Missing bundle | AST-only fallback works |
| 22 | Passing tests | Exit code 0 and no new report |
| 23 | pytest entry point | `pytest11` entry point is registered |
| 24 | Prior report cleanup | Passing rerun removes an old recognizable report at configured path |
| 25 | Unrecognized pre-existing output | An unrelated file at a custom output path is preserved |
| 26 | Output-path warning | Terminal warning explains why the unrelated file was preserved |
| 27 | Fixture setup failure | Setup error creates a context report |
| 28 | Fixture teardown failure | Teardown error creates a context report |
| 29 | Multiple failures | Both failing test node IDs appear in one report |
| 30 | Tight token budget | Omission is disclosed and pytest result is preserved |
| 31 | Zero definition cap | Definition-cap omission is disclosed |
| 32 | Zero time cap | Time-cap omission is disclosed |
| 33 | Corrupt bundle | AST-only fallback works and pytest result is preserved |
| 34 | Relative import | Relative package import resolves current-source definition |
| 35 | Ambiguous duplicate symbol | Resolver does not guess between duplicate definitions |
| 36 | Frame path safety | External and out-of-repository frames are excluded |

| 37 | Collection error | Syntax error during collection generates a context report and preserves pytest's non-zero result |
| 38 | Runtime metadata | Generated UTC timestamp and Python/pytest versions are included |
| 39 | Atomic output | Temporary file is cleaned after successful report replacement |
| 40 | Disabled plugin lifecycle | A disabled plugin run does not remove a prior report |

## Scope of this matrix

These 40 synthetic integration checks, not a statistically representative accuracy benchmark. They demonstrate expected behavior for selected scenarios. The 465-reference Flask smoke metric is candidate coverage, not precision/recall. The 60-row sample is preliminary and stratified, not an independently labelled ground-truth evaluation.
