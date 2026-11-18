# Secure Executable Invocation (Preventing Binary Planting)

On Windows, a bare executable name (`cmd.exe`, `az`, `docker`, `git`, `gh`, `kubectl`, ...) is looked up in the
**current working directory first**, both by `CreateProcess` (`shell=False`) and by `cmd.exe` (`shell=True`).
If a user runs a command from an untrusted directory (e.g. a cloned repo) containing a planted binary, Azure CLI
would execute it ([CWE-427](https://cwe.mitre.org/data/definitions/427.html)).

```python
# ❌ Vulnerable
subprocess.check_output(['az', 'version'], shell=True)
run_cmd(['docker', 'ps'])
```

## Fix

Resolve the name to an absolute path with `azure.cli.core.util.get_safe_executable_path` before spawning it.
It works like `shutil.which`, except that it:

- searches `%SystemRoot%\System32` and `%SystemRoot%` first on Windows, then `PATH`;
- skips the current working directory as well as relative `PATH` entries (`""`, `.`);
- returns `None` when nothing trusted is found or the working directory is unknown. It never falls back to the
  bare name.

```python
# ✅ Safe
from azure.cli.core.azclierror import ValidationError
from azure.cli.core.util import get_safe_executable_path, run_cmd

docker = get_safe_executable_path('docker')
if not docker:
    raise ValidationError("Docker is not installed or not on PATH.")
run_cmd([docker, 'ps'])
```

To run `az` itself (a batch script, `az.cmd`, on Windows), resolve both `cmd.exe` and `az`, and fall back to
`[sys.executable, '-m', 'azure.cli']`. See `_get_az_cmd_prefix` in
`src/azure-cli/azure/cli/command_modules/util/custom.py`. Prefer in-process calls over spawning `az`; see
[cli_subprocess_guidelines.md](./cli_subprocess_guidelines.md).

## Checklist for module owners

1. Find bare-name spawns in your module:
   ```bash
   grep -rnE "(subprocess\.(run|call|check_call|check_output|Popen)|run_cmd)\(\s*\[?['\"](cmd\.exe|docker|git|gh|kubectl)" src/azure-cli/azure/cli/command_modules/<module>
   ```
2. Replace each bare name with `get_safe_executable_path('<name>')` and handle `None`.
3. Pass arguments as a list and drop `shell=True`.
4. Add a test that puts a decoy executable in the CWD and checks that it isn't selected (see
   `TestSafeExecutablePath` in `src/azure-cli-core/azure/cli/core/tests/test_util.py`).
