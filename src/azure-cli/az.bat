@echo off
setlocal

IF EXIST "%~dp0\python.exe" (
  "%~dp0\python.exe" -m azure.cli %*
) ELSE (
  SET PYTHONPATH=%~dp0/src;%PYTHONPATH%
  python -m azure.cli %*
)
