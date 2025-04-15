#!/usr/bin/env bash

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

#
# Bash script to install the Azure CLI
#
INSTALL_SCRIPT_URL="https://azurecliprod.blob.core.windows.net/install.py"
INSTALL_SCRIPT_SHA256=7869d3c46992852525b8f9e4c63e34edd2d29cafed9e16fd94d5356665eefdfd
_TTY=/dev/tty

install_script=$(mktemp -t azure_cli_install_tmp_XXXXXX) || exit
echo "Downloading Azure CLI install script from $INSTALL_SCRIPT_URL to $install_script."
curl -# $INSTALL_SCRIPT_URL > $install_script || exit

if command -v sha256sum >/dev/null 2>&1
then
  echo "$INSTALL_SCRIPT_SHA256  $install_script" | sha256sum -c - || exit
elif command -v shasum >/dev/null 2>&1
then
  echo "$INSTALL_SCRIPT_SHA256  $install_script" | shasum -a 256 -c - || exit
fi

python_cmd=python3
if ! command -v python3 >/dev/null 2>&1
then
  if command -v python >/dev/null 2>&1
  then
    python_cmd=python
  else
    echo "ERROR: python3 or python not found."
    echo "If python is available on the system, add it to PATH."
    exit 1
  fi
fi

chmod 775 $install_script
echo "Running install script."
$python_cmd $install_script < $_TTY
