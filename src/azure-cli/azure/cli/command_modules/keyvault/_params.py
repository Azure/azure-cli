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
    datetime_type, certificate_type,
    get_vault_base_url_type, get_hsm_base_url_type, validate_key_import_type,
    validate_key_import_source, validate_key_type, validate_policy_permissions, validate_principal,
    validate_resource_group_name, validate_x509_certificate_chain,
    secret_text_encoding_values, secret_binary_encoding_values, validate_subnet, validate_ip_address,
    validate_vault_or_hsm, validate_key_id, validate_sas_definition_id, validate_storage_account_id,
    validate_storage_disabled_attribute, validate_deleted_vault_or_hsm_name, validate_encryption, validate_decryption,
    validate_vault_name_and_hsm_name, set_vault_base_url, validate_keyvault_resource_id,
    process_hsm_name, KeyEncryptionDataType, process_key_release_policy)

# CUSTOM CHOICE LISTS

secret_encoding_values = secret_text_encoding_values + secret_binary_encoding_values
key_format_values = certificate_format_values = ['PEM', 'DER']


# pylint: disable=too-many-locals, too-many-branches, too-many-statements, line-too-long
def load_arguments(self, _):
    (JsonWebKeyOperation, JsonWebKeyType, SasTokenType,
     SasDefinitionAttributes, SecretAttributes, CertificateAttributes, StorageAccountAttributes) = self.get_models(
         'JsonWebKeyOperation', 'JsonWebKeyType', 'SasTokenType',
         'SasDefinitionAttributes', 'SecretAttributes', 'CertificateAttributes', 'StorageAccountAttributes',
         resource_type=ResourceType.DATA_KEYVAULT)

    KeyCurveName = self.get_sdk('KeyCurveName', resource_type=ResourceType.DATA_KEYVAULT_KEYS, mod='_enums')
    EncryptionAlgorithm = self.get_sdk('EncryptionAlgorithm', resource_type=ResourceType.DATA_KEYVAULT_KEYS, mod='crypto._enums')

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

    class CLIJsonWebKeyType(str, Enum):
        ec = "EC"  #: Elliptic Curve.
        ec_hsm = "EC-HSM"  #: Elliptic Curve with a private key which is not exportable from the HSM.
        rsa = "RSA"  #: RSA (https://tools.ietf.org/html/rfc3447)
        rsa_hsm = "RSA-HSM"  #: RSA with a private key which is not exportable from the HSM.
        oct = "oct"  #: Octet sequence (used to represent symmetric keys)
        oct_hsm = "oct-HSM"  #: Oct with a private key which is not exportable from the HSM.

    JsonWebKeyType = CLIJsonWebKeyType  # TODO: Remove this patch when new SDK is released

    class CLIKeyTypeForBYOKImport(str, Enum):
        ec = "EC"  #: Elliptic Curve.
        rsa = "RSA"  #: RSA (https://tools.ietf.org/html/rfc3447)
        oct = "oct"  #: Octet sequence (used to represent symmetric keys)

    class CLISecurityDomainOperation(str, Enum):
        download = "download"  #: Download operation
        upload = "upload"  #: Upload operation

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
                   help='Proceed only if Key Vault belongs to the specified resource group.',
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
        c.argument('enable_rbac_authorization', arg_type=get_three_state_flag())
        c.argument('enable_soft_delete', arg_type=get_three_state_flag(), deprecate_info=c.deprecate(
            message_func=lambda x: 'Warning! The ability to create new key vaults with soft delete disabled will be '
                                   'deprecated by December 2020. All key vaults will be required to have soft delete '
                                   'enabled. Please see the following documentation for additional guidance.\n'
                                   'https://docs.microsoft.com/azure/key-vault/general/soft-delete-change'),
                   help='[Vault Only] Property to specify whether the \'soft delete\' functionality is enabled for '
                        'this key vault. If it\'s not set to any value (true or false) when creating new key vault, it '
                        'will be set to true by default. Once set to true, it cannot be reverted to false.')
        c.argument('enable_purge_protection', arg_type=get_three_state_flag())
        c.argument('public_network_access', arg_type=get_enum_type(PublicNetworkAccess),
                   help="Property to specify whether the vault will accept traffic from public internet. If set to "
                        "'disabled' all traffic except private endpoint traffic and that originates from trusted "
                        "services will be blocked. This will override the set firewall rules, meaning that even if the "
                        "firewall rules are present we will not honor the rules.")

    with self.argument_context('keyvault', arg_group='Network Rule', min_api='2018-02-14') as c:
        c.argument('bypass', arg_type=get_enum_type(NetworkRuleBypassOptions),
                   help='Bypass traffic for space-separated uses.')
        c.argument('default_action', arg_type=get_enum_type(NetworkRuleAction),
                   help='Default action to apply when no rule matches.')

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
                               ' Allowed values for HSM: Standard_B1, Custom_B32. Default: Standard_B1')
        c.argument('no_self_perms', arg_type=get_three_state_flag(),
                   help='[Vault Only] Don\'t add permissions for the current user/service principal in the new vault.')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('retention_days', help='Soft delete data retention days. It accepts >=7 and <=90.', default='90')

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

    with self.argument_context('keyvault update-hsm') as c:
        c.argument('name', hsm_name_type)
        c.argument('enable_purge_protection', options_list=['--enable-purge-protection', '-e'])
        c.argument('secondary_locations', nargs='+',
                   help='--secondary-locations extends/contracts an HSM pool to listed regions. The primary location '
                        'where the resource was originally created CANNOT be removed.')

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

    with self.argument_context('keyvault network-rule', min_api='2018-02-14') as c:
        c.argument('ip_address', help='IPv4 address or CIDR range.')
        c.argument('subnet', help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
        c.argument('vnet_name', help='Name of a virtual network.', validator=validate_subnet)

    with self.argument_context('keyvault network-rule add', min_api='2018-02-14') as c:
        c.argument('ip_address', nargs='*', help='IPv4 address or CIDR range. Can supply a list: --ip-address ip1 [ip2]...', validator=validate_ip_address)

    for item in ['approve', 'reject', 'delete', 'show', 'wait']:
        with self.argument_context('keyvault private-endpoint-connection {}'.format(item), min_api='2018-02-14') as c:
            c.extra('connection_id', options_list=['--id'], required=False,
                    help='The ID of the private endpoint connection associated with the Key Vault/HSM. '
                         'If specified --vault-name/--hsm-name and --name/-n, this should be omitted.')
            c.argument('description', help='Comments for the {} operation.'.format(item))
            c.argument('private_endpoint_connection_name', options_list=['--name', '-n'], required=False,
                       help='The name of the private endpoint connection associated with the Key Vault/HSM. '
                            'Required if --id is not specified')
            c.argument('vault_name', vault_name_type, required=False,
                       help='Name of the Key Vault. Required if --id is not specified')
            c.argument('hsm_name', mgmt_plane_hsm_name_type, min_api='2021-04-01-preview',
                       help='Name of the HSM. Required if --id is not specified.'
                            '(--hsm-name and --vault-name are mutually exclusive, please specify just one of them)')

    with self.argument_context('keyvault private-endpoint-connection list') as c:
        c.argument("hsm_name", hsm_name_type)

    with self.argument_context('keyvault private-link-resource', min_api='2018-02-14', max_api='2020-04-01-preview') as c:
        c.argument('vault_name', vault_name_type, required=True)
    with self.argument_context('keyvault private-link-resource', min_api='2021-04-01-preview') as c:
        c.argument('vault_name', vault_name_type)
        c.argument('hsm_name', mgmt_plane_hsm_name_type)
    # endregion

    # region Shared
    for item in ['secret', 'certificate']:
        with self.argument_context('keyvault ' + item, arg_group='Id') as c:
            c.argument(item + '_name', options_list=['--name', '-n'], help='Name of the {}.'.format(item),
                       id_part='child_name_1', completer=get_keyvault_name_completion_list(item))
            c.argument('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None)
            c.argument(item + '_version', options_list=['--version', '-v'],
                       help='The {} version. If omitted, uses the latest version.'.format(item), default='',
                       required=False, completer=get_keyvault_version_completion_list(item))

        for cmd in ['backup', 'decrypt', 'delete', 'download', 'encrypt', 'list-versions', 'set-attributes', 'show',
                    'list']:
            with self.argument_context('keyvault {} {}'.format(item, cmd), arg_group='Id') as c:
                try:
                    if cmd in ['list']:
                        c.extra('identifier', options_list=['--id'],
                                help='Full URI of the Vault or HSM. '
                                     'If specified all other \'Id\' arguments should be omitted.',
                                validator=validate_vault_or_hsm)
                    else:
                        c.extra('identifier', options_list=['--id'],
                                help='Id of the {}. '
                                     'If specified all other \'Id\' arguments should be omitted.'.format(item),
                                validator=validate_key_id(item))
                except ValueError:
                    pass
                c.argument(item + '_name', help='Name of the {}. Required if --id is not specified.'.format(item),
                           required=False)
                c.argument('vault_base_url', vault_name_type, required=False,
                           help='Name of the Key Vault. Required if --id is not specified.')
                c.argument(item + '_version', required=False)

        for cmd in ['purge', 'recover', 'show-deleted']:
            with self.argument_context('keyvault {} {}'.format(item, cmd), arg_group='Id') as c:
                c.extra('identifier', options_list=['--id'],
                        help='The recovery id of the {}. '
                             'If specified all other \'Id\' arguments should be omitted.'.format(item),
                        validator=validate_key_id('deleted' + item))
                c.argument(item + '_name', help='Name of the {}. Required if --id is not specified.'.format(item),
                           required=False)
                c.argument('vault_base_url', help='Name of the Vault. Required if --id is not specified.',
                           required=False)
                c.argument(item + '_version', required=False)

        for cmd in ['list', 'list-deleted']:
            with self.argument_context('keyvault {} {}'.format(item, cmd)) as c:
                c.argument('include_pending', arg_type=get_three_state_flag())

            with self.argument_context('keyvault {} {}'.format(item, cmd), arg_group='Id') as c:
                if cmd in ['list-deleted']:
                    c.extra('identifier', options_list=['--id'],
                            help='Full URI of the Vault{}. '
                                 'If specified all other \'Id\' arguments should be '
                                 'omitted.'.format(' or HSM' if item == 'key' else ''),
                            validator=validate_vault_or_hsm)
    # endregion

    # region keys
    # keys track1
    with self.argument_context('keyvault key') as c:
        c.argument('key_ops', arg_type=get_enum_type(JsonWebKeyOperation), options_list=['--ops'], nargs='*',
                   help='Space-separated list of permitted JSON web key operations.')

    for item in ['delete', 'list', 'list-deleted', 'list-versions', 'purge', 'recover', 'show-deleted']:
        with self.argument_context('keyvault key {}'.format(item), arg_group='Id') as c:
            c.ignore('cls')
            c.argument('key_name', options_list=['--name', '-n'], required=False, id_part='child_name_1',
                       completer=get_keyvault_name_completion_list('key'),
                       help='Name of the key. Required if --id is not specified.')
            c.argument('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx),
                       id_part=None, required=False)
            c.argument('key_version', options_list=['--version', '-v'],
                       help='The key version. If omitted, uses the latest version.', default='',
                       required=False, completer=get_keyvault_version_completion_list('key'))
            c.extra('identifier', options_list=['--id'], validator=validate_key_id('key'),
                    help='Id of the key. If specified all other \'Id\' arguments should be omitted.')
            c.extra('hsm_name', data_plane_hsm_name_type)

            if item in ['list', 'list-deleted']:
                c.extra('identifier', options_list=['--id'], validator=validate_vault_or_hsm,
                        help='Full URI of the Vault or HSM. If specified all other \'Id\' arguments should be omitted.')
            elif item in ['show-deleted', 'purge', 'recover']:
                c.extra('identifier', options_list=['--id'], validator=validate_key_id('deletedkey'),
                        help='The recovery id of the key. If specified all other \'Id\' arguments should be omitted.')

    for item in ['backup', 'download']:
        with self.argument_context('keyvault key {}'.format(item), arg_group='Id') as c:
            c.argument('key_name', options_list=['--name', '-n'],
                       help='Name of the key. Required if --id is not specified.',
                       required=False, id_part='child_name_1', completer=get_keyvault_name_completion_list('key'))
            c.argument('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None)
            c.argument('key_version', options_list=['--version', '-v'],
                       help='The key version. If omitted, uses the latest version.', default='',
                       required=False, completer=get_keyvault_version_completion_list('key'))
            c.argument('identifier', options_list=['--id'], validator=validate_key_id('key'),
                       help='Id of the key. If specified all other \'Id\' arguments should be omitted.')
            c.argument('hsm_name', data_plane_hsm_name_type)

    with self.argument_context('keyvault key backup') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='Local file path in which to store key backup.')

    with self.argument_context('keyvault key download') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='File to receive the key contents.')
        c.argument('encoding', arg_type=get_enum_type(key_format_values), options_list=['--encoding', '-e'],
                   help='Encoding of the key, default: PEM', default='PEM')

    with self.argument_context('keyvault key restore', arg_group='Id') as c:
        c.argument('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None)
        c.argument('identifier', options_list=['--id'], validator=validate_vault_or_hsm,
                   help='Full URI of the Vault or HSM. If specified all other \'Id\' arguments should be omitted.')
        c.argument('hsm_name', data_plane_hsm_name_type, validator=None)

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
        c.argument('key_name', options_list=['--name', '-n'],
                   help='Name of the key. (Only for restoring from storage account)')

    for scope in ['list', 'list-deleted', 'list-versions']:
        with self.argument_context('keyvault key {}'.format(scope)) as c:
            c.argument('maxresults', options_list=['--maxresults'], type=int)

    with self.argument_context('keyvault key list') as c:
        c.extra('include_managed', arg_type=get_three_state_flag(), default=False,
                help='Include managed keys. Default: false')

    # keys track2
    for scope in ['create', 'import', 'set-attributes', 'show', 'encrypt', 'decrypt',
                  'rotate', 'rotation-policy show', 'rotation-policy update']:
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
            c.argument('exportable', arg_type=get_three_state_flag(), is_preview=True,
                       help='Whether the private key can be exported. To create key with release policy, '
                            '"exportable" must be true and caller must have "export" permission.')
            c.argument('release_policy', options_list=['--policy'], type=file_type, completer=FilesCompleter(),
                       validator=process_key_release_policy, is_preview=True,
                       help='The policy rules under which the key can be exported. '
                            'Policy definition as JSON, or a path to a file containing JSON policy definition.')
            c.extra('immutable', arg_type=get_three_state_flag(), is_preview=True,
                    help='Mark a release policy as immutable. '
                         'An immutable release policy cannot be changed or updated after being marked immutable. '
                         'Release policies are mutable by default.')

    with self.argument_context('keyvault key create') as c:
        c.argument('kty', arg_type=get_enum_type(JsonWebKeyType), validator=validate_key_type,
                   help='The type of key to create. For valid values, see: https://docs.microsoft.com/rest/api/keyvault/createkey/createkey#jsonwebkeytype')
        c.argument('curve', arg_type=get_enum_type(KeyCurveName),
                   help='Elliptic curve name. For valid values, see: https://docs.microsoft.com/rest/api/keyvault/createkey/createkey#jsonwebkeycurvename')

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

    with self.argument_context('keyvault key rotation-policy update') as c:
        c.argument('value', type=file_type, completer=FilesCompleter(),
                   help='The rotation policy file definition as JSON, or a path to a file containing JSON policy definition.')
    # endregion

    # region KeyVault Secret
    with self.argument_context('keyvault secret set') as c:
        c.argument('content_type', options_list=['--description'],
                   help='Description of the secret contents (e.g. password, connection string, etc)')
        c.attributes_argument('secret', SecretAttributes, create=True)

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
        c.attributes_argument('secret', SecretAttributes)

    with self.argument_context('keyvault secret download') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='File to receive the secret contents.')
        c.argument('encoding', arg_type=get_enum_type(secret_encoding_values), options_list=['--encoding', '-e'],
                   help="Encoding of the secret. By default, will look for the 'file-encoding' tag on the secret. "
                        "Otherwise will assume 'utf-8'.", default=None)

    for scope in ['backup', 'restore']:
        with self.argument_context('keyvault secret {}'.format(scope)) as c:
            c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                       help='File to receive the secret contents.')

    for scope in ['list', 'list-deleted', 'list-versions']:
        with self.argument_context('keyvault secret {}'.format(scope)) as c:
            c.argument('maxresults', options_list=['--maxresults'], type=int)

    with self.argument_context('keyvault secret list') as c:
        c.extra('include_managed', arg_type=get_three_state_flag(), default=False,
                help='Include managed secrets. Default: false')
    # endregion

    # region keyvault security-domain
    for scope in ['init-recovery', 'download', 'upload']:
        with self.argument_context('keyvault security-domain {}'.format(scope), arg_group='HSM Id') as c:
            c.argument('hsm_name', hsm_url_type, required=False,
                       help='Name of the HSM. Can be omitted if --id is specified.')
            c.extra('identifier', options_list=['--id'], validator=validate_vault_or_hsm, help='Full URI of the HSM.')
            c.ignore('vault_base_url')

    with self.argument_context('keyvault security-domain init-recovery') as c:
        c.argument('sd_exchange_key', help='Local file path to store the exported key.')

    with self.argument_context('keyvault security-domain upload') as c:
        c.argument('sd_file', help='This file contains security domain encrypted using SD Exchange file downloaded '
                                   'in security-domain init-recovery command.')
        c.argument('sd_exchange_key', help='The exchange key for security domain.')
        c.argument('sd_wrapping_keys', nargs='*',
                   help='Space-separated file paths to PEM files containing private keys.')
        c.argument('passwords', nargs='*', help='Space-separated password list for --sd-wrapping-keys. '
                                                'CLI will match them in order. Can be omitted if your keys are without '
                                                'password protection.')

    with self.argument_context('keyvault security-domain download') as c:
        c.argument('sd_wrapping_keys', nargs='*',
                   help='Space-separated file paths to PEM files containing public keys.')
        c.argument('security_domain_file',
                   help='Path to a file where the JSON blob returned by this command is stored.')
        c.argument('sd_quorum', type=int, help='The minimum number of shares required to decrypt the security domain '
                                               'for recovery.')

    with self.argument_context('keyvault security-domain wait') as c:
        c.argument('hsm_name', hsm_url_type, help='Name of the HSM. Can be omitted if --id is specified.',
                   required=False)
        c.argument('identifier', options_list=['--id'], validator=validate_vault_or_hsm, help='Full URI of the HSM.')
        c.argument('resource_group_name', options_list=['--resource-group', '-g'],
                   help='Proceed only if HSM belongs to the specified resource group.')
        c.argument('target_operation', arg_type=get_enum_type(CLISecurityDomainOperation),
                   help='Target operation that needs waiting.')
        c.ignore('vault_base_url')
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
            c.argument('token', options_list=['--storage-container-SAS-token', '-t'], required=True,
                       help='The SAS token pointing to an Azure Blob storage container')

    with self.argument_context('keyvault restore start') as c:
        c.argument('folder_to_restore', options_list=['--backup-folder'],
                   help='Name of the blob container which contains the backup')

    with self.argument_context('keyvault restore start', arg_group='Storage Id') as c:
        c.extra('storage_resource_uri', required=False,
                help='Azure Blob storage container Uri. If specified all other \'Storage Id\' '
                     'arguments should be omitted')
        c.extra('storage_account_name', help='Name of Azure Storage Account.')
        c.extra('blob_container_name', help='Name of Blob Container.')

    # endregion

    # region KeyVault Storage Account
    with self.argument_context('keyvault storage', arg_group='Id') as c:
        c.argument('storage_account_name', options_list=['--name', '-n'],
                   help='Name to identify the storage account in the vault.', id_part='child_name_1',
                   completer=get_keyvault_name_completion_list('storage_account'))
        c.argument('vault_base_url', vault_name_type, type=get_vault_base_url_type(self.cli_ctx), id_part=None)

    for scope in ['keyvault storage add', 'keyvault storage update']:
        with self.argument_context(scope) as c:
            c.extra('disabled', arg_type=get_three_state_flag(), help='Add the storage account in a disabled state.',
                    validator=validate_storage_disabled_attribute(
                        'storage_account_attributes', StorageAccountAttributes))
            c.ignore('storage_account_attributes')
            c.argument('auto_regenerate_key', arg_type=get_three_state_flag(), required=False)
            c.argument('regeneration_period', help='The key regeneration time duration specified in ISO-8601 format, '
                                                   'such as "P30D" for rotation every 30 days.')
    for scope in ['backup', 'show', 'update', 'remove', 'regenerate-key']:
        with self.argument_context('keyvault storage ' + scope, arg_group='Id') as c:
            c.extra('identifier', options_list=['--id'],
                    help='Id of the storage account.  If specified all other \'Id\' arguments should be omitted.',
                    validator=validate_storage_account_id)
            c.argument('storage_account_name', required=False,
                       help='Name to identify the storage account in the vault. Required if --id is not specified.')
            c.argument('vault_base_url', help='Name of the Key Vault. Required if --id is not specified.',
                       required=False)

    with self.argument_context('keyvault storage backup') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='Local file path in which to store storage account backup.')

    with self.argument_context('keyvault storage restore') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='Local key backup from which to restore storage account.')

    with self.argument_context('keyvault storage sas-definition', arg_group='Id') as c:
        c.argument('storage_account_name', options_list=['--account-name'],
                   help='Name to identify the storage account in the vault.', id_part='child_name_1',
                   completer=get_keyvault_name_completion_list('storage_account'))
        c.argument('sas_definition_name', options_list=['--name', '-n'],
                   help='Name to identify the SAS definition in the vault.', id_part='child_name_2')

    for scope in ['keyvault storage sas-definition create', 'keyvault storage sas-definition update']:
        with self.argument_context(scope) as c:
            c.extra('disabled', arg_type=get_three_state_flag(), help='Add the storage account in a disabled state.',
                    validator=validate_storage_disabled_attribute('sas_definition_attributes', SasDefinitionAttributes))
            c.ignore('sas_definition_attributes')
            c.argument('sas_type', arg_type=get_enum_type(SasTokenType))
            c.argument('template_uri',
                       help='The SAS definition token template signed with the key 00000000. '
                            'In the case of an account token this is only the sas token itself, for service tokens, '
                            'the full service endpoint url along with the sas token.  Tokens created according to the '
                            'SAS definition will have the same properties as the template.')
            c.argument('validity_period',
                       help='The validity period of SAS tokens created according to the SAS definition in ISO-8601, '
                            'such as "PT12H" for 12 hour tokens.')
            c.argument('auto_regenerate_key', arg_type=get_three_state_flag())

    for scope in ['keyvault storage sas-definition delete', 'keyvault storage sas-definition show',
                  'keyvault storage sas-definition update']:
        with self.argument_context(scope, arg_group='Id') as c:
            c.extra('identifier', options_list=['--id'],
                    help='Id of the SAS definition. If specified all other \'Id\' arguments should be omitted.',
                    validator=validate_sas_definition_id)
            c.argument('storage_account_name', required=False,
                       help='Name to identify the storage account in the vault. Required if --id is not specified.')
            c.argument('sas_definition_name', required=False,
                       help='Name to identify the SAS definition in the vault. Required if --id is not specified.')
            c.argument('vault_base_url', help='Name of the Key Vault. Required if --id is not specified.',
                       required=False)
    # endregion

    # KeyVault Certificate
    with self.argument_context('keyvault certificate') as c:
        c.argument('validity', type=int,
                   help='Number of months the certificate is valid for. Overrides the value specified with --policy/-p')

    # TODO: Remove workaround when https://github.com/Azure/azure-rest-api-specs/issues/1153 is fixed
    with self.argument_context('keyvault certificate create') as c:
        c.attributes_argument('certificate', CertificateAttributes, True, ignore=['expires', 'not_before'])

    with self.argument_context('keyvault certificate set-attributes') as c:
        c.attributes_argument('certificate', CertificateAttributes, ignore=['expires', 'not_before'])

    with self.argument_context('keyvault certificate backup') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='Local file path in which to store certificate backup.')

    with self.argument_context('keyvault certificate restore') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='Local certificate backup from which to restore certificate.')

    for item in ['create', 'set-attributes', 'import']:
        with self.argument_context('keyvault certificate ' + item) as c:
            c.argument('certificate_policy', options_list=['--policy', '-p'],
                       help='JSON encoded policy definition. Use @{file} to load from a file(e.g. @my_policy.json).',
                       type=get_json_object)

    with self.argument_context('keyvault certificate import') as c:
        c.argument('certificate_data', options_list=['--file', '-f'], completer=FilesCompleter(),
                   help='PKCS12 file or PEM file containing the certificate and private key.',
                   type=certificate_type)
        c.argument('password', help="If the private key in certificate is encrypted, the password used for encryption.")
        c.extra('disabled', arg_type=get_three_state_flag(), help='Import the certificate in disabled state.')

    with self.argument_context('keyvault certificate download') as c:
        c.argument('file_path', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='File to receive the binary certificate contents.')
        c.argument('encoding', arg_type=get_enum_type(certificate_format_values), options_list=['--encoding', '-e'],
                   help='Encoding of the certificate. DER will create a binary DER formatted x509 certificate, '
                        'and PEM will create a base64 PEM x509 certificate.')

    # TODO: Fix once service side issue is fixed that there is no way to list pending certificates
    with self.argument_context('keyvault certificate pending') as c:
        c.argument('certificate_name', options_list=['--name', '-n'], help='Name of the pending certificate.',
                   id_part='child_name_1', completer=None)

    with self.argument_context('keyvault certificate pending merge') as c:
        c.argument('x509_certificates', options_list=['--file', '-f'], type=file_type, completer=FilesCompleter(),
                   help='File containing the certificate or certificate chain to merge.',
                   validator=validate_x509_certificate_chain)
        c.attributes_argument('certificate', CertificateAttributes, True)

    with self.argument_context('keyvault certificate pending cancel') as c:
        c.ignore('cancellation_requested')

    with self.argument_context('keyvault certificate contact') as c:
        c.argument('contact_email', options_list=['--email'], help='Contact e-mail address. Must be unique.')
        c.argument('contact_name', options_list=['--name'], help='Full contact name.')
        c.argument('contact_phone', options_list=['--phone'], help='Contact phone number.')

    with self.argument_context('keyvault certificate issuer admin') as c:
        c.argument('email', help='Admin e-mail address. Must be unique within the vault.')
        c.argument('name', help='Full admin name.')
        c.argument('phone', help='Admin phone number.')
        c.argument('first_name', help='Admin first name.')
        c.argument('last_name', help='Admin last name.')

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

    for item in ['list', 'list-deleted', 'list-versions']:
        with self.argument_context('keyvault certificate {}'.format(item)) as c:
            c.argument('maxresults', options_list=['--maxresults'], type=int)

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
