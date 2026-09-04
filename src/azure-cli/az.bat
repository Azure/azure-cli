@echo off
setlocal

SET PYTHONPATH=%~dp0\src;%PYTHONPATH%
SET AZ_INSTALLER=PIP

IF NOT EXIST "%~dp0\python.exe" GOTO usepath
"%~dp0\python.exe" -m azure.cli %*
GOTO end
:usepath
python -m azure.cli %*
:end
