@echo off
setlocal

IF EXIST "%~dp0src\azure\cli\__main__.py" (
  SET "PYTHONPATH=%~dp0src;%PYTHONPATH%"
) ELSE (
  SET "PYTHONPATH=%~dp0;%PYTHONPATH%"
)
SET "AZ_INSTALLER=PIP"

IF EXIST "%~dp0\python.exe" (
  "%~dp0\python.exe" -c "import os,runpy,sys; cwd=os.path.normcase(os.path.realpath(os.getcwd())); sys.path[:]=[path for path in sys.path if os.path.normcase(os.path.realpath(path or os.curdir)) != cwd]; runpy.run_module('azure.cli.__main__', run_name='__main__', alter_sys=True)" %*
) ELSE (
  python -c "import os,runpy,sys; cwd=os.path.normcase(os.path.realpath(os.getcwd())); sys.path[:]=[path for path in sys.path if os.path.normcase(os.path.realpath(path or os.curdir)) != cwd]; runpy.run_module('azure.cli.__main__', run_name='__main__', alter_sys=True)" %*
)
