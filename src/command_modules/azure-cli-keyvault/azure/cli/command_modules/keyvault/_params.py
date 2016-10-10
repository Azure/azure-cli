#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import json

from azure.mgmt.keyvault.models.key_vault_management_client_enums import \
    (SkuName, KeyPermissions, SecretPermissions, CertificatePermissions)
from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list, resource_group_name_type,
    tags_type, ignore_type, enum_choice_list)
from azure.cli.core.commands import \
    (register_cli_argument, register_extra_cli_argument, CliArgumentType)
import azure.cli.core.commands.arm # pylint: disable=unused-import

from azure.cli.command_modules.keyvault.keyvaultclient.models.key_vault_client_enums import \
    (JsonWebKeyOperation)
from azure.cli.command_modules.keyvault.keyvaultclient.models import \
    (KeyAttributes, SecretAttributes, CertificateAttributes)
from azure.cli.command_modules.keyvault._validators import \
    (datetime_type,
     get_attribute_validator,
     vault_base_url_type, validate_key_import_source,
     validate_key_type, validate_key_ops, validate_policy_permissions,
     validate_principal, validate_resource_group_name)

# CUSTOM CHOICE LISTS

key_permission_values = ', '.join([x.value for x in KeyPermissions])
secret_permission_values = ', '.join([x.value for x in SecretPermissions])
certificate_permission_values = ', '.join([x.value for x in CertificatePermissions])
json_web_key_op_values = ', '.join([x.value for x in JsonWebKeyOperation])

# KEY ATTRIBUTE PARAMETER REGISTRATION

def register_attributes_argument(scope, name, attr_class, create=False):
    register_cli_argument(scope, '{}_attributes'.format(name), ignore_type, validator=get_attribute_validator(name, attr_class, create))
    if create:
        register_extra_cli_argument(scope, 'disabled', action='store_true', help='Create {} in disabled state.'.format(name))
    else:
        register_extra_cli_argument(scope, 'enabled', default=None, choices=['true', 'false'], help='Enable the {}.'.format(name))
    register_extra_cli_argument(scope, 'expires', default=None, help='Expiration UTC datetime  (Y-m-d\'T\'H:M\'Z\').', type=datetime_type)
    register_extra_cli_argument(scope, 'not_before', default=None, help='Key not usable before the provided UTC datetime  (Y-m-d\'T\'H:M\'Z\').', type=datetime_type)

# ARGUMENT DEFINITIONS

vault_name_type = CliArgumentType(help='Name of the key vault.', options_list=('--vault-name',), completer=get_resource_name_completion_list('Microsoft.KeyVault/vaults'), id_part=None)

# PARAMETER REGISTRATIONS

register_cli_argument('keyvault', 'resource_group_name', resource_group_name_type, id_part=None, required=False, help='Proceed only if Key Vault belongs to the specified resource group.', validator=validate_resource_group_name)
register_cli_argument('keyvault', 'vault_name', vault_name_type, options_list=('--name', '-n'))
register_cli_argument('keyvault', 'object_id', help='a GUID that identifies the principal that will receive permissions')
register_cli_argument('keyvault', 'spn', help='name of a service principal that will receive permissions')
register_cli_argument('keyvault', 'upn', help='name of a user principal that will receive permissions')
register_cli_argument('keyvault', 'tags', tags_type)

register_cli_argument('keyvault create', 'resource_group_name', resource_group_name_type, completer=None, validator=None)
register_cli_argument('keyvault create', 'vault_name', completer=None)
register_cli_argument('keyvault create', 'sku', **enum_choice_list(SkuName))
register_cli_argument('keyvault create', 'no_self_perms', action='store_true', help="If specified, don't add permissions for the current user in the new vault")

register_cli_argument('keyvault list', 'resource_group_name', resource_group_name_type, validator=None)

register_cli_argument('keyvault delete-policy', 'object_id', validator=validate_principal)
register_cli_argument('keyvault set-policy', 'key_permissions', metavar='PERM', nargs='*', help='Space separated list. Possible values: {}'.format(key_permission_values), arg_group='Permission', validator=validate_policy_permissions)
register_cli_argument('keyvault set-policy', 'secret_permissions', metavar='PERM', nargs='*', help='Space separated list. Possible values: {}'.format(secret_permission_values), arg_group='Permission')
register_cli_argument('keyvault set-policy', 'certificate_permissions', metavar='PERM', nargs='*', help='Space separated list. Possible values: {}'.format(certificate_permission_values), arg_group='Permission')

for item in ['key', 'secret', 'certificate']:
    register_cli_argument('keyvault {}'.format(item), '{}_name'.format(item), options_list=('--name', '-n'), help='Name of the {}.'.format(item), id_part='child_name')
    register_cli_argument('keyvault {}'.format(item), 'vault_base_url', vault_name_type, type=vault_base_url_type, id_part=None)

register_cli_argument('keyvault key', 'key_ops', options_list=('--ops',), nargs='*', help='Space separated list of permitted JSON web key operations. Possible values: {}'.format(json_web_key_op_values), validator=validate_key_ops, type=str.lower)
register_cli_argument('keyvault key', 'key_version', options_list=('--version', '-v'), help='The key version. If omitted, uses the latest version.')

for item in ['create', 'import']:
    register_cli_argument('keyvault key {}'.format(item), 'destination', options_list=('--protection', '-p'), choices=['software', 'hsm'], help='Specifies the type of key protection.', validator=validate_key_type, type=str.lower)
    register_cli_argument('keyvault key {}'.format(item), 'disabled', action='store_true', help='Create key in disabled state.')
    register_cli_argument('keyvault key {}'.format(item), 'key_size', options_list=('--size',), type=int)
    register_cli_argument('keyvault key {}'.format(item), 'expires', default=None, help='Expiration UTC datetime  (Y-m-d\'T\'H:M\'Z\').', type=datetime_type)
    register_cli_argument('keyvault key {}'.format(item), 'not_before', default=None, help='Key not usable before the provided UTC datetime  (Y-m-d\'T\'H:M\'Z\').', type=datetime_type)

register_cli_argument('keyvault key import', 'pem_file', help='PEM file containing the key to be imported.', arg_group='Key Source', validator=validate_key_import_source)
register_cli_argument('keyvault key import', 'pem_password', help='Password of PEM file.', arg_group='Key Source')
register_cli_argument('keyvault key import', 'byok_file', help='BYOK file containing the key to be imported. Must not be password protected.', arg_group='Key Source')

register_attributes_argument('keyvault key set-attributes', 'key', KeyAttributes)

register_cli_argument('keyvault secret', 'secret_version', options_list=('--version', '-v'), help='The secret version. If omitted, uses the latest version.')

register_attributes_argument('keyvault secret set', 'secret', SecretAttributes, create=True)
register_attributes_argument('keyvault secret set-attributes', 'secret', SecretAttributes)

register_cli_argument('keyvault certificate', 'certificate_version', options_list=('--version', '-v'), help='The certificate version. If omitted, uses the latest version.')

for item in ['create', 'set-attributes']:
    register_attributes_argument('keyvault certificate {}'.format(item), 'certificate', CertificateAttributes, item == 'create')
    register_cli_argument('keyvault certificate {}'.format(item), 'certificate_policy', options_list=('--policy', '-p'), help='JSON encoded policy defintion. Use @{file} to load from a file.', type=json.loads)
