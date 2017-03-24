Building the Windows MSI
========================

This document provides instructions on creating the MSI.

Prerequisites
-------------

1. Install 'WIX Toolset build tools' if not already installed.
    http://wixtoolset.org/releases/

2. Install 'curl' as it's used during the build.
    You can get this through Git for Windows.

3. Install 'Microsoft Build Tools 2015'.
    https://www.microsoft.com/en-us/download/details.aspx?id=48159

4. Install a *clean* Python environment on to the machine.
    *note: This is not a Python virtual environment*
    This is the version of Python that will be included in the MSI.
    i.e. https://www.python.org/ftp/python/3.6.1/python-3.6.1.exe
    The script expects this Python install to be in the following directory:
        `%HOMEDRIVE%%HOMEPATH%\zPython`

Building
--------

1. Change the 'ProductVersion' in `Product.wxs` when creating a new release.
    In `.\scripts\prepareRepoClone.cmd` also change the CLI_VERSION in there.

2. Run `build.cmd`.

3. The MSI will be in the `.\out` folder.
