# Windows quick start — V4.2

Run these commands from the extracted `pytest-failure-context` folder (the folder containing `verify_plugin.py` and `dist/`).

## 1. Install the included wheel

```powershell
py -m pip install --force-reinstall .\dist\pytest_failure_context-0.0.6-py3-none-any.whl
```

## 2. Verify registration

```powershell
py -c "import importlib.metadata as m; print([(e.name, e.value) for e in m.entry_points(group='pytest11') if e.name == 'failure_context'])"
```

Expected:

```text
[('failure_context', 'pytest_failure_context.plugin')]
```

## 3. Run the complete local verification harness

```powershell
py .\verify_plugin.py
```

Expected final lines:

```text
Checks: 40/40 passed
ALL CHECKS PASSED
```

Record the actual output and environment versions. Do not report the build-environment result as a Windows result until this command passes on Windows.

## 4. Run in a repository

From the repository root:

```powershell
py -m pytest --failure-context --failure-context-out .failure-context/failure_context.md
```

Optionally add the UnvibeCode bundle path:

```powershell
py -m pytest --failure-context --failure-context-bundle "C:\path\to\analysis-run"
```

The plugin is opt-in. Reports contain source excerpts and exception messages; inspect for secrets before sharing. The configured output should be a dedicated Markdown report path.
