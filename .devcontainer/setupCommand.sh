#!/bin/bash
source /workspaces/azure-cli/env/bin/activate

azdev setup --cli /workspaces/azure-cli
az --version
