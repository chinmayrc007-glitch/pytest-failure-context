# Security and privacy notes

- The plugin is opt-in. It does not generate reports unless `--failure-context` is supplied.
- Context generation runs locally as part of the pytest process. This prototype does not send source code or test output to a network service.
- The optional UnvibeCode bundle is read-only. The plugin reads metadata/chunks to report provenance and freshness; it does not modify the bundle.
- The configured output path is the only report file the plugin manages. At the beginning of an opted-in run, a prior report recognizable by its failure-context header/marker is removed to prevent stale reports after a passing run. An unrelated pre-existing file is preserved and a terminal warning is shown. Use a dedicated path such as `.failure-context/failure_context.md`.
- On a failing run, the report is written to a temporary sibling file and atomically replaced into the configured destination.
- Reports may contain source-code excerpts, file paths relative to the repository, test names, and exception messages. These can include secrets, tokens, customer data, or other sensitive values. Review the report before attaching it to an issue, sending it to an external service, or including it in a public submission.
- The plugin excludes traceback frames outside the repository and common virtual-environment/site-packages paths. This is a source-selection safeguard, not a full secrets scanner or data-loss-prevention system.
- Context-generation errors are contained so they do not intentionally replace pytest's test exit status. The output path itself should still be selected carefully.
