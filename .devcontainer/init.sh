#!/bin/bash
cd /workspaces
pip install --upgrade pip
python3 -m venv azdev
source ./azdev/bin/activate
pip3 install azdev
azdev setup -c /workspaces/azure-cli/