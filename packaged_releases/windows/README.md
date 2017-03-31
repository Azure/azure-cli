Building the Windows MSI
========================

This document provides instructions on creating the MSI.

Prerequisites
-------------

1. Install 'WIX Toolset build tools' if not already installed.
    http://wixtoolset.org/releases/

2. Get Git for Windows (it has several tools used for the build).
    https://github.com/git-for-windows/git/releases/download/v2.12.2.windows.1/Git-2.12.2-32-bit.exe

3. Install 'Microsoft Build Tools 2015'.
    https://www.microsoft.com/en-us/download/details.aspx?id=48159

Building
--------

1. Change the 'ProductVersion' in `Product.wxs` when creating a new release.
    In `.\scripts\prepareRepoClone.cmd` also change the CLI_VERSION in there.

2. Run `build.cmd`.

3. The unsigned MSI will be in the `.\out` folder.
