# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.mgmt.keyvault.models.key_vault_management_client_enums import \
    (SkuName, KeyPermissions, SecretPermissions, CertificatePermissions)
from azure.cli.core.commands import \
    (register_cli_argument, register_extra_cli_argument, CliArgumentType)
import azure.cli.core.commands.arm # pylint: disable=unused-import
from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list, resource_group_name_type,
    tags_type, ignore_type, enum_choice_list)
from azure.cli.core._profile import Profile
from azure.cli.core._util import get_json_object
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication

from azure.keyvault.generated.models.key_vault_client_enums import \
    (JsonWebKeyOperation)
from azure.keyvault.generated.models import \
    (KeyAttributes, SecretAttributes, CertificateAttributes)
from azure.cli.command_modules.keyvault._validators import \
    (datetime_type, base64_encoded_certificate_type,
     get_attribute_validator,
     vault_base_url_type, validate_key_import_source,
     validate_key_type, validate_key_ops, validate_policy_permissions,
     validate_principal, validate_resource_group_name,
     validate_x509_certificate_chain,
     process_certificate_cancel_namespace,
     process_secret_set_namespace,
     secret_text_encoding_values, secret_binary_encoding_values)

# COMPLETERS

def _get_token(server, resource, scope): # pylint: disable=unused-argument
    return Profile().get_login_credentials(resource)[0]._token_retriever() # pylint: disable=protected-access

def get_keyvault_name_completion_list(resource_name):
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        client = KeyVaultClient(KeyVaultAuthentication(_get_token)) # pylint: disable=redefined-variable-type
        func_name = 'get_{}s'.format(resource_name)
        vault = parsed_args.vault_base_url
        items = []
        for y in list(getattr(client, func_name)(vault)):
            id_val = getattr(y, 'id', None) or getattr(y, 'kid', None)
            items.append(id_val.rsplit('/', 1)[1])
        return items
    return completer

def get_keyvault_version_completion_list(resource_name):

    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        client = KeyVaultClient(KeyVaultAuthentication(_get_token)) # pylint: disable=redefined-variable-type
        func_name = 'get_{}_versions'.format(resource_name)
        vault = parsed_args.vault_base_url
        name = getattr(parsed_args, '{}_name'.format(resource_name))
        items = []
        for y in list(getattr(client, func_name)(vault, name)):
            id_val = getattr(y, 'id', None) or getattr(y, 'kid', None)
            items.append(id_val.rsplit('/', 1)[1])
        return items
    return completer

# CUSTOM CHOICE LISTS

key_permission_values = ', '.join([x.value for x in KeyPermissions])
secret_permission_values = ', '.join([x.value for x in SecretPermissions])
certificate_permission_values = ', '.join([x.value for x in CertificatePermissions])
json_web_key_op_values = ', '.join([x.value for x in JsonWebKeyOperation])
secret_encoding_values = secret_text_encoding_values + secret_binary_encoding_values
certificate_file_encoding_values = ['binary', 'string']

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
    register_cli_argument('keyvault {}'.format(item), '{}_name'.format(item), options_list=('--name', '-n'), help='Name of the {}.'.format(item), id_part='child_name', completer=get_keyvault_name_completion_list(item))
    register_cli_argument('keyvault {}'.format(item), 'vault_base_url', vault_name_type, type=vault_base_url_type, id_part=None)
# TODO: Fix once service side issue is fixed that there is no way to list pending certificates
register_cli_argument('keyvault certificate pending', 'certificate_name', options_list=('--name', '-n'), help='Name of the pending certificate.', id_part='child_name', completer=None)

register_cli_argument('keyvault key', 'key_ops', options_list=('--ops',), nargs='*', help='Space separated list of permitted JSON web key operations. Possible values: {}'.format(json_web_key_op_values), validator=validate_key_ops, type=str.lower)
register_cli_argument('keyvault key', 'key_version', options_list=('--version', '-v'), help='The key version. If omitted, uses the latest version.', default='', required=False, completer=get_keyvault_version_completion_list('key'))

for item in ['create', 'import']:
    register_cli_argument('keyvault key {}'.format(item), 'destination', options_list=('--protection', '-p'), choices=['software', 'hsm'], help='Specifies the type of key protection.', validator=validate_key_type, type=str.lower)
    register_cli_argument('keyvault key {}'.format(item), 'disabled', action='store_true', help='Create key in disabled state.')
    register_cli_argument('keyvault key {}'.format(item), 'key_size', options_list=('--size',), type=int)
    register_cli_argument('keyvault key {}'.format(item), 'expires', default=None, help='Expiration UTC datetime  (Y-m-d\'T\'H:M\'Z\').', type=datetime_type)
    register_cli_argument('keyvault key {}'.format(item), 'not_before', default=None, help='Key not usable before the provided UTC datetime  (Y-m-d\'T\'H:M\'Z\').', type=datetime_type)

register_cli_argument('keyvault key import', 'pem_file', help='PEM file containing the key to be imported.', arg_group='Key Source', validator=validate_key_import_source)
register_cli_argument('keyvault key import', 'pem_password', help='Password of PEM file.', arg_group='Key Source')
register_cli_argument('keyvault key import', 'byok_file', help='BYOK file containing the key to be imported. Must not be password protected.', arg_group='Key Source')

register_cli_argument('keyvault key backup', 'file_path', options_list=('--file', '-f'), help='Local file path in which to store key backup.')

register_cli_argument('keyvault key restore', 'file_path', options_list=('--file', '-f'), help='Local key backup from which to restore key.')

register_attributes_argument('keyvault key set-attributes', 'key', KeyAttributes)

register_cli_argument('keyvault secret', 'secret_version', options_list=('--version', '-v'), help='The secret version. If omitted, uses the latest version.', default='', required=False, completer=get_keyvault_version_completion_list('secret'))

register_cli_argument('keyvault secret set', 'content_type', options_list=('--description',), help='Description of the secret contents (e.g. password, connection string, etc)')
register_attributes_argument('keyvault secret set', 'secret', SecretAttributes, create=True)
register_cli_argument('keyvault secret set', 'value', options_list=('--value',), help="Plain text secret value. Cannot be used with '--file' or '--encoding'", required=False, arg_group='Content Source')
register_extra_cli_argument('keyvault secret set', 'file_path', options_list=('--file', '-f'), help="Source file for secret. Use in conjunction with '--encoding'", arg_group='Content Source')
register_extra_cli_argument('keyvault secret set', 'encoding', options_list=('--encoding', '-e'), help='Source file encoding. The value is saved as a tag (file-encoding=<val>) and used during download to automtically encode the resulting file.', default='utf-8', validator=process_secret_set_namespace, arg_group='Content Source', **enum_choice_list(secret_encoding_values))

register_attributes_argument('keyvault secret set-attributes', 'secret', SecretAttributes)

register_cli_argument('keyvault secret download', 'file_path', options_list=('--file', '-f'), help='File to receive the secret contents.')
register_cli_argument('keyvault secret download', 'encoding', options_list=('--encoding', '-e'), help="Encoding of the destination file. By default, will look for the 'file-encoding' tag on the secret. Otherwise will assume 'utf-8'.", default=None, **enum_choice_list(secret_encoding_values))

register_cli_argument('keyvault certificate', 'certificate_version', options_list=('--version', '-v'), help='The certificate version. If omitted, uses the latest version.', default='', required=False, completer=get_keyvault_version_completion_list('certificate'))
register_attributes_argument('keyvault certificate create', 'certificate', CertificateAttributes, True)
register_attributes_argument('keyvault certificate import', 'certificate', CertificateAttributes, True)
register_attributes_argument('keyvault certificate set-attributes', 'certificate', CertificateAttributes)
for item in ['create', 'set-attributes', 'import']:
    register_cli_argument('keyvault certificate {}'.format(item), 'certificate_policy', options_list=('--policy', '-p'), help='JSON encoded policy defintion. Use @{file} to load from a file.', type=get_json_object)

register_cli_argument('keyvault certificate import', 'base64_encoded_certificate', options_list=('--file', '-f'), help='PKCS12 file or PEM file containing the certificate and private key.', type=base64_encoded_certificate_type)

register_cli_argument('keyvault certificate download', 'file_path', options_list=('--file', '-f'), help='File to receive the binary certificate contents.')
register_cli_argument('keyvault certificate download', 'encoding', options_list=('--encoding', '-e'), help='How to store base64 certificate contents in file.', **enum_choice_list(certificate_file_encoding_values))

register_cli_argument('keyvault certificate pending merge', 'x509_certificates', options_list=('--file', '-f'), help='File containing the certificate or certificate chain to merge.', validator=validate_x509_certificate_chain)
register_attributes_argument('keyvault certificate pending merge', 'certificate', CertificateAttributes, True)

register_cli_argument('keyvault certificate pending cancel', 'cancellation_requested', ignore_type, validator=process_certificate_cancel_namespace)

register_cli_argument('keyvault certificate contact', 'contact_email', options_list=('--email',), help='Contact e-mail address. Must be unique.')
register_cli_argument('keyvault certificate contact', 'contact_name', options_list=('--name',), help='Full contact name.')
register_cli_argument('keyvault certificate contact', 'contact_phone', options_list=('--phone',), help='Contact phone number.')

register_cli_argument('keyvault certificate issuer admin', 'email', options_list=('--email',), help='Admin e-mail address. Must be unique within the vault.')
register_cli_argument('keyvault certificate issuer admin', 'name', options_list=('--name',), help='Full admin name.')
register_cli_argument('keyvault certificate issuer admin', 'phone', options_list=('--phone',), help='Amin phone number.')

register_cli_argument('keyvault certificate issuer', 'issuer_name', help='Certificate issuer name.')
register_cli_argument('keyvault certificate issuer', 'disabled', action='store_true', help='Set issuer to disabled state.')
register_cli_argument('keyvault certificate issuer', 'account_id', arg_group='Issuer Credential')
register_cli_argument('keyvault certificate issuer', 'password', arg_group='Issuer Credential')
register_cli_argument('keyvault certificate issuer', 'organization_id', arg_group='Organization Detail')
register_cli_argument('keyvault certificate issuer', 'admin_first_name', arg_group='Organization Detail')
register_cli_argument('keyvault certificate issuer', 'admin_last_name', arg_group='Organization Detail')
register_cli_argument('keyvault certificate issuer', 'admin_email', arg_group='Organization Detail')
register_cli_argument('keyvault certificate issuer', 'admin_phone', arg_group='Organization Detail')
