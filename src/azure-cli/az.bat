@echo off
setlocal DisableDelayedExpansion

SET "PYTHONPATH=%~dp0\src;%PYTHONPATH%"
SET AZ_INSTALLER=PIP

IF NOT EXIST "%~dp0az-cli.exe" (
  >&2 echo Azure CLI launcher error: "%~dp0az-cli.exe" was not found.
  >&2 echo Reinstall Azure CLI using the same installer and environment, then reopen your shell.
  EXIT /B 1
)

"%~dp0az-cli.exe" %*
EXIT /B %ERRORLEVEL%
