#!/bin/bash
cd /workspaces
pip install --upgrade pip
python3 -m venv azdev
source ./azdev/bin/activate
pip3 install azdev
azdev setup -c /workspaces/azure-cli/
echo "Manual config steps:"
echo "  - config vscode python interpreter to '/workspaces/azdev/bin/python'"
echo "  - run 'source /workspaces/azdev/bin/activate', so you have azdev venv loaded."
echo "==============="
echo "for debug launch:"
echo "  - modify .vscode/launch.json 'args' in 'Azure CLI Debug (Integrated Console)' with your own command in string array (not include az itself) "
echo "  - seems won't close the debug session, you would have to watch a terminal tab 'Python Debug Console' for debug output."