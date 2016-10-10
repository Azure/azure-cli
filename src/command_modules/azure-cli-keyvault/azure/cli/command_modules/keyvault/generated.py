#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from .custom import (list_keyvault, create_keyvault, set_policy, delete_policy)
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.keyvault.operations import VaultsOperations

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import cli_generic_update_command

from azure.cli.command_modules.keyvault.keyvaultclient.generated import KeyVaultClient as BaseKeyVaultClient
from azure.cli.command_modules.keyvault.keyvaultclient import KeyVaultClient
from azure.cli.command_modules.keyvault._command_type import cli_keyvault_data_plane_command
from azure.cli.command_modules.keyvault.custom import \
    (create_key, create_certificate,
     add_certificate_contact, delete_certificate_contact,
     create_certificate_issuer, update_certificate_issuer,
     add_certificate_issuer_admin, delete_certificate_issuer_admin, list_certificate_issuer_admins)

def _keyvault_client_factory(**_):
    return get_mgmt_service_client(KeyVaultManagementClient)

factory = lambda args: _keyvault_client_factory(**args).vaults
cli_command('keyvault create', create_keyvault, factory)
cli_command('keyvault list', list_keyvault, factory)
cli_command('keyvault show', VaultsOperations.get, factory)
cli_command('keyvault delete', VaultsOperations.delete, factory)

cli_command('keyvault set-policy', set_policy, factory)
cli_command('keyvault delete-policy', delete_policy, factory)

def keyvault_update_setter(client, resource_group_name, vault_name, parameters):
    from azure.mgmt.keyvault.models import VaultCreateOrUpdateParameters
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=parameters.location,
                                       properties=parameters.properties))

cli_generic_update_command('keyvault update', VaultsOperations.get, keyvault_update_setter, lambda: _keyvault_client_factory().vaults)

# Data Plane Commands

cli_keyvault_data_plane_command('keyvault key list', KeyVaultClient.get_keys)
cli_keyvault_data_plane_command('keyvault key list-versions', KeyVaultClient.get_key_versions)
cli_keyvault_data_plane_command('keyvault key create', create_key)
cli_keyvault_data_plane_command('keyvault key set-attributes', BaseKeyVaultClient.update_key)
cli_keyvault_data_plane_command('keyvault key show', BaseKeyVaultClient.get_key)
cli_keyvault_data_plane_command('keyvault key delete', KeyVaultClient.delete_key)
# TODO: Round 3
#cli_keyvault_data_plane_command('keyvault key import', import_key)
#cli_keyvault_data_plane_command('keyvault key backup', KeyVaultClient.backup_key)
#cli_keyvault_data_plane_command('keyvault key restore', KeyVaultClient.restore_key)

cli_keyvault_data_plane_command('keyvault secret list', KeyVaultClient.get_secrets)
cli_keyvault_data_plane_command('keyvault secret list-versions', KeyVaultClient.get_secret_versions)
cli_keyvault_data_plane_command('keyvault secret set', KeyVaultClient.set_secret)
cli_keyvault_data_plane_command('keyvault secret set-attributes', BaseKeyVaultClient.update_secret)
cli_keyvault_data_plane_command('keyvault secret show', BaseKeyVaultClient.get_secret)
cli_keyvault_data_plane_command('keyvault secret delete', KeyVaultClient.delete_secret)
# TODO: Round 3
#cli_keyvault_data_plane_command('keyvault secret download', dummy)

cli_keyvault_data_plane_command('keyvault certificate create', create_certificate)
cli_keyvault_data_plane_command('keyvault certificate list', KeyVaultClient.get_certificates)
cli_keyvault_data_plane_command('keyvault certificate list-versions', KeyVaultClient.get_certificate_versions)
cli_keyvault_data_plane_command('keyvault certificate show', BaseKeyVaultClient.get_certificate)
cli_keyvault_data_plane_command('keyvault certificate delete', KeyVaultClient.delete_certificate)
cli_keyvault_data_plane_command('keyvault certificate set-attributes', BaseKeyVaultClient.update_certificate)

# TODO: Round 3
#cli_keyvault_data_plane_command('keyvault certificate import', KeyVaultClient.import_certificate)
#cli_keyvault_data_plane_command('keyvault certificate merge', KeyVaultClient.merge_certificate)
#cli_keyvault_data_plane_command('keyvault certificate download', dummy)

cli_keyvault_data_plane_command('keyvault certificate contact list', KeyVaultClient.get_certificate_contacts)
cli_keyvault_data_plane_command('keyvault certificate contact add', add_certificate_contact)
cli_keyvault_data_plane_command('keyvault certificate contact delete', delete_certificate_contact)

cli_keyvault_data_plane_command('keyvault certificate issuer update', update_certificate_issuer)
cli_keyvault_data_plane_command('keyvault certificate issuer list', KeyVaultClient.get_certificate_issuers)
cli_keyvault_data_plane_command('keyvault certificate issuer create', create_certificate_issuer)
cli_keyvault_data_plane_command('keyvault certificate issuer show', KeyVaultClient.get_certificate_issuer)
cli_keyvault_data_plane_command('keyvault certificate issuer delete', KeyVaultClient.delete_certificate_issuer)

cli_keyvault_data_plane_command('keyvault certificate issuer admin list', list_certificate_issuer_admins)
cli_keyvault_data_plane_command('keyvault certificate issuer admin add', add_certificate_issuer_admin)
cli_keyvault_data_plane_command('keyvault certificate issuer admin delete', delete_certificate_issuer_admin)

#cli_command('keyvault certificate TEMPLATE', certificate_policy_template)
