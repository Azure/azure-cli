#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.mgmt.keyvault.models.key_vault_management_client_enums import (SkuName)
from azure.cli.commands.parameters import (
    get_resource_name_completion_list,
    name_type)
from azure.cli.commands import register_cli_argument
import azure.cli.commands.arm # pylint: disable=unused-import

from azure.cli.command_modules.keyvault._validators import (process_policy_namespace, process_set_policy_perms_namespace)

register_cli_argument('keyvault', 'vault_name', arg_type=name_type, help='Name of the key vault', completer=get_resource_name_completion_list('Microsoft.KeyVault/vaults'), id_part='name')
register_cli_argument('keyvault', 'object_id', help='a GUID that identifies the principal that will receive permissions')
register_cli_argument('keyvault', 'spn', help='name of a service principal that will receive permissions')
register_cli_argument('keyvault', 'upn', help='name of a user principal that will receive permissions')

register_cli_argument('keyvault create', 'vault_name', completer=None)
register_cli_argument('keyvault create', 'sku', choices=[e.value for e in SkuName])
register_cli_argument('keyvault create', 'no_self_perms', action='store_true', help="If specified, don't add permissions for the current user in the new vault")

register_cli_argument('keyvault set-policy', 'object_id', validator=process_policy_namespace)
register_cli_argument('keyvault delete-policy', 'object_id', validator=process_policy_namespace)
# TODO Validate perms_to_keys and perms_to_secrets when enums are added in keyvault SDK
register_cli_argument('keyvault set-policy', 'perms_to_keys', nargs='*', validator=process_set_policy_perms_namespace, help='Permissions to keys')
register_cli_argument('keyvault set-policy', 'perms_to_secrets', nargs='*', help='Permissions to secrets')
