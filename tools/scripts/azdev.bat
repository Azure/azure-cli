@echo off

REM --------------------------------------------------------------------------------------------
REM Copyright (c) Microsoft Corporation. All rights reserved.
REM Licensed under the MIT License. See License.txt in the project root for license information.
REM --------------------------------------------------------------------------------------------

pip show azure-cli-dev-tools>NUL || pip install -e %~dp0
python -m automation %*