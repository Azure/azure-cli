# Secure Executable Invocation (Preventing Binary Planting)

This guide explains how Azure CLI protects against **binary planting** (a.k.a. executable
hijacking, [CWE-427: Uncontrolled Search Path Element](https://cwe.mitre.org/data/definitions/427.html))
and how command-module owners should remediate bare executable invocations such as `cmd.exe`,
`docker`, `git`, `gh`, and `kubectl`.

> TL;DR: Never spawn a bare executable name. Resolve it to an absolute path from **trusted**
> directories first (excluding the current working directory), then invoke that absolute path.
> Use `azure.cli.core.util.get_safe_executable_path`.

## The problem

When you launch a process by a bare name, the operating system decides *which* file on disk to run
by walking a search path. On Windows this search is especially dangerous:

- `CreateProcess` (and therefore `subprocess` with `shell=False`) resolves the **current working
  directory first**, before the system directory and `PATH`.
- `cmd.exe` (used implicitly by `shell=True`) applies the same current-directory-first rule.

So if a victim `cd`s into an attacker-controlled directory (a cloned repo, an unzipped artifact)
that contains a planted `cmd.exe`, `az.cmd`, `docker.exe`, `git.exe`, `gh.exe`, or `kubectl.exe`,
a command that spawns that bare name will execute the **attacker's** binary inside the victim's
Azure CLI session — leading to arbitrary (and potentially elevated) code execution.

```python
# ❌ Vulnerable: the first token is resolved against the current working directory first on Windows.
subprocess.check_output(['az', 'version', '-o', 'json'], shell=platform.system() == 'Windows')
subprocess.run(['cmd.exe', '/c', 'echo', 'hi'], shell=False)
run_cmd(['docker', 'ps'])
```

`shell=False` does **not** help — the current-directory-first resolution happens in the OS, not the
shell.

## The fix: resolve to an absolute path from trusted directories

Azure CLI Core provides a single, reusable resolution helper:

```python
from azure.cli.core.util import get_safe_executable_path
```

### `get_safe_executable_path(executable) -> str`

Resolves a bare executable **name** to an absolute path, searching only trusted directories:

1. If the input already contains a directory component, it is returned unchanged (nothing to do).
2. On Windows, the Windows system directory (`%SystemRoot%\System32`) and `%SystemRoot%` are
   searched first, so system binaries like `cmd.exe` always resolve there.
3. `PATH` entries are searched next — **but the current working directory (and empty `PATH`
   entries, which Windows treats as the current directory) are excluded.**
4. Windows `PATHEXT` extensions are expanded, so `az` correctly resolves to `az.cmd` / `az.exe`.
5. If resolution fails (the binary is not on `PATH`), the original name is returned as a safe
   fallback — callers keep their previous behavior and existing error handling.

```python
# ✅ Safe: resolve the absolute path first, then invoke it.
from azure.cli.core.util import get_safe_executable_path

docker = get_safe_executable_path('docker')   # e.g. C:\Program Files\Docker\docker.exe
run_cmd([docker, 'ps'])
```

### Invoking `az` itself (or any batch script) on Windows

On Windows, `az` is a batch script (`az.cmd`) that must be run through `cmd.exe`. Resolve **both**
`cmd.exe` and `az` to absolute paths and avoid `shell=True`:

```python
import platform
from azure.cli.core.util import get_safe_executable_path

def _get_az_cmd_prefix():
    if platform.system() == 'Windows':
        return [get_safe_executable_path('cmd.exe'), '/c', get_safe_executable_path('az')]
    return [get_safe_executable_path('az')]

# az version
subprocess.check_output(_get_az_cmd_prefix() + ['version', '-o', 'json'])  # shell=False
```

See `src/azure-cli/azure/cli/command_modules/util/custom.py` for the real implementation used by
`az upgrade`.

> For `az`-related work, prefer an in-process call (SDK, codegen atomic command, or
> `run_az_cmd`) over spawning a subprocess. Spawning a fresh `az` process is only appropriate when
> you specifically need a clean interpreter — for example after an in-place upgrade. See
> [cli_subprocess_guidelines.md](./cli_subprocess_guidelines.md).

## Remediation checklist for command-module owners

Address binary planting in your command module by reviewing every bare executable invocation.
Known affected binaries include `cmd.exe`, `docker`, `git`, `gh`, and `kubectl`.

1. **Find the sinks.** Search your module for subprocess spawns:
   ```bash
   grep -rnE "(subprocess\.(run|call|check_call|check_output|Popen)|run_cmd)\(\s*\[?['\"](cmd\.exe|docker|git|gh|kubectl)" src/azure-cli/azure/cli/command_modules/<your-module>
   ```
2. **Resolve before spawning.** Replace the bare name with
   `get_safe_executable_path('<name>')` and pass the result as the first list element.
3. **Drop `shell=True`.** Pass arguments as a list with `shell=False` (the default). For batch
   scripts on Windows, invoke them through a resolved absolute `cmd.exe /c`.
4. **Keep args as a list.** Never build a command string from user input. Continue to use
   `run_cmd` / `run_az_cmd` where applicable.
5. **Regression-test from a hostile directory.** Add a test that places a decoy executable in the
   current working directory and asserts it is **not** selected (see
   `TestSafeExecutablePath` in `src/azure-cli-core/azure/cli/core/tests/test_util.py`).

### Before / after

```python
# ❌ Before
run_cmd(['docker', 'ps'])
subprocess.call(['kubectl', 'get', 'pods'])
run_cmd(['gh', 'auth', 'status'], capture_output=True)

# ✅ After
from azure.cli.core.util import get_safe_executable_path
run_cmd([get_safe_executable_path('docker'), 'ps'])
subprocess.call([get_safe_executable_path('kubectl'), 'get', 'pods'])
run_cmd([get_safe_executable_path('gh'), 'auth', 'status'], capture_output=True)
```

## Existing precedents in the codebase

Several modules already defend against this class of issue. Prefer the shared Core helper for new
code so the logic stays centralized, but these are useful references:

| Location | Mechanism | Notes |
| --- | --- | --- |
| `azure.cli.core.util.get_safe_executable_path` | Resolve to absolute path, exclude CWD | **Preferred shared helper for new code.** |
| `command_modules/util/custom.py` (`_get_az_cmd_prefix`) | Resolve `cmd.exe` + `az`, drop `shell=True` | Used by `az upgrade`. |
| `command_modules/acr/custom.py` (`_validate_command_path`) | Reject a binary that resolves into the CWD | Honors `DOCKER_COMMAND` override. |
| `command_modules/acs/custom.py` (`which`) | Manual `PATH` lookup (no CWD prepend) | `kubectl` location. |

## Summary

- Binary planting lets an attacker run their executable from a victim's working directory.
- `shell=False` alone does not protect you on Windows.
- Resolve bare executable names to absolute paths from trusted directories **before** spawning,
  using `get_safe_executable_path`.
- Review `cmd.exe`, `docker`, `git`, `gh`, and `kubectl` invocations in your module and add a
  regression test that proves a decoy in the CWD is never selected.

