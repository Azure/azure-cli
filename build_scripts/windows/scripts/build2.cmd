@echo off
SetLocal EnableDelayedExpansion

set ARTIFACTS_DIR=%~dp0..\artifacts

set BUILDING_DIR=%ARTIFACTS_DIR%\cli
:: Remove .py and only deploy .pyc files
pushd %BUILDING_DIR%\Lib\site-packages
for /f %%f in ('dir /b /s *.pyc') do (
    set PARENT_DIR=%%~df%%~pf..
	echo !PARENT_DIR! 
    echo !PARENT_DIR! | findstr /C:\Lib\site-packages\pip\
    if !errorlevel! neq  0 (
		echo should trim
    ) ELSE (
        echo --SKIP !PARENT_DIR! under pip
    )
)
popd
