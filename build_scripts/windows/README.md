Building the Windows MSI
========================

This document provides instructions on creating the MSI.

Prerequisites
-------------

1. Install the .NET SDK 8 or later.
    https://dotnet.microsoft.com/download
    - The WiX Toolset is restored from NuGet as part of the build, so it doesn't need to be installed separately.

2. Accept the WiX Toolset Open Source Maintenance Fee (OSMF) EULA, which WiX v7 requires. Either:
    - run `dotnet build build_scripts\windows\azure-cli.wixproj -t:AcceptEula -p:EulaId=wix7` once per user and machine, or
    - set the `AcceptEula` environment variable to `wix7` for the build (e.g. in CI).
    See https://wixtoolset.org/osmf/ for the terms.

3. Get Git for Windows (it has several tools used for the build).
    - https://github.com/git-for-windows/git/releases/download/v2.12.2.windows.1/Git-2.12.2-32-bit.exe
    - Choose the 'Use Git and optional Unix tools from the Windows Command Prompt' option.

4. Clone the repository.
    - git clone https://github.com/azure/azure-cli

Note: The above can be done on a Windows 10 VM.

Building
--------

1. Set the `CLI_VERSION` environment variable.

2. Run `build_scripts\windows\scripts\build.cmd`.

3. The unsigned MSI will be in the `.\out` folder.
