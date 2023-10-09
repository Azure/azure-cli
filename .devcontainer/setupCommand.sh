#!/bin/bash
. /home/vscode/env/bin/activate

cd /workspaces
git clone https://github.com/Azure/azure-cli-extensions.git azure-cli-extensions
azdev setup --cli ./azure-cli --repo ./azure-cli-extensions
az --version
