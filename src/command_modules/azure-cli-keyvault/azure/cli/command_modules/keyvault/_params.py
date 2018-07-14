# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

import azure.cli.core.commands.arm  # pylint: disable=unused-import
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list, resource_group_name_type, tags_type, file_type, get_three_state_flag,
    get_enum_type)
from azure.cli.core.util import get_json_object

from azure.cli.command_modules.keyvault._completers import (
    get_keyvault_name_completion_list, get_keyvault_version_completion_list)
from azure.cli.command_modules.keyvault._validators import (
    datetime_type, certificate_type,
    get_vault_base_url_type, validate_key_import_source,
    validate_key_type, validate_policy_permissions,
    validate_principal, validate_resource_group_name,
    validate_x509_certificate_chain,
    secret_text_encoding_values, secret_binary_encoding_values)


# CUSTOM CHOICE LISTS

secret_encoding_values = secret_text_encoding_values + secret_binary_encoding_values
certificate_format_values = ['PEM', 'DER']


# pylint: disable=too-many-locals, too-many-branches, too-many-statements, line-too-long
def load_arguments(self, _):
    from azure.keyvault.models import JsonWebKeyOperation
    from azure.keyvault.models import KeyAttributes, SecretAttributes, CertificateAttributes
    from azure.mgmt.keyvault.models.key_vault_management_client_enums import (
        SkuName, KeyPermissions, SecretPermissions, CertificatePermissions)

    # ARGUMENT DEFINITIONS
    vault_name_type = CLIArgumentType(
        help='Name of the key vault.', options_list=['--vault-name'], metavar='NAME', id_part=None,
        completer=get_resource_name_completion_list('Microsoft.KeyVault/vaults'))

    # region vault (management)
    with self.argument_context('keyvault') as c:
        c.argument('resource_group_name', resource_group_name_type, id_part=None, required=False, help='Proceed only if Key Vault belongs to the specified resource group.', validator=validate_resource_group_name)
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'])
        c.argument('object_id', help='a GUID that identifies the principal that will receive permissions')
        c.argument('spn', help='name of a service principal that will receive permissions')
        c.argument('upn', help='name of a user principal that will receive permissions')
        c.argument('tags', tags_type)
        c.argument('enabled_for_deployment', arg_type=get_three_state_flag(), help='Allow Virtual Machines to retrieve certificates stored as secrets from the vault.')
        c.argument('enabled_for_disk_encryption', arg_type=get_three_state_flag(), help='Allow Disk Encryption to retrieve secrets from the vault and unwrap keys.')
        c.argument('enabled_for_template_deployment', arg_type=get_three_state_flag(), help='Allow Resource Manager to retrieve secrets from the vault.')
        c.argument('enable_soft_delete', arg_type=get_three_state_flag(), help='Enable vault deletion recovery for the vault, and all contained entities')

    with self.argument_context('keyvault create') as c:
        c.argument('resource_group_name', resource_group_name_type, required=True, completer=None, validator=None)
        c.argument('vault_name', completer=None)
        c.argument('sku', arg_type=get_enum_type(SkuName, default=SkuName.standard.value))
        c.argument('no_self_perms', arg_type=get_three_state_flag(), help="Don't add permissions for the current user/service principal in the new vault.")
        c.argument('location', validator=get_default_location_from_resource_group)

    with self.argument_context('keyvault list') as c:
        c.argument('resource_group_name', resource_group_name_type, validator=None)

    with self.argument_context('keyvault delete-policy') as c:
        c.argument('object_id', validator=validate_principal)

    with self.argument_context('keyvault set-policy', arg_group='Permission') as c:
        c.argument('key_permissions', arg_type=get_enum_type(KeyPermissions), metavar='PERM', nargs='*', help='Space-separated list of key permissions to assign.', validator=validate_policy_permissions)
        c.argument('secret_permissions', arg_type=get_enum_type(SecretPermissions), metavar='PERM', nargs='*', help='Space-separated list of secret permissions to assign.')
        c.argument('certificate_permissions', arg_type=get_enum_type(CertificatePermissions), metavar='PERM', nargs='*', help='Space-separated list of certificate permissions to assign.')
    # endregion

    # region Shared
    for item in ['key', 'secret', 'certificate']:
        with self.argument_context('keyvault ' + item) as c:
            c.argument(item + '_name', options_list=['--name', '-n'], help='Name of the {}.'.format(item), id_part='child_name_1', completer=get_keyvault_name_completion_list(item))
            c.argument('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None)
    # endregion

    # region keys
    with self.argument_context('keyvault key') as c:
        c.argument('key_ops', arg_type=get_enum_type(JsonWebKeyOperation), options_list=['--ops'], nargs='*', help='Space-separated list of permitted JSON web key operations.')
        c.argument('key_version', options_list=['--version', '-v'], help='The key version. If omitted, uses the latest version.', default='', required=False, completer=get_keyvault_version_completion_list('key'))

    for scope in ['keyvault key create', 'keyvault key import']:
        with self.argument_context(scope) as c:
            c.argument('destination', arg_type=get_enum_type(['software', 'hsm']), options_list=['--protection', '-p'], help='Specifies the type of key protection.', validator=validate_key_type)
            c.argument('disabled', arg_type=get_three_state_flag(), help='Create key in disabled state.')
            c.argument('key_size', options_list=['--size'], type=int)
            c.argument('expires', default=None, help='Expiration UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').', type=datetime_type)
            c.argument('not_before', default=None, help='Key not usable before the provided UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').', type=datetime_type)

    with self.argument_context('keyvault key import', arg_group='Key Source') as c:
        c.argument('pem_file', type=file_type, help='PEM file containing the key to be imported.', completer=FilesCompleter(), validator=validate_key_import_source)
        c.argument('pem_password', help='Password of PEM file.')
        c.argument('byok_file', type=file_type, help='BYOK file containing the key to be imported. Must not be password protected.', completer=FilesCompleter())

    with self.argument_context('keyvault key backup') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(), help='Local file path in which to store key backup.')

    with self.argument_context('keyvault key restore') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(), help='Local key backup from which to restore key.')

    with self.argument_context('keyvault key set-attributes') as c:
        c.attributes_argument('key', KeyAttributes)
    # endregion

    # region KeyVault Secret
    with self.argument_context('keyvault secret') as c:
        c.argument('secret_version', options_list=['--version', '-v'], help='The secret version. If omitted, uses the latest version.', default='', required=False, completer=get_keyvault_version_completion_list('secret'))

    with self.argument_context('keyvault secret set') as c:
        c.argument('content_type', options_list=['--description'], help='Description of the secret contents (e.g. password, connection string, etc)')
        c.attributes_argument('secret', SecretAttributes, create=True)

    with self.argument_context('keyvault secret set', arg_group='Content Source') as c:
        c.argument('value', options_list=['--value'], help="Plain text secret value. Cannot be used with '--file' or '--encoding'", required=False)
        c.extra('file_path', options_list=['--file', '-f'], type=file_type, help="Source file for secret. Use in conjunction with '--encoding'", completer=FilesCompleter())
        c.extra('encoding', arg_type=get_enum_type(secret_encoding_values, default='utf-8'), options_list=['--encoding', '-e'], help='Source file encoding. The value is saved as a tag (`file-encoding=<val>`) and used during download to automatically encode the resulting file.')

    with self.argument_context('keyvault secret set-attributes') as c:
        c.attributes_argument('secret', SecretAttributes)

    with self.argument_context('keyvault secret download') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(), help='File to receive the secret contents.')
        c.argument('encoding', arg_type=get_enum_type(secret_encoding_values), options_list=['--encoding', '-e'], help="Encoding of the destination file. By default, will look for the 'file-encoding' tag on the secret. Otherwise will assume 'utf-8'.", default=None)
    # endregion

    # KeyVault Certificate
    with self.argument_context('keyvault certificate') as c:
        c.argument('certificate_version', options_list=['--version', '-v'], help='The certificate version. If omitted, uses the latest version.', default='', required=False, completer=get_keyvault_version_completion_list('certificate'))
        c.argument('validity', type=int, help='Number of months the certificate is valid for. Overrides the value specified with --policy/-p')

    # TODO: Remove workaround when https://github.com/Azure/azure-rest-api-specs/issues/1153 is fixed
    with self.argument_context('keyvault certificate create') as c:
        c.attributes_argument('certificate', CertificateAttributes, True, ignore=['expires', 'not_before'])

    with self.argument_context('keyvault certificate set-attributes') as c:
        c.attributes_argument('certificate', CertificateAttributes, ignore=['expires', 'not_before'])

    for item in ['create', 'set-attributes', 'import']:
        with self.argument_context('keyvault certificate ' + item) as c:
            c.argument('certificate_policy', options_list=['--policy', '-p'], help='JSON encoded policy defintion. Use @{file} to load from a file.', type=get_json_object)

    with self.argument_context('keyvault certificate import') as c:
        c.argument('certificate_data', options_list=['--file', '-f'], completer=FilesCompleter(), help='PKCS12 file or PEM file containing the certificate and private key.', type=certificate_type)
        c.argument('password', help="If the private key in certificate is encrypted, the password used for encryption.")
        c.extra('disabled', arg_type=get_three_state_flag(), help='Import the certificate in disabled state.')

    with self.argument_context('keyvault certificate download') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(), help='File to receive the binary certificate contents.')
        c.argument('encoding', arg_type=get_enum_type(certificate_format_values), options_list=['--encoding', '-e'], help='Encoding of the certificate. DER will create a binary DER formatted x509 certificate, and PEM will create a base64 PEM x509 certificate.')

    # TODO: Fix once service side issue is fixed that there is no way to list pending certificates
    with self.argument_context('keyvault certificate pending') as c:
        c.argument('certificate_name', options_list=['--name', '-n'], help='Name of the pending certificate.', id_part='child_name_1', completer=None)

    with self.argument_context('keyvault certificate pending merge') as c:
        c.argument('x509_certificates', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(), help='File containing the certificate or certificate chain to merge.', validator=validate_x509_certificate_chain)
        c.attributes_argument('certificate', CertificateAttributes, True)

    with self.argument_context('keyvault certificate pending cancel') as c:
        c.ignore('cancellation_requested')

    with self.argument_context('keyvault certificate contact') as c:
        c.argument('contact_email', options_list=['--email'], help='Contact e-mail address. Must be unique.')
        c.argument('contact_name', options_list=['--name'], help='Full contact name.')
        c.argument('contact_phone', options_list=['--phone'], help='Contact phone number.')

    with self.argument_context('keyvault certificate issuer admin') as c:
        c.argument('email', options_list=['--email'], help='Admin e-mail address. Must be unique within the vault.')
        c.argument('name', options_list=['--name'], help='Full admin name.')
        c.argument('phone', options_list=['--phone'], help='Amin phone number.')

    with self.argument_context('keyvault certificate issuer') as c:
        c.argument('issuer_name', help='Certificate issuer name.')
        c.argument('disabled', arg_type=get_three_state_flag(), help='Set issuer to disabled state.')
        c.argument('enabled', arg_type=get_three_state_flag(), help='Set issuer enabled state.')

    with self.argument_context('keyvault certificate issuer', arg_group='Issuer Credential') as c:
        c.argument('account_id')
        c.argument('password')

    with self.argument_context('keyvault certificate issuer', arg_group='Organization Detail') as c:
        c.argument('organization_id')
        c.argument('admin_first_name')
        c.argument('admin_last_name')
        c.argument('admin_email')
        c.argument('admin_phone')
    # endregion
