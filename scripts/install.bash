#!/bin/bash
# 
# Bash script to install the Azure CLI
#
INSTALL_SCRIPT_URL=http://12.345.678.910/azure-cli-install.py
_TTY=/dev/tty

temp_dir=$(mktemp -d) || exit
echo "Created temp directory at $temp_dir"
install_script=$temp_dir/install.py
echo "Downloading Azure CLI install script from $INSTALL_SCRIPT_URL"
curl -# $INSTALL_SCRIPT_URL > $install_script || exit
chmod 775 $install_script
echo "Running install script from $install_script"

if which python3 > /dev/null 2>&1;
then
    PYTHON=python3
else
    PYTHON=python
fi

if [[ -z "$AZURE_CLI_DISABLE_PROMPTS" && -t 1 ]]; then
    $PYTHON $install_script < $_TTY
else
    export AZURE_CLI_DISABLE_PROMPTS=1
    $PYTHON $install_script
fi
