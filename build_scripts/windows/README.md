Building the Windows MSI and ZIP
===============================

This document provides instructions on creating x64 MSI and ZIP packages.
Windows x86 builds are retired. The x64 MSI still upgrades existing x86
installations (including the same version) and detects newer x86 installations
to prevent downgrades.

Prerequisites
-------------

1. Turn on the '.NET Framework 3.5' Windows Feature (required for WIX Toolset).

2. Install 'WIX Toolset build tools' if not already installed. (e.g. WiX v3.10.3)
    http://wixtoolset.org/releases/

3. Get Git for Windows (it has several tools used for the build).
    - https://git-scm.com/download/win (choose the x64 installer)
    - Choose the 'Use Git and optional Unix tools from the Windows Command Prompt' option.

4. Install 'Microsoft Build Tools 2015'.
    https://www.microsoft.com/download/details.aspx?id=48159

5. Clone the repository.
    - git clone https://github.com/azure/azure-cli

Note: The above can be done on a Windows 10 VM.

Building
--------

1. Set the `CLI_VERSION` environment variable.

2. Run `build_scripts\windows\scripts\build.cmd`. `ARCH` defaults to `x64`;
   any other value, including `x86`, is rejected.

3. The unsigned MSI will be in `build_scripts\windows\out`. To build the ZIP
   instead, set `TARGET=zip` (the default is `msi`). Other targets are rejected.

The MSI installs under `C:\Program Files\Microsoft SDKs\Azure\CLI2`.
`scripts\setup_msi_test.ps1` uses that directory's `python.exe`; invoke
`scripts\test_msi_package.py` with it too. Package tests use that same interpreter
for pytest.
MSI/ZIP installation test scripts accept an unset `PLATFORM` as x64 and reject
any explicitly specified platform other than `x64`.

Python and pip bootstrap
------------------------

The build downloads embedded Python and `get-pip.py`. During bootstrap, it sets
`PIP_PYTHON` to the embedded interpreter so pip uses its interpreter runner rather
than executing the bundled `pip` directory, which triggers pip's Windows
self-modification protection. This setting is scoped to bootstrap only.

Downloads, extraction, bootstrap, and setuptools/wheel installation must succeed
before packaging continues. Before copying Python into either package, the build
checks the exact Python version configured in `scripts\build.cmd`, the
`win-amd64` platform, and 64-bit pointer size, then verifies that pip is importable.
These checks also apply when reusing `build_scripts\windows\artifacts\Python`.
A stale x86 interpreter, different Python version, or incomplete bootstrap causes
a build failure, not a fallback. Move only that cache directory aside and retry
to download a fresh Python environment; the build does not automatically delete it.

Run the focused packaging regression tests without installer tooling:

```powershell
python -B -m unittest discover -s build_scripts\windows\tests -v
```
