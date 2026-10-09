::
:: Microsoft Azure CLI - Windows Installer - Author file components script
:: Copyright (C) Microsoft Corporation. All Rights Reserved.
::

@echo off
setlocal

IF NOT EXIST "%~dp0\..\python.exe" GOTO pynotfound
SET AZ_INSTALLER=MSI
"%~dp0\..\python.exe" -IBm azure.cli %*
GOTO end
:pynotfound
echo Failed to load python executable.
exit /b 1
:end
