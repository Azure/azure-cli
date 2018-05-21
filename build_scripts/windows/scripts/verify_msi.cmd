echo OFF
SetLocal EnableDelayedExpansion

echo This script will run all tests on installed Azure CLI under "ProgramFiles(x86)" folder.
echo You must create a virtual-env with python 3.6.5 and activate it before invoke this script 

set REPO_DIR=%~dp0..\..\..\

pip install -e %REPO_DIR%\tools
pip install -e %REPO_DIR%\src\azure-cli-testsdk

set PYTHONPATH=%ProgramFiles(x86)%\Microsoft SDKs\Azure\CLI2\Lib\site-packages
for /D %%i in (%REPO_DIR%\src\command_modules\*) do (
    set m=%%~ni
    set module=!m:~10!
    azdev test !module!
	if !errorlevel! neq 0 set ERR_MODULES=!ERR_MODULES!;!module!
)
azdev test core
if %errorlevel% neq 0 set ERR_MODULES=%ERR_MODULES%;core
echo Module with test errors: %ERR_MODULES%
