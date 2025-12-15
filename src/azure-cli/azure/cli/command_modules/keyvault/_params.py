# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from enum import Enum

from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

import azure.cli.core.commands.arm  # pylint: disable=unused-import
from azure.cli.core.commands.validators import get_default_location_from_resource_group, validate_file_or_dict
from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list, resource_group_name_type, tags_type, file_type, get_three_state_flag,
    get_enum_type)
from azure.cli.core.util import get_json_object
from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.keyvault._completers import (
    get_keyvault_name_completion_list, get_keyvault_version_completion_list)
from azure.cli.command_modules.keyvault._validators import (
    datetime_type, certificate_type, validate_retention_days_on_creation,
    get_vault_base_url_type, get_hsm_base_url_type, validate_key_import_type,
    validate_key_import_source, validate_key_type, validate_policy_permissions, validate_principal,
    validate_resource_group_name, validate_x509_certificate_chain,
    secret_text_encoding_values, secret_binary_encoding_values, validate_subnet, validate_ip_address,
    validate_vault_or_hsm,
    validate_deleted_vault_or_hsm_name, validate_encryption, validate_decryption,
    validate_vault_name_and_hsm_name, set_vault_base_url, validate_keyvault_resource_id,
    process_hsm_name, KeyEncryptionDataType, process_key_release_policy, process_certificate_policy,
    process_certificate_import)

# CUSTOM CHOICE LISTS

secret_encoding_values = secret_text_encoding_values + secret_binary_encoding_values
key_format_values = certificate_format_values = ['PEM', 'DER']


# pylint: disable=too-many-locals, too-many-branches, too-many-statements, line-too-long
def load_arguments(self, _):

    JsonWebKeyType = self.get_sdk('KeyType', resource_type=ResourceType.DATA_KEYVAULT_KEYS, mod='_enums')
    KeyCurveName = self.get_sdk('KeyCurveName', resource_type=ResourceType.DATA_KEYVAULT_KEYS, mod='_enums')
    EncryptionAlgorithm = self.get_sdk('EncryptionAlgorithm', resource_type=ResourceType.DATA_KEYVAULT_KEYS, mod='crypto._enums')
    SignatureAlgorithm = self.get_sdk('SignatureAlgorithm', resource_type=ResourceType.DATA_KEYVAULT_KEYS, mod='crypto._enums')

    class CLIJsonWebKeyOperation(str, Enum):
        encrypt = "encrypt"
        decrypt = "decrypt"
        sign = "sign"
        verify = "verify"
        wrap_key = "wrapKey"
        unwrap_key = "unwrapKey"
        import_ = "import"
        export = "export"

    JsonWebKeyOperation = CLIJsonWebKeyOperation  # TODO: Remove this patch when new SDK is released

    class CLIKeyTypeForBYOKImport(str, Enum):
        ec = "EC"  #: Elliptic Curve.
        rsa = "RSA"  #: RSA (https://tools.ietf.org/html/rfc3447)
        oct = "oct"  #: Octet sequence (used to represent symmetric keys)

    class CLISecurityDomainOperation(str, Enum):
        download = "download"  #: Download operation
        upload = "upload"  #: Upload operation
        restore_blob = "restore_blob"  #: Restore blob operation

    (KeyPermissions, SecretPermissions, CertificatePermissions, StoragePermissions,
     NetworkRuleBypassOptions, NetworkRuleAction, PublicNetworkAccess) = self.get_models(
        'KeyPermissions', 'SecretPermissions', 'CertificatePermissions', 'StoragePermissions',
        'NetworkRuleBypassOptions', 'NetworkRuleAction', 'PublicNetworkAccess',
        resource_type=ResourceType.MGMT_KEYVAULT)

    # ARGUMENT DEFINITIONS
    vault_name_type = CLIArgumentType(
        help='Name of the Vault.', options_list=['--vault-name'], metavar='NAME', id_part=None,
        completer=get_resource_name_completion_list('Microsoft.KeyVault/vaults'))

    deleted_vault_name_type = CLIArgumentType(
        help='Name of the deleted Vault.', options_list=['--vault-name'], metavar='NAME', id_part=None)

    hsm_name_type = CLIArgumentType(help='Name of the HSM.',
                                    options_list=['--hsm-name'], id_part=None)
    hsm_url_type = CLIArgumentType(help='Name of the HSM.', type=get_hsm_base_url_type(self.cli_ctx),
                                   options_list=['--hsm-name'], id_part=None)

    mgmt_plane_hsm_name_type = CLIArgumentType(help='Name of the HSM. (--hsm-name and --name/-n are mutually '
                                                    'exclusive, please specify just one of them)',
                                               options_list=['--hsm-name'], id_part=None,
                                               validator=validate_vault_name_and_hsm_name)

    data_plane_hsm_name_type = CLIArgumentType(help='Name of the HSM. (--hsm-name and --vault-name are '
                                                    'mutually exclusive, please specify just one of them)',
                                               type=get_hsm_base_url_type(self.cli_ctx),
                                               options_list=['--hsm-name'], id_part=None,
                                               validator=set_vault_base_url)

    deleted_hsm_name_type = CLIArgumentType(help='Name of the deleted HSM. (--hsm-name and --name/-n are '
                                                 'mutually exclusive, please specify just one of them)',
                                            options_list=['--hsm-name'], id_part=None,
                                            validator=validate_vault_name_and_hsm_name)

    # region vault (management)
    with self.argument_context('keyvault') as c:
        c.argument('resource_group_name', resource_group_name_type, id_part=None, required=False,
                   help='Name of resource group.',
                   validator=validate_resource_group_name)
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'])
        c.argument('object_id', help='a GUID that identifies the principal that will receive permissions')
        c.argument('spn', help='name of a service principal that will receive permissions')
        c.argument('upn', help='name of a user principal that will receive permissions')
        c.argument('tags', tags_type)
        c.argument('enabled_for_deployment', arg_type=get_three_state_flag(),
                   help='[Vault Only] Property to specify whether Azure Virtual Machines are permitted to retrieve '
                        'certificates stored as secrets from the key vault.')
        c.argument('enabled_for_disk_encryption', arg_type=get_three_state_flag(),
                   help='[Vault Only] Property to specify whether Azure Disk Encryption is permitted to retrieve '
                        'secrets from the vault and unwrap keys.')
        c.argument('enabled_for_template_deployment', arg_type=get_three_state_flag(),
                   help='[Vault Only] Property to specify whether Azure Resource Manager is permitted to retrieve '
                        'secrets from the key vault.')
        c.argument('enable_rbac_authorization', arg_type=get_three_state_flag(),
                   help='Property that controls how data actions are authorized. When true, the key vault will use '
                        'Role Based Access Control (RBAC) for authorization of data actions, and the access policies '
                        'specified in vault properties will be ignored. When false, the key vault will use the access '
                        'policies specified in vault properties, and any policy stored on Azure Resource Manager will '
                        'be ignored. If null or not specified, the vault is created with the default value of true. '
                        'Note that management actions are always authorized with RBAC.')
        c.argument('enable_purge_protection', arg_type=get_three_state_flag(),
                   help='Property specifying whether protection against purge is enabled for this vault/managed HSM '
                        'pool. Setting this property to true activates protection against purge for this vault/managed '
                        'HSM pool and its content - only the Key Vault/Managed HSM service may initiate a hard, '
                        'irrecoverable deletion. The setting is effective only if soft delete is also enabled. '
                        'Enabling this functionality is irreversible.')
        c.argument('public_network_access', arg_type=get_enum_type(PublicNetworkAccess),
                   help='Control permission for data plane traffic coming from public networks '
                        'while private endpoint is enabled')

    with self.argument_context('keyvault', arg_group='Network Rule') as c:
        c.argument('bypass', arg_type=get_enum_type(NetworkRuleBypassOptions),
                   help='Bypass traffic for space-separated uses.')
        c.argument('default_action', arg_type=get_enum_type(NetworkRuleAction),
                   help='Default action to apply when no rule matches.')

    with self.argument_context('keyvault check-name') as c:
        c.argument('name', options_list=['--name', '-n'],
                   help='The name of the HSM within the specified resource group')
        c.argument('resource_type', arg_type=get_enum_type(['hsm']), help='Type of resource. ')

    for item in ['show', 'delete', 'create']:
        with self.argument_context('keyvault {}'.format(item)) as c:
            c.argument('hsm_name', mgmt_plane_hsm_name_type)

    with self.argument_context('keyvault create') as c:
        c.argument('resource_group_name', resource_group_name_type, required=True, completer=None, validator=None)
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'])
        c.argument('administrators', nargs='+',
                   help='[HSM Only] Administrator role for data plane operations for Managed HSM. '
                        'It accepts a space separated list of OIDs that will be assigned.')
        c.argument('sku', help='Required. SKU details. Allowed values for Vault: premium, standard. Default: standard.'
                               ' Allowed values for HSM: Standard_B1, Custom_B32, Custom_B6, Custom_C42, Custom_C10. Default: Standard_B1')
        c.argument('no_self_perms', arg_type=get_three_state_flag(),
                   help='[Vault Only] Don\'t add permissions for the current user/service principal in the new vault.')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('retention_days', validator=validate_retention_days_on_creation,
                   help='Soft delete data retention days. It accepts >=7 and <=90. '
                        'Defaults to 90 for keyvault creation. Required for MHSM creation')
        c.argument('user_identities', options_list=['--mi-user-assigned'], nargs='*',
                   resource_type=ResourceType.MGMT_KEYVAULT, operation_group="managed_hsms",
                   help="[HSM Only] Enable user-assigned managed identities for managed HSM. "
                        "Accept space-separated list of identity resource IDs.")

    with self.argument_context('keyvault create', arg_group='Network Rule') as c:
        c.argument('network_acls', type=validate_file_or_dict,
                   help='Network ACLs. It accepts a JSON filename or a JSON string. JSON format: '
                        '`{\\"ip\\":[<ip1>, <ip2>...],\\"vnet\\":[<vnet_name_1>/<subnet_name_1>,<subnet_id2>...]}`')
        c.argument('network_acls_ips', nargs='*', help='Network ACLs IP rules. Space-separated list of IP addresses.')
        c.argument('network_acls_vnets', nargs='*', help='Network ACLS VNet rules. Space-separated list of '
                                                         'Vnet/subnet pairs or subnet resource ids.')

    with self.argument_context('keyvault update') as c:
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'])
        c.argument('retention_days', help='Soft delete data retention days. It accepts >=7 and <=90.')

    with self.argument_context('keyvault update-hsm', resource_type=ResourceType.MGMT_KEYVAULT, operation_group="managed_hsms") as c:
        c.argument('name', hsm_name_type)
        c.argument('enable_purge_protection', options_list=['--enable-purge-protection', '-e'])
        c.argument('secondary_locations', nargs='+',
                   help='--secondary-locations extends/contracts an HSM pool to listed regions. The primary location '
                        'where the resource was originally created CANNOT be removed.')
        c.argument('user_identities', options_list=['--mi-user-assigned'], nargs='*',
                   help="Enable user-assigned managed identities for managed HSM. "
                        "Accept space-separated list of identity resource IDs.")

    with self.argument_context('keyvault wait-hsm') as c:
        c.argument('hsm_name', hsm_name_type)
        c.argument('resource_group_name', options_list=['--resource-group', '-g'],
                   help='Proceed only if HSM belongs to the specified resource group.')

    with self.argument_context('keyvault recover') as c:
        c.argument('vault_name', deleted_vault_name_type, options_list=['--name', '-n'],
                   validator=validate_deleted_vault_or_hsm_name)
        c.argument('hsm_name', deleted_hsm_name_type)
        c.argument('resource_group_name', resource_group_name_type, id_part=None, required=False,
                   help='Resource group of the deleted Vault or HSM')
        c.argument('location', help='Location of the deleted Vault or HSM', required=False)

    with self.argument_context('keyvault purge') as c:
        c.argument('vault_name', deleted_vault_name_type, options_list=['--name', '-n'],
                   validator=validate_deleted_vault_or_hsm_name)
        c.argument('hsm_name', deleted_hsm_name_type)
        c.argument('location', help='Location of the deleted Vault or HSM', required=False)

    with self.argument_context('keyvault list') as c:
        c.argument('resource_group_name', resource_group_name_type, validator=None)
        c.argument('resource_type', help='When --resource-type is not present the command will list all Vaults and HSMs.'
                                         ' Possible values for --resource-type are vault and hsm.')

    with self.argument_context('keyvault list-deleted') as c:
        c.argument('resource_type', help='When --resource-type is not present the command will list all deleted Vaults '
                                         'and HSMs. Possible values for --resource-type are vault and hsm.')

    with self.argument_context('keyvault show-deleted') as c:
        c.argument('vault_name', deleted_vault_name_type, options_list=['--name', '-n'],
                   validator=validate_deleted_vault_or_hsm_name)
        c.argument('hsm_name', deleted_hsm_name_type)
        c.argument('location', help='Location of the deleted Vault or HSM', required=False)

    for item in ['set-policy', 'delete-policy']:
        with self.argument_context('keyvault {}'.format(item)) as c:
            c.argument('object_id', validator=validate_principal)
            c.argument('application_id', help='Application ID of the client making request on behalf of a principal. '
                                              'Exposed for compound identity using on-behalf-of authentication flow.')

    with self.argument_context('keyvault set-policy', arg_group='Permission') as c:
        c.argument('key_permissions', arg_type=get_enum_type(KeyPermissions), metavar='PERM', nargs='*',
                   help='Space-separated list of key permissions to assign.', validator=validate_policy_permissions)
        c.argument('secret_permissions', arg_type=get_enum_type(SecretPermissions), metavar='PERM', nargs='*',
                   help='Space-separated list of secret permissions to assign.')
        c.argument('certificate_permissions', arg_type=get_enum_type(CertificatePermissions), metavar='PERM', nargs='*',
                   help='Space-separated list of certificate permissions to assign.')
        c.argument('storage_permissions', arg_type=get_enum_type(StoragePermissions), metavar='PERM', nargs='*',
                   help='Space-separated list of storage permissions to assign.')

    with self.argument_context('keyvault network-rule') as c:
        c.argument('hsm_name', mgmt_plane_hsm_name_type)
        c.argument('ip_address', help='IPv4 address or CIDR range.')
        c.argument('subnet', help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
        c.argument('vnet_name', help='Name of a virtual network.', validator=validate_subnet)

    for item in ['add', 'remove']:
        with self.argument_context('keyvault network-rule {}'.format(item)) as c:
            c.argument('ip_address', nargs='*', help='IPv4 address or CIDR range. Can supply a list: --ip-address ip1 '
                                                     '[ip2]...', validator=validate_ip_address)

    for item in ['approve', 'reject', 'delete', 'show', 'wait']:
        with self.argument_context('keyvault private-endpoint-connection {}'.format(item)) as c:
            c.extra('connection_id', options_list=['--id'], required=False,
                    help='The ID of the private endpoint connection associated with the Key Vault/HSM. '
                         'If specified --vault-name/--hsm-name and --name/-n, this should be omitted.')
            c.argument('description', help='Comments for the {} operation.'.format(item))
            c.argument('private_endpoint_connection_name', options_list=['--name', '-n'], required=False,
                       help='The name of the private endpoint connection associated with the Key Vault/HSM. '
                            'Required if --id is not specified')
            c.argument('vault_name', vault_name_type, required=False,
                       help='Name of the Key Vault. Required if --id is not specified')
            c.argument('hsm_name', mgmt_plane_hsm_name_type,
                       help='Name of the HSM. Required if --id is not specified.'
                            '(--hsm-name and --vault-name are mutually exclusive, please specify just one of them)')

    with self.argument_context('keyvault private-endpoint-connection list') as c:
        c.argument("hsm_name", hsm_name_type)

    with self.argument_context('keyvault private-link-resource') as c:
        c.argument('vault_name', vault_name_type)
        c.argument('hsm_name', mgmt_plane_hsm_name_type)
    # endregion

    # region keys
    with self.argument_context('keyvault key') as c:
        c.argument('key_ops', arg_type=get_enum_type(JsonWebKeyOperation), options_list=['--ops'], nargs='*',
                   help='Space-separated list of permitted JSON web key operations.')

    # keys track2
    for scope in ['create', 'import', 'set-attributes', 'show', 'show-deleted', 'delete', 'list', 'list-deleted',
                  'list-versions', 'encrypt', 'decrypt', 'sign', 'verify', 'recover', 'purge', 'download',
                  'backup', 'restore', 'rotate', 'get-attestation', 'rotation-policy show', 'rotation-policy update']:
        with self.argument_context('keyvault key {}'.format(scope), arg_group='Id') as c:
            c.argument('name', options_list=['--name', '-n'], id_part='child_name_1',
                       required=False, completer=get_keyvault_name_completion_list('key'),
                       help='Name of the key. Required if --id is not specified.')
            c.argument('version', options_list=['--version', '-v'],
                       help='The key version. If omitted, uses the latest version.', default='',
                       required=False, completer=get_keyvault_version_completion_list('key'))
            c.extra('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None)
            c.extra('hsm_name', data_plane_hsm_name_type, required=False)
            c.extra('identifier', options_list=['--id'],
                    help='Id of the key. If specified all other \'Id\' arguments should be omitted.',
                    validator=validate_keyvault_resource_id('key'))

    for item in ['list', 'list-deleted', 'restore']:
        with self.argument_context(f'keyvault key {item}') as c:
            c.extra('hsm_name', hsm_url_type, required=False, arg_group='Id',
                    help='Name of the HSM. Can be omitted if --id is specified.')
            c.extra('identifier', options_list=['--id'], validator=validate_vault_or_hsm, arg_group='Id',
                    help='Full URI of the Vault or HSM. If specified all other \'Id\' arguments should be omitted.')

    for item in ['recover', 'purge']:
        with self.argument_context(f'keyvault key {item}') as c:
            c.extra('identifier', options_list=['--id'], arg_group='Id',
                    help='The recovery id of the key. If specified all other \'Id\' arguments should be omitted.',
                    validator=validate_keyvault_resource_id('key'))

    with self.argument_context('keyvault key get-attestation') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help="File to receive the key's attestation if you want to save it.")
        c.extra('hsm_name', data_plane_hsm_name_type, required=False, arg_group='Id',
                help='Name of the HSM. Required if --id is not specified.')
        c.ignore('vault_base_url')

    with self.argument_context('keyvault key list') as c:
        c.extra('include_managed', arg_type=get_three_state_flag(), default=False,
                help='Include managed keys.')
        c.argument('maxresults', options_list=['--maxresults'], type=int, help='Maximum number of results to return.')

    for item in ['list-versions', 'list-deleted']:
        with self.argument_context(f'keyvault key {item}') as c:
            c.extra('max_page_size', options_list=['--maxresults'], type=int, help='Maximum number of results to return.')

    for item in ['create', 'import']:
        with self.argument_context('keyvault key {}'.format(item)) as c:
            c.argument('protection', arg_type=get_enum_type(['software', 'hsm']), options_list=['--protection', '-p'],
                       help='Specifies the type of key protection.')
            c.argument('disabled', arg_type=get_three_state_flag(), help='Create key in disabled state.')
            c.argument('key_size', options_list=['--size'], type=int,
                       help='The key size in bits. For example: 2048, 3072, or 4096 for RSA. 128, 192, or 256 for oct.')
            c.argument('expires', default=None, help='Expiration UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').',
                       type=datetime_type)
            c.argument('not_before', default=None, type=datetime_type,
                       help='Key not usable before the provided UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').')
            c.argument('exportable', arg_type=get_three_state_flag(),
                       help='Whether the private key can be exported. To create key with release policy, '
                            '"exportable" must be true and caller must have "export" permission.')
            c.argument('release_policy', options_list=['--policy'], type=file_type, completer=FilesCompleter(),
                       validator=process_key_release_policy,
                       help='The policy rules under which the key can be exported. '
                            'Policy definition as JSON, or a path to a file containing JSON policy definition.')
            c.extra('default_cvm_policy', action='store_true',
                    help='Use default policy under which the key can be exported for CVM disk encryption.')
            c.extra('default_data_disk_policy', action='store_true', options_list=['--default-data-disk-policy', '--default-dd-policy'],
                    help='Use default policy under which the key can be exported for data disk encryption.')
            c.extra('immutable', arg_type=get_three_state_flag(), is_preview=True,
                    help='Mark a release policy as immutable. '
                         'An immutable release policy cannot be changed or updated after being marked immutable. '
                         'Release policies are mutable by default.')

    with self.argument_context('keyvault key create') as c:
        c.argument('kty', arg_type=get_enum_type(JsonWebKeyType), validator=validate_key_type,
                   help='The type of key to create. For valid values, see: https://learn.microsoft.com/rest/api/keyvault/keys/create-key/create-key#jsonwebkeytype')
        c.argument('curve', arg_type=get_enum_type(KeyCurveName),
                   help='Elliptic curve name. For valid values, see: https://learn.microsoft.com/rest/api/keyvault/keys/create-key/create-key#jsonwebkeycurvename')

    with self.argument_context('keyvault key import') as c:
        c.argument('kty', arg_type=get_enum_type(CLIKeyTypeForBYOKImport), validator=validate_key_import_type,
                   help='The type of key to import (only for BYOK).')
        c.argument('curve', arg_type=get_enum_type(KeyCurveName), validator=validate_key_import_type,
                   help='The curve name of the key to import (only for BYOK).')

    with self.argument_context('keyvault key import', arg_group='Key Source') as c:
        c.argument('pem_file', type=file_type, help='PEM file containing the key to be imported.', completer=FilesCompleter(), validator=validate_key_import_source)
        c.argument('pem_string', type=file_type, help='PEM string containing the key to be imported.', validator=validate_key_import_source)
        c.argument('pem_password', help='Password of PEM file.')
        c.argument('byok_file', type=file_type, help='BYOK file containing the key to be imported. Must not be password protected.', completer=FilesCompleter(), validator=validate_key_import_source)
        c.argument('byok_string', type=file_type, help='BYOK string containing the key to be imported. Must not be password protected.', validator=validate_key_import_source)

    with self.argument_context('keyvault key download') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='File to receive the key contents.')
        c.argument('encoding', arg_type=get_enum_type(key_format_values), options_list=['--encoding', '-e'],
                   help='Encoding of the key, default: PEM', default='PEM')

    with self.argument_context('keyvault key backup') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='Local file path in which to store key backup.')

    with self.argument_context('keyvault key restore') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='Local key backup from which to restore key.')

    with self.argument_context('keyvault key restore', arg_group='Storage Id') as c:
        c.argument('storage_resource_uri', options_list=['--storage-resource-uri', '-u'],
                   help='Azure Blob storage container Uri. If specified, all '
                        'other \'Storage Id\' arguments should be omitted')
        c.argument('storage_account_name', help='Name of Azure Storage Account.')
        c.argument('blob_container_name', help='Name of Blob Container.')

    with self.argument_context('keyvault key restore', arg_group='Restoring keys from storage account') as c:
        c.argument('token', options_list=['--storage-container-SAS-token', '-t'],
                   help='The SAS token pointing to an Azure Blob storage container')
        c.argument('backup_folder', help='Name of the blob container which contains the backup')
        c.argument('name', options_list=['--name', '-n'],
                   help='Name of the key. (Only for restoring from storage account)')

    for scope in ['encrypt', 'decrypt']:
        with self.argument_context('keyvault key {}'.format(scope)) as c:
            c.argument('algorithm', options_list=['--algorithm', '-a'], arg_type=get_enum_type(EncryptionAlgorithm),
                       help='Algorithm identifier')

    with self.argument_context('keyvault key encrypt') as c:
        c.argument('value', help='The value to be encrypted. Default data type is Base64 encoded string.',
                   validator=validate_encryption)
        c.extra('data_type', help='The type of the original data.', arg_type=get_enum_type(KeyEncryptionDataType),
                default='base64')
        c.argument('iv', help='Initialization vector. Required for only AES-CBC(PAD) encryption.')
        c.argument('aad', help='Optional data that is authenticated but not encrypted. For use with AES-GCM encryption.')

    with self.argument_context('keyvault key decrypt') as c:
        c.argument('value', help='The value to be decrypted, which should be the result of "az keyvault encrypt"',
                   validator=validate_decryption)
        c.extra('data_type', help='The type of the original data.', arg_type=get_enum_type(KeyEncryptionDataType),
                default='base64')
        c.argument('iv', help='The initialization vector used during encryption. Required for AES decryption.')
        c.argument('aad', help='Optional data that is authenticated but not encrypted. For use with AES-GCM decryption.')
        c.argument('tag', help='The authentication tag generated during encryption. Required for only AES-GCM decryption.')

    for scope in ['sign', 'verify']:
        with self.argument_context('keyvault key {}'.format(scope)) as c:
            c.argument('algorithm', options_list=['--algorithm', '-a'], arg_type=get_enum_type(SignatureAlgorithm),
                       help='Algorithm identifier')
            c.argument('digest', help='The value to sign (base64 encoded)')
            c.argument('signature', help='signature to verify')

    with self.argument_context('keyvault key random') as c:
        c.extra('hsm_name', hsm_url_type, arg_group='Id', required=False)
        c.extra('identifier', options_list=['--id'], arg_group='Id',
                help='Full URI of the HSM.', validator=validate_vault_or_hsm)
        c.argument('count', type=int, help='The requested number of random bytes.')

    with self.argument_context('keyvault key set-attributes') as c:
        c.extra('enabled', help='Enable the key.', arg_type=get_three_state_flag())
        c.extra('expires_on', options_list=['--expires'], default=None, type=datetime_type,
                help='Expiration UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').')
        c.extra('not_before', default=None, type=datetime_type,
                help='Key not usable before the provided UTC datetime  (Y-m-d\'T\'H:M:S\'Z\').')
        c.extra('key_operations', arg_type=get_enum_type(JsonWebKeyOperation), options_list=['--ops'], nargs='*',
                help='Space-separated list of permitted JSON web key operations.')
        c.extra('release_policy', options_list=['--policy'], type=file_type, completer=FilesCompleter(),
                validator=process_key_release_policy, is_preview=True,
                help='The policy rules under which the key can be exported. '
                     'Policy definition as JSON, or a path to a file containing JSON policy definition.')
        c.extra('immutable', arg_type=get_three_state_flag(), is_preview=True,
                help='Mark a release policy as immutable. '
                     'An immutable release policy cannot be changed or updated after being marked immutable. '
                     'Release policies are mutable by default.')
        c.extra('tags', tags_type)

    with self.argument_context('keyvault key rotation-policy') as c:
        c.argument('key_name', options_list=['--name', '-n'], id_part='child_name_1',
                   required=False, completer=get_keyvault_name_completion_list('key'),
                   help='Name of the key. Required if --id is not specified.')

    with self.argument_context('keyvault key rotation-policy update') as c:
        c.argument('value', type=file_type, completer=FilesCompleter(),
                   help='The rotation policy file definition as JSON, or a path to a file containing JSON policy definition.')
    # endregion

    # region KeyVault shared between Secret and Certificate track2
    for item in ['secret', 'certificate']:
        for cmd in ['backup', 'decrypt', 'delete', 'download', 'encrypt', 'list-versions', 'set-attributes', 'show',
                    'list', 'list-deleted']:
            with self.argument_context('keyvault {} {}'.format(item, cmd), arg_group='Id') as c:
                try:
                    if cmd in ['list', 'list-deleted']:
                        c.extra('identifier', options_list=['--id'],
                                help='Full URI of the Vault. '
                                     'If specified all other \'Id\' arguments should be omitted.',
                                validator=validate_vault_or_hsm)
                    else:
                        c.extra('identifier', options_list=['--id'],
                                help='Id of the {}. '
                                     'If specified all other \'Id\' arguments should be omitted.'.format(item),
                                validator=validate_keyvault_resource_id(item))
                except ValueError:
                    pass
                if item == 'secret':
                    c.argument('name', options_list=['--name', '-n'], required=False,
                               help='Name of the {}. Required if --id is not specified.'.format(item))
                elif item == 'certificate':
                    c.argument('{}_name'.format(item), options_list=['--name', '-n'], required=False,
                               help='Name of the {}. Required if --id is not specified.'.format(item))
                c.extra('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None,
                        options_list=['--vault-name'], help='Name of the Key Vault. Required if --id is not specified')
                c.argument('version', options_list=['--version', '-v'],
                           help='The {} version. If omitted, uses the latest version.'.format(item), default='',
                           required=False, arg_group='Id', completer=get_keyvault_version_completion_list(item))

        for cmd in ['purge', 'recover', 'show-deleted']:
            with self.argument_context('keyvault {} {}'.format(item, cmd), arg_group='Id') as c:
                c.extra('identifier', options_list=['--id'],
                        help='The recovery id of the {}. '
                             'If specified all other \'Id\' arguments should be omitted.'.format(item),
                        validator=validate_keyvault_resource_id(item))
                if item == 'secret':
                    c.argument('name', options_list=['--name', '-n'], required=False,
                               help='Name of the {}. Required if --id is not specified.'.format(item))
                elif item == 'certificate':
                    c.argument('{}_name'.format(item), options_list=['--name', '-n'], required=False,
                               help='Name of the {}. Required if --id is not specified.'.format(item))
                c.extra('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None,
                        options_list=['--vault-name'], required=False,
                        help='Name of the Vault. Required if --id is not specified.')
                c.argument('version', required=False)

        for scope in ['list', 'list-versions', 'list-deleted']:
            with self.argument_context('keyvault {} {}'.format(item, scope)) as c:
                c.extra('max_page_size', options_list=['--maxresults'], type=int,
                        help='Maximum number of results to return in a page. '
                             'If not specified, the service will return up to 25 results.')

    with self.argument_context('keyvault secret list') as c:
        c.extra('include_managed', arg_type=get_three_state_flag(), default=False,
                help='Include managed secrets. Default: false')

    for cmd in ['set', 'set-attributes']:
        with self.argument_context('keyvault secret {}'.format(cmd)) as c:
            c.extra('content_type', options_list=['--description', '--content-type'],
                    help='Description of the secret contents (e.g. password, connection string, etc)')
            c.extra('expires_on', options_list=['--expires'], type=datetime_type,
                    help='Expiration UTC datetime (Y-m-d\'T\'H:M:S\'Z\').')
            c.extra('not_before', type=datetime_type,
                    help='Secret not usable before the provided UTC datetime (Y-m-d\'T\'H:M:S\'Z\').')
            c.extra('tags', tags_type)

    with self.argument_context('keyvault secret set') as c:
        c.argument('name', options_list=['--name', '-n'], required=True, arg_group='Id',
                   help='Name of the secret.')
        c.extra('vault_base_url', vault_name_type, required=True, arg_group='Id',
                type=get_vault_base_url_type(self.cli_ctx), id_part=None)
        c.extra('disabled', help='Create secret in disabled state.', arg_type=get_three_state_flag())

    with self.argument_context('keyvault secret set', arg_group='Content Source') as c:
        c.argument('value', options_list=['--value'],
                   help="Plain text secret value. Cannot be used with '--file' or '--encoding'", required=False)
        c.extra('file_path', options_list=['--file', '-f'], type=file_type,
                help="Source file for secret. Use in conjunction with '--encoding'", completer=FilesCompleter())
        c.extra('encoding', arg_type=get_enum_type(secret_encoding_values, default='utf-8'),
                options_list=['--encoding', '-e'],
                help='Source file encoding. The value is saved as a tag (`file-encoding=<val>`) '
                     'and used during download to automatically encode the resulting file.')

    with self.argument_context('keyvault secret set-attributes') as c:
        c.extra('content_type', options_list=['--content-type'],
                help='Type of the secret value such as a password.')
        c.extra('enabled', help='Enable the secret.', arg_type=get_three_state_flag())

    with self.argument_context('keyvault secret download') as c:
        c.argument('encoding', arg_type=get_enum_type(secret_encoding_values), options_list=['--encoding', '-e'],
                   help="Encoding of the secret. By default, will look for the 'file-encoding' tag on the secret. "
                        "Otherwise will assume 'utf-8'.", default=None)
        c.argument('overwrite', action='store_true', options_list=['--overwrite'], help="Overwrite the file if it exists.")

    for scope in ['download', 'backup', 'restore']:
        with self.argument_context('keyvault secret {}'.format(scope)) as c:
            c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                       help='File to receive the secret contents.')

    with self.argument_context('keyvault secret restore') as c:
        c.extra('vault_base_url', vault_name_type, required=True, arg_group='Id',
                type=get_vault_base_url_type(self.cli_ctx), id_part=None)
    # endregion

    # region keyvault security-domain
    for scope in ['init-recovery', 'download', 'upload', 'wait']:
        with self.argument_context('keyvault security-domain {}'.format(scope), arg_group='HSM Id') as c:
            c.extra('hsm_name', hsm_url_type, required=False,
                    help='Name of the HSM. Can be omitted if --id is specified.')
            c.extra('identifier', options_list=['--id'], validator=validate_vault_or_hsm, help='Full URI of the HSM.')
            c.ignore('vault_base_url')

    with self.argument_context('keyvault security-domain init-recovery') as c:
        c.argument('sd_exchange_key', help='Local file path to store the exported key.')

    with self.argument_context('keyvault security-domain upload') as c:
        c.argument('sd_file', help='This file contains security domain encrypted using SD Exchange file downloaded '
                                   'in security-domain init-recovery command.')
        c.argument('restore_blob', help='Indicator if blob is already restored.')
        c.argument('sd_exchange_key', help='The exchange key for security domain.')
        c.argument('sd_wrapping_keys', nargs='*',
                   help='Space-separated file paths to PEM files containing private keys.')
        c.argument('passwords', nargs='*', help='Space-separated password list for --sd-wrapping-keys. '
                                                'CLI will match them in order. Can be omitted if your keys are without '
                                                'password protection.')

    with self.argument_context('keyvault security-domain restore-blob') as c:
        c.argument('sd_file', help='This file contains security domain encrypted using SD Exchange file downloaded '
                                   'in security-domain init-recovery command.')
        c.argument('sd_exchange_key', help='The exchange key for security domain.')
        c.argument('sd_wrapping_keys', nargs='*',
                   help='Space-separated file paths to PEM files containing private keys.')
        c.argument('passwords', nargs='*', help='Space-separated password list for --sd-wrapping-keys. '
                                                'CLI will match them in order. Can be omitted if your keys are without '
                                                'password protection.')
        c.argument('sd_file_restore_blob', help='Local file path to store the security domain encrypted with the exchange key.')

    with self.argument_context('keyvault security-domain download') as c:
        c.argument('sd_wrapping_keys', nargs='*',
                   help='Space-separated file paths to PEM files containing public keys.')
        c.argument('security_domain_file',
                   help='Path to a file where the JSON blob returned by this command is stored.')
        c.argument('sd_quorum', type=int, help='The minimum number of shares required to decrypt the security domain '
                                               'for recovery.')

    with self.argument_context('keyvault security-domain wait') as c:
        c.argument('target_operation', arg_type=get_enum_type(CLISecurityDomainOperation),
                   help='Target operation that needs waiting.')
    # endregion

    # region keyvault backup/restore
    for item in ['backup', 'restore']:
        for scope in ['start']:  # TODO add 'status' when SDK is ready
            with self.argument_context('keyvault {} {}'.format(item, scope), arg_group='HSM Id') as c:
                c.argument('hsm_name', hsm_url_type, required=False,
                           help='Name of the HSM. Can be omitted if --id is specified.')
                c.extra('identifier', options_list=['--id'], validator=validate_vault_or_hsm, help='Full URI of the HSM.')
                c.ignore('cls')

    with self.argument_context('keyvault backup start', arg_group='Storage Id') as c:
        c.argument('storage_resource_uri', required=False,
                   help='Azure Blob storage container Uri. If specified all other \'Storage Id\' arguments '
                        'should be omitted')
        c.extra('storage_account_name', help='Name of Azure Storage Account.')
        c.extra('blob_container_name', help='Name of Blob Container.')

    for command_group in ['backup', 'restore']:
        with self.argument_context('keyvault {} start'.format(command_group)) as c:
            c.argument('token', options_list=['--storage-container-SAS-token', '-t'],
                       help='The SAS token pointing to an Azure Blob storage container')
            c.argument('use_managed_identity', arg_type=get_three_state_flag(),
                       help='If True, Managed HSM will use the configured user-assigned managed identity to '
                            'authenticate with Azure Storage. Otherwise, a `sas_token` has to be specified.')

    with self.argument_context('keyvault restore start') as c:
        c.argument('folder_to_restore', options_list=['--backup-folder'],
                   help='Name of the blob container which contains the backup')
        c.argument('key_name', options_list=['--key-name', '--key'],
                   help='Name of a single key in the backup. When set, only this key will be restored')

    with self.argument_context('keyvault restore start', arg_group='Storage Id') as c:
        c.extra('storage_resource_uri', required=False,
                help='Azure Blob storage container Uri. If specified all other \'Storage Id\' '
                     'arguments should be omitted')
        c.extra('storage_account_name', help='Name of Azure Storage Account.')
        c.extra('blob_container_name', help='Name of Blob Container.')

    # endregion

    # KeyVault Certificate
    with self.argument_context('keyvault certificate issuer admin') as c:
        c.argument('email', help='Admin e-mail address. Must be unique within the vault.')
        c.argument('name', help='Full admin name.')
        c.argument('phone', help='Admin phone number.')
        c.argument('first_name', help='Admin first name.')
        c.argument('last_name', help='Admin last name.')
    # endregion

    # region KeyVault Certificate track2
    with self.argument_context('keyvault certificate create') as c:
        c.argument('certificate_name', options_list=['--name', '-n'], required=True, arg_group='Id',
                   help='Name of the certificate.')
        c.extra('vault_base_url', vault_name_type, required=True, arg_group='Id',
                type=get_vault_base_url_type(self.cli_ctx), id_part=None)
        c.extra('disabled', help='Create certificate in disabled state.', arg_type=get_three_state_flag())
        c.extra('validity', type=int,
                help='Number of months the certificate is valid for. Overrides the value specified with --policy/-p')
        c.argument('policy', options_list=['--policy', '-p'],
                   help='JSON encoded policy definition. Use @{file} to load from a file(e.g. @my_policy.json).',
                   type=get_json_object, validator=process_certificate_policy)

    with self.argument_context('keyvault certificate set-attributes') as c:
        c.extra('enabled', help='Enable the certificate.', arg_type=get_three_state_flag())
        c.extra('policy', options_list=['--policy', '-p'],
                help='JSON encoded policy definition. Use @{file} to load from a file(e.g. @my_policy.json).',
                type=get_json_object, validator=process_certificate_policy)
        c.extra('tags', tags_type)

    for cmd in ['list', 'list-deleted']:
        with self.argument_context('keyvault certificate {}'.format(cmd)) as c:
            c.extra('include_pending', arg_type=get_three_state_flag(),
                    help='Specifies whether to include certificates which are not completely provisioned.')

    with self.argument_context('keyvault certificate import') as c:
        c.argument('certificate_name', options_list=['--name', '-n'], required=True, arg_group='Id',
                   help='Name of the certificate.')
        c.extra('vault_base_url', vault_name_type, required=True, arg_group='Id',
                type=get_vault_base_url_type(self.cli_ctx), id_part=None)
        c.argument('certificate_bytes', options_list=['--file', '-f'], completer=FilesCompleter(),
                   help='PKCS12 file or PEM file containing the certificate and private key.',
                   type=certificate_type)
        c.extra('password', help="If the private key in certificate is encrypted, the password used for encryption.")
        c.extra('disabled', arg_type=get_three_state_flag(), help='Import the certificate in disabled state.',
                validator=process_certificate_import)
        c.extra('policy', options_list=['--policy', '-p'],
                help='JSON encoded policy definition. Use @{file} to load from a file(e.g. @my_policy.json).',
                type=get_json_object, validator=process_certificate_policy)
        c.extra('tags', tags_type)

    with self.argument_context('keyvault certificate backup') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='Local file path in which to store certificate backup.')

    with self.argument_context('keyvault certificate restore') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='Local certificate backup from which to restore certificate.')
        c.extra('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None,
                options_list=['--vault-name'], arg_group='Id', help='Name of the Key Vault.')

    with self.argument_context('keyvault certificate download') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='File to receive the binary certificate contents.')
        c.argument('encoding', arg_type=get_enum_type(certificate_format_values), options_list=['--encoding', '-e'],
                   help='Encoding of the certificate. DER will create a binary DER formatted x509 certificate, '
                        'and PEM will create a base64 PEM x509 certificate.')

    # TODO: Fix once service side issue is fixed that there is no way to list pending certificates
    with self.argument_context('keyvault certificate pending') as c:
        c.argument('certificate_name', options_list=['--name', '-n'], arg_group='Id',
                   help='Name of the pending certificate.',
                   id_part='child_name_1', completer=None)

    for item in ['merge', 'show', 'delete']:
        with self.argument_context('keyvault certificate pending {}'.format(item)) as c:
            c.extra('vault_base_url', vault_name_type, required=True, arg_group='Id',
                    type=get_vault_base_url_type(self.cli_ctx), id_part=None)

    with self.argument_context('keyvault certificate pending merge') as c:
        c.argument('x509_certificates', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='File containing the certificate or certificate chain to merge.',
                   validator=validate_x509_certificate_chain)
        c.extra('disabled', arg_type=get_three_state_flag(), help='Create certificate in disabled state.',
                validator=process_certificate_import)
        c.extra('tags', tags_type)

    with self.argument_context('keyvault certificate contact') as c:
        c.argument('email', help='Contact e-mail address. Must be unique.')
        c.argument('name', help='Full contact name.')
        c.argument('phone', help='Contact phone number.')

    for item in ['list', 'add', 'delete']:
        with self.argument_context('keyvault certificate contact {}'.format(item)) as c:
            c.extra('vault_base_url', vault_name_type, required=True, arg_group='Id',
                    type=get_vault_base_url_type(self.cli_ctx), id_part=None)

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

    for item in ['create', 'show', 'list', 'delete', 'update']:
        with self.argument_context('keyvault certificate issuer {}'.format(item)) as c:
            c.extra('vault_base_url', vault_name_type, required=True, arg_group='Id',
                    type=get_vault_base_url_type(self.cli_ctx), id_part=None)

    for item in ['add', 'list', 'delete']:
        with self.argument_context('keyvault certificate issuer admin {}'.format(item)) as c:
            c.extra('vault_base_url', vault_name_type, required=True, arg_group='Id',
                    type=get_vault_base_url_type(self.cli_ctx), id_part=None)
    # endregion

    # region KeyVault Role
    with self.argument_context('keyvault role') as c:
        c.argument('scope',
                   help='scope at which the role assignment or definition applies to, '
                        'e.g., "/" or "/keys" or "/keys/{keyname}"')

    with self.argument_context('keyvault role', arg_group='Id') as c:
        c.argument('hsm_name', hsm_url_type)
        c.argument('identifier', options_list=['--id'],
                   help='Full URI of the HSM. If specified all other \'Id\' arguments should be omitted.',
                   validator=process_hsm_name)

    with self.argument_context('keyvault role assignment') as c:
        c.argument('role_assignment_name', options_list=['--name', '-n'], help='Name of the role assignment.')
        c.argument('assignee', help='represent a user, group, or service principal. '
                                    'supported format: object id, user sign-in name, or service principal name')
        c.argument('assignee_object_id',
                   help='Use this parameter instead of \'--assignee\' to bypass graph permission issues. '
                        'This parameter only works with object ids for users, groups, service principals, and '
                        'managed identities. For managed identities use the principal id. For service principals, '
                        'use the object id and not the app id.')
        c.argument('ids', nargs='+', help='space-separated role assignment ids')
        c.argument('role', help='role name or id')

    with self.argument_context('keyvault role definition') as c:
        c.argument('hsm_name', hsm_url_type)
        c.argument('role_definition', help='Description of a role as JSON, or a path to a file containing a JSON description.')
        c.argument('role_id', help='The role definition ID.')
        c.argument('role_definition_name', options_list=['--name', '-n'], help='The role definition name. '
                   'This is a GUID in the "name" property of a role definition.')

    with self.argument_context('keyvault role definition list') as c:
        c.argument('custom_role_only', arg_type=get_three_state_flag(), help='Only show custom role definitions.')

    class PrincipalType(str, Enum):  # Copied from azure.mgmt.authorization v2018_09_01_preview
        user = "User"
        group = "Group"
        service_principal = "ServicePrincipal"
        unknown = "Unknown"
        directory_role_template = "DirectoryRoleTemplate"
        foreign_group = "ForeignGroup"
        application = "Application"
        msi = "MSI"
        directory_object_or_group = "DirectoryObjectOrGroup"
        everyone = "Everyone"

    with self.argument_context('keyvault role assignment create') as c:
        c.argument('assignee_principal_type', options_list=['--assignee-principal-type', '-t'],
                   arg_type=get_enum_type(PrincipalType), help='The principal type of assignee.')
    # endregion

    with self.argument_context('keyvault region') as c:
        c.argument('name', hsm_name_type)
        c.argument('region_name', options_list=['--region-name', '--region', '-r'],
                   help='The region name.')

    for item in ['list', 'show', 'update']:
        with self.argument_context(f'keyvault setting {item}', arg_group='Id') as c:
            c.extra('hsm_name', hsm_url_type)
            c.extra('identifier', options_list=['--id'],
                    help='Full URI of the HSM. If specified all other \'Id\' arguments should be omitted.',
                    validator=process_hsm_name)

    with self.argument_context('keyvault setting') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the setting.')
        c.argument('value', help='Value of the setting.')
        c.argument('setting_type', options_list=['--setting-type', '--type'],
                   arg_type=get_enum_type(['boolean', 'string']), help='Type of the setting value.')
