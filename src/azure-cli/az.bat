@echo off
setlocal

IF DEFINED PYTHONPATH (
  SET "PYTHONPATH=%~dp0\src;%PYTHONPATH%"
) ELSE (
  SET "PYTHONPATH=%~dp0\src"
)
SET AZ_INSTALLER=PIP

IF EXIST "%~dp0\python.exe" (
  "%~dp0\python.exe" -c "import sys; sys.path.pop(0) if sys.path and sys.path[0] == '' else None; import runpy; runpy.run_module('azure.cli', run_name='__main__', alter_sys=True)" %*
) ELSE (
  python -c "import sys; sys.path.pop(0) if sys.path and sys.path[0] == '' else None; import runpy; runpy.run_module('azure.cli', run_name='__main__', alter_sys=True)" %*
)
