@echo off

REM --------------------------------------------------------------------------------------------
REM Copyright (c) Microsoft Corporation. All rights reserved.
REM Licensed under the MIT License. See License.txt in the project root for license information.
REM --------------------------------------------------------------------------------------------

pip show azure-cli-utility-automation>NUL || pip install -e %~dp0
python -m automation.style.run %*