# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.backup._client_factory import (
    vaults_cf)

cli_command(__name__, 'backup vault show', 'azure.mgmt.recoveryservices.operations.vaults_operations#VaultsOperations.get', vaults_cf)

cli_command(__name__, 'backup container show', 'azure.cli.command_modules.backup.custom#show_container', vaults_cf)
cli_command(__name__, 'backup container list', 'azure.cli.command_modules.backup.custom#list_containers', vaults_cf)

cli_command(__name__, 'backup policy show', 'azure.cli.command_modules.backup.custom#show_policy', vaults_cf)
cli_command(__name__, 'backup policy list', 'azure.cli.command_modules.backup.custom#list_policies', vaults_cf)

cli_command(__name__, 'backup protection enable-for-vm', 'azure.cli.command_modules.backup.custom#enable_protection_for_vm', vaults_cf)
cli_command(__name__, 'backup protection disable', 'azure.cli.command_modules.backup.custom#disable_protection', vaults_cf)

cli_command(__name__, 'backup item show', 'azure.cli.command_modules.backup.custom#show_item', vaults_cf)
cli_command(__name__, 'backup item list', 'azure.cli.command_modules.backup.custom#list_items', vaults_cf)


