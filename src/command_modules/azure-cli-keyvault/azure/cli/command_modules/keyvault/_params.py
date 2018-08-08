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
from azure.cli.core.profiles import ResourceType, get_sdk

from ._completers import (
    get_keyvault_name_completion_list, get_keyvault_version_completion_list)
from ._validators import (
    datetime_type, certificate_type,
    get_vault_base_url_type, validate_key_import_source,
    validate_key_type, validate_policy_permissions,
    validate_principal, validate_resource_group_name,
    validate_x509_certificate_chain,
    secret_text_encoding_values, secret_binary_encoding_values, validate_subnet,
    validate_vault_id, validate_sas_definition_id, validate_storage_account_id, validate_storage_disabled_attribute)

# CUSTOM CHOICE LISTS

secret_encoding_values = secret_text_encoding_values + secret_binary_encoding_values
certificate_format_values = ['PEM', 'DER']


# pylint: disable=too-many-locals, too-many-branches, too-many-statements, line-too-long
def load_arguments(self, _):
    JsonWebKeyOperation = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.key_vault_client_enums#JsonWebKeyOperation')
    KeyAttributes = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.key_attributes#KeyAttributes')
    JsonWebKeyType = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.key_vault_client_enums#JsonWebKeyType')
    JsonWebKeyCurveName = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.key_vault_client_enums#JsonWebKeyCurveName')
    SasTokenType = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.key_vault_client_enums#SasTokenType')
    SasDefinitionAttributes = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.sas_definition_attributes#SasDefinitionAttributes')
    SecretAttributes = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.secret_attributes#SecretAttributes')
    CertificateAttributes = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.certificate_attributes#CertificateAttributes')
    StorageAccountAttributes = get_sdk(self.cli_ctx, ResourceType.DATA_KEYVAULT, 'models.storage_account_attributes#StorageAccountAttributes')
    SkuName = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT, 'models.key_vault_management_client_enums#SkuName')
    KeyPermissions = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT, 'models.key_vault_management_client_enums#KeyPermissions')
    SecretPermissions = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT, 'models.key_vault_management_client_enums#SecretPermissions')
    CertificatePermissions = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT, 'models.key_vault_management_client_enums#CertificatePermissions')
    StoragePermissions = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT, 'models.key_vault_management_client_enums#StoragePermissions')
    NetworkRuleBypassOptions = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT, 'models.key_vault_management_client_enums#NetworkRuleBypassOptions')
    NetworkRuleAction = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT, 'models.key_vault_management_client_enums#NetworkRuleAction')
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
        c.argument('enable_purge_protection', arg_type=get_three_state_flag(), help='Prevents manual purging of deleted vault, and all contained entities')

    with self.argument_context('keyvault', arg_group='Network Rule', min_api='2018-02-14') as c:
        c.argument('bypass', arg_type=get_enum_type(NetworkRuleBypassOptions), help='Bypass traffic for space-separated uses.')
        c.argument('default_action', arg_type=get_enum_type(NetworkRuleAction), help='Default action to apply when no rule matches.')

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
        c.argument('storage_permissions', arg_type=get_enum_type(StoragePermissions), metavar='PERM', nargs='*', help='Space-separated list of storage permissions to assign.')

    with self.argument_context('keyvault network-rule', min_api='2018-02-14') as c:
        c.argument('ip_address', help='IPv4 address or CIDR range.')
        c.argument('subnet', help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
        c.argument('vnet_name', help='Name of a virtual network.', validator=validate_subnet)
    # endregion

    # region Shared
    for item in ['key', 'secret', 'certificate']:
        with self.argument_context('keyvault ' + item, arg_group='Id') as c:
            c.argument(item + '_name', options_list=['--name', '-n'], help='Name of the {}.'.format(item), id_part='child_name_1', completer=get_keyvault_name_completion_list(item))
            c.argument('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None)
            c.argument(item + '_version', options_list=['--version', '-v'], help='The {} version. If omitted, uses the latest version.'.format(item), default='', required=False, completer=get_keyvault_version_completion_list(item))

        for cmd in ['backup', 'delete', 'download', 'set-attributes', 'show']:
            with self.argument_context('keyvault {} {}'.format(item, cmd), arg_group='Id') as c:
                c.extra('identifier', options_list=['--id'], help='Id of the {}.  If specified all other \'Id\' arguments should be omitted.'.format(item), validator=validate_vault_id(item))
                c.argument(item + '_name', help='Name of the {}. Required if --id is not specified.'.format(item), required=False)
                c.argument('vault_base_url', help='Name of the key vault. Required if --id is not specified.', required=False)
                c.argument(item + '_version', required=False)

        for cmd in ['purge', 'recover', 'show-deleted']:
            with self.argument_context('keyvault {} {}'.format(item, cmd), arg_group='Id') as c:
                c.extra('identifier', options_list=['--id'], help='The recovery id of the {}.  If specified all other \'Id\' arguments should be omitted.'.format(item), validator=validate_vault_id('deleted' + item))
                c.argument(item + '_name', help='Name of the {}. Required if --id is not specified.'.format(item), required=False)
                c.argument('vault_base_url', help='Name of the key vault. Required if --id is not specified.', required=False)
                c.argument(item + '_version', required=False)
    # endregion

    # region keys
    with self.argument_context('keyvault key') as c:
        c.argument('key_ops', arg_type=get_enum_type(JsonWebKeyOperation), options_list=['--ops'], nargs='*', help='Space-separated list of permitted JSON web key operations.')

    for scope in ['keyvault key create', 'keyvault key import']:
        with self.argument_context(scope) as c:
            c.argument('protection', arg_type=get_enum_type(['software', 'hsm']), options_list=['--protection', '-p'], help='Specifies the type of key protection.')
            c.argument('disabled', arg_type=get_three_state_flag(), help='Create key in disabled state.')
            c.argument('key_size', options_list=['--size'], type=int)
            c.argument('expires', default=None, help='Expiration UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').', type=datetime_type)
            c.argument('not_before', default=None, help='Key not usable before the provided UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').', type=datetime_type)

    with self.argument_context('keyvault key create') as c:
        c.argument('kty', arg_type=get_enum_type(JsonWebKeyType), validator=validate_key_type)
        c.argument('curve', arg_type=get_enum_type(JsonWebKeyCurveName))

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

    # region KeyVault Storage Account

    with self.argument_context('keyvault storage', arg_group='Id') as c:
        c.argument('storage_account_name', options_list=['--name', '-n'], help='Name to identify the storage account in the vault.', id_part='child_name_1', completer=get_keyvault_name_completion_list('storage_account'))
        c.argument('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None)

    for scope in ['keyvault storage add', 'keyvault storage update']:
        with self.argument_context(scope) as c:
            c.extra('disabled', arg_type=get_three_state_flag(), help='Add the storage account in a disabled state.', validator=validate_storage_disabled_attribute('storage_account_attributes', StorageAccountAttributes))
            c.ignore('storage_account_attributes')
            c.argument('auto_regenerate_key', arg_type=get_three_state_flag(), required=False)
            c.argument('regeneration_period', help='The key regeneration time duration specified in ISO-8601 format, such as "P30D" for rotation every 30 days.')
    for scope in ['backup', 'show', 'update', 'remove', 'regenerate-key']:
        with self.argument_context('keyvault storage ' + scope, arg_group='Id') as c:
            c.extra('identifier', options_list=['--id'], help='Id of the storage account.  If specified all other \'Id\' arguments should be omitted.', validator=validate_storage_account_id)
            c.argument('storage_account_name', required=False, help='Name to identify the storage account in the vault. Required if --id is not specified.')
            c.argument('vault_base_url', help='Name of the key vault. Required if --id is not specified.', required=False)

    with self.argument_context('keyvault storage backup') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(), help='Local file path in which to store storage account backup.')

    with self.argument_context('keyvault storagerestore') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(), help='Local key backup from which to restore storage account.')

    with self.argument_context('keyvault storage sas-definition', arg_group='Id') as c:
        c.argument('storage_account_name', options_list=['--account-name'], help='Name to identify the storage account in the vault.', id_part='child_name_1', completer=get_keyvault_name_completion_list('storage_account'))
        c.argument('sas_definition_name', options_list=['--name', '-n'], help='Name to identify the SAS definition in the vault.', id_part='child_name_2')

    for scope in ['keyvault storage sas-definition create', 'keyvault storage sas-definition update']:
        with self.argument_context(scope) as c:
            c.extra('disabled', arg_type=get_three_state_flag(), help='Add the storage account in a disabled state.', validator=validate_storage_disabled_attribute('sas_definition_attributes', SasDefinitionAttributes))
            c.ignore('sas_definition_attributes')
            c.argument('sas_type', arg_type=get_enum_type(SasTokenType))
            c.argument('template_uri', help='The SAS definition token template signed with the key 00000000.  In the case of an account token this is only the sas token itself, for service tokens, the full service endpoint url along with the sas token.  Tokens created according to the SAS definition will have the same properties as the template.')
            c.argument('validity_period', help='The validity period of SAS tokens created according to the SAS definition in ISO-8601, such as "PT12H" for 12 hour tokens.')
            c.argument('auto_regenerate_key', arg_type=get_three_state_flag())

    for scope in ['keyvault storage sas-definition delete', 'keyvault storage sas-definition show', 'keyvault storage sas-definition update']:
        with self.argument_context(scope, arg_group='Id') as c:
            c.extra('identifier', options_list=['--id'], help='Id of the SAS definition.  If specified all other \'Id\' arguments should be omitted.', validator=validate_sas_definition_id)
            c.argument('storage_account_name', required=False, help='Name to identify the storage account in the vault. Required if --id is not specified.')
            c.argument('sas_definition_name', required=False, help='Name to identify the SAS definition in the vault. Required if --id is not specified.')
            c.argument('vault_base_url', help='Name of the key vault. Required if --id is not specified.', required=False)
    # endregion

    # KeyVault Certificate
    with self.argument_context('keyvault certificate') as c:
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
