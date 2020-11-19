::
:: Microsoft Azure CLI - Windows Installer - Author file components script
:: Copyright (C) Microsoft Corporation. All Rights Reserved.
::

@IF EXIST "%~dp0\..\az.exe" (
  SET AZ_INSTALLER=MSI
  "%~dp0\..\az.exe" %*
) ELSE (
  echo Failed to load az executable.
  exit /b 1
)
