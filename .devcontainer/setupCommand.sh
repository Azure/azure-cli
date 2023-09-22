#!/bin/bash
source /home/vscode/env/bin/activate

azdev setup --cli /workspaces/azure-cli
az --version
