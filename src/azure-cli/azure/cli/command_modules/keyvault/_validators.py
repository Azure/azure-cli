# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import base64
import binascii
from datetime import datetime
import re
import sys
from ipaddress import ip_network

from enum import Enum
from knack.deprecation import Deprecated
from knack.util import CLIError

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import validate_tags
from azure.cli.core.azclierror import RequiredArgumentMissingError, InvalidArgumentValueError
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import get_file_json, shell_safe_json_parse


secret_text_encoding_values = ['utf-8', 'utf-16le', 'utf-16be', 'ascii']
secret_binary_encoding_values = ['base64', 'hex']


class KeyEncryptionDataType(str, Enum):
    BASE64 = 'base64'
    PLAINTEXT = 'plaintext'


def _extract_version(item_id):
    return item_id.split('/')[-1]


def _get_resource_group_from_resource_name(cli_ctx, vault_name, hsm_name=None):
    """
    Fetch resource group from vault name
    :param str vault_name: name of the key vault
    :param str hsm_name: name of the managed hsm
    :return: resource group name or None
    :rtype: str
    """
    from msrestazure.tools import parse_resource_id

    if vault_name:
        client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT).vaults
        for vault in client.list():
            id_comps = parse_resource_id(vault.id)
            if id_comps.get('name', None) and id_comps['name'].lower() == vault_name.lower():
                return id_comps['resource_group']

    if hsm_name:
        client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT).managed_hsms
        try:
            for hsm in client.list_by_subscription():
                id_comps = parse_resource_id(hsm.id)
                if id_comps.get('name', None) and id_comps['name'].lower() == hsm_name.lower():
                    return id_comps['resource_group']
        except:  # pylint: disable=bare-except
            return None

    return None


# COMMAND NAMESPACE VALIDATORS


def process_certificate_cancel_namespace(namespace):
    namespace.cancellation_requested = True


def process_secret_set_namespace(cmd, namespace):
    validate_tags(namespace)

    content = namespace.value
    file_path = namespace.file_path
    encoding = namespace.encoding
    tags = namespace.tags or {}

    use_error = CLIError("incorrect usage: [Required] --value VALUE | --file PATH")

    if (content and file_path) or (not content and not file_path):
        raise use_error

    SecretAttributes = cmd.get_models('SecretAttributes', resource_type=ResourceType.DATA_KEYVAULT)
    namespace.secret_attributes = SecretAttributes()
    if namespace.expires:
        namespace.secret_attributes.expires = namespace.expires
    if namespace.disabled:
        namespace.secret_attributes.enabled = not namespace.disabled
    if namespace.not_before:
        namespace.secret_attributes.not_before = namespace.not_before

    encoding = encoding or 'utf-8'
    if file_path:
        if encoding in secret_text_encoding_values:
            with open(file_path, 'r') as f:
                try:
                    content = f.read()
                except UnicodeDecodeError:
                    raise CLIError("Unable to decode file '{}' with '{}' encoding.".format(
                        file_path, encoding))
                encoded_str = content
                encoded = content.encode(encoding)
                decoded = encoded.decode(encoding)
        elif encoding == 'base64':
            with open(file_path, 'rb') as f:
                content = f.read()
                try:
                    encoded = base64.encodebytes(content)
                except AttributeError:
                    encoded = base64.encodestring(content)  # pylint: disable=deprecated-method
                encoded_str = encoded.decode('utf-8')
                decoded = base64.b64decode(encoded_str)
        elif encoding == 'hex':
            with open(file_path, 'rb') as f:
                content = f.read()
                encoded = binascii.b2a_hex(content)
                encoded_str = encoded.decode('utf-8')
                decoded = binascii.unhexlify(encoded_str)

        if content != decoded:
            raise CLIError("invalid encoding '{}'".format(encoding))

        content = encoded_str

    tags.update({'file-encoding': encoding})
    namespace.tags = tags
    namespace.value = content


def process_sas_token_parameter(cmd, ns):
    SASTokenParameter = cmd.get_models('SASTokenParameter', resource_type=ResourceType.DATA_KEYVAULT)
    return SASTokenParameter(storage_resource_uri=ns.storage_resource_uri, token=ns.token)


def process_hsm_name(ns):
    if not ns.identifier and not ns.hsm_name:
        raise CLIError('Please specify --hsm-name or --id.')
    if ns.identifier:
        ns.hsm_name = ns.identifier


def validate_vault_name_and_hsm_name(ns):
    vault_name = getattr(ns, 'vault_name', None)
    hsm_name = getattr(ns, 'hsm_name', None)
    if vault_name and hsm_name:
        raise CLIError('--vault-name and --hsm-name are mutually exclusive.')

    if not vault_name and not hsm_name:
        raise CLIError('Please specify --vault-name or --hsm-name.')

# PARAMETER NAMESPACE VALIDATORS


def get_attribute_validator(name, attribute_class, create=False):
    def validator(ns):
        ns_dict = ns.__dict__
        enabled = not ns_dict.pop('disabled') if create else ns_dict.pop('enabled')
        attributes = attribute_class(
            enabled=enabled,
            not_before=ns_dict.pop('not_before', None),
            expires=ns_dict.pop('expires', None))
        setattr(ns, '{}_attributes'.format(name), attributes)

    return validator


def validate_key_import_source(ns):
    byok_file = ns.byok_file
    byok_string = ns.byok_string
    pem_file = ns.pem_file
    pem_string = ns.pem_string
    pem_password = ns.pem_password
    if len([arg for arg in [byok_file, byok_string, pem_file, pem_string] if arg]) != 1:
        raise ValueError('supply exactly one: --byok-file, --byok-string, --pem-file, --pem-string')
    if (byok_file or byok_string) and pem_password:
        raise ValueError('--byok-file or --byok-string cannot be used with --pem-password')
    if pem_password and not pem_file and not pem_string:
        raise ValueError('--pem-password must be used with --pem-file or --pem-string')


def validate_key_import_type(ns):
    # Default value of kty is: RSA
    kty = getattr(ns, 'kty', None)
    crv = getattr(ns, 'curve', None)

    if (kty == 'EC' and crv is None) or (kty != 'EC' and crv):
        from azure.cli.core.azclierror import ValidationError
        raise ValidationError('parameter --curve should be specified when key type --kty is EC.')


def validate_key_type(ns):
    crv = getattr(ns, 'curve', None)
    kty = getattr(ns, 'kty', None) or ('EC' if crv else 'RSA')
    protection = getattr(ns, 'protection', None)

    if protection == 'hsm':
        kty = kty if kty.endswith('-HSM') else kty + '-HSM'
    elif protection == 'software':
        if getattr(ns, 'byok_file', None):
            raise CLIError('BYOK keys are hardware protected. Omit --protection')
        if kty.endswith('-HSM'):
            raise CLIError('The key type {} is invalid for software protected keys. Omit --protection')

    setattr(ns, 'kty', kty)


def process_key_release_policy(cmd, ns):
    default_cvm_policy = None
    if hasattr(ns, 'default_cvm_policy'):
        default_cvm_policy = ns.default_cvm_policy
        del ns.default_cvm_policy

    immutable = None
    if hasattr(ns, 'immutable'):
        immutable = ns.immutable
        del ns.immutable

    if not ns.release_policy and not default_cvm_policy:
        if immutable is not None:
            raise InvalidArgumentValueError('Please provide policy when setting `--immutable`')
        return

    if ns.release_policy and default_cvm_policy:
        raise InvalidArgumentValueError('Can not specify both `--policy` and `--default-cvm-policy`')

    import json
    KeyReleasePolicy = cmd.loader.get_sdk('KeyReleasePolicy', mod='_models',
                                          resource_type=ResourceType.DATA_KEYVAULT_KEYS)
    if default_cvm_policy:
        policy = {
            'version': '1.0.0',
            'anyOf': [
                {
                    'authority': 'https://sharedeus.eus.attest.azure.net/',
                    'allOf': [
                        {
                            'claim': 'x-ms-attestation-type',
                            'equals': 'sevsnpvm'
                        },
                        {
                            'claim': 'x-ms-compliance-status',
                            'equals': 'azure-compliant-cvm'
                        }
                    ]
                },
                {
                    'authority': 'https://sharedwus.wus.attest.azure.net/',
                    'allOf': [
                        {
                            'claim': 'x-ms-attestation-type',
                            'equals': 'sevsnpvm'
                        },
                        {
                            'claim': 'x-ms-compliance-status',
                            'equals': 'azure-compliant-cvm'
                        }
                    ]
                },
                {
                    'authority': 'https://sharedneu.neu.attest.azure.net/',
                    'allOf': [
                        {
                            'claim': 'x-ms-attestation-type',
                            'equals': 'sevsnpvm'
                        },
                        {
                            'claim': 'x-ms-compliance-status',
                            'equals': 'azure-compliant-cvm'
                        }
                    ]
                },
                {
                    'authority': 'https://sharedweu.weu.attest.azure.net/',
                    'allOf': [
                        {
                            'claim': 'x-ms-attestation-type',
                            'equals': 'sevsnpvm'
                        },
                        {
                            'claim': 'x-ms-compliance-status',
                            'equals': 'azure-compliant-cvm'
                        }
                    ]
                }
            ]
        }
        ns.release_policy = KeyReleasePolicy(encoded_policy=json.dumps(policy).encode('utf-8'),
                                             immutable=immutable)
        return

    import os
    if os.path.exists(ns.release_policy):
        data = get_file_json(ns.release_policy)
    else:
        data = shell_safe_json_parse(ns.release_policy)

    ns.release_policy = KeyReleasePolicy(encoded_policy=json.dumps(data).encode('utf-8'),
                                         immutable=immutable)


def validate_policy_permissions(ns):
    key_perms = ns.key_permissions
    secret_perms = ns.secret_permissions
    cert_perms = ns.certificate_permissions
    storage_perms = ns.storage_permissions

    if not any([key_perms, secret_perms, cert_perms, storage_perms]):
        raise argparse.ArgumentError(
            None,
            'specify at least one: --key-permissions, --secret-permissions, '
            '--certificate-permissions --storage-permissions')


def validate_private_endpoint_connection_id(cmd, ns):
    if ns.connection_id:
        from azure.cli.core.util import parse_proxy_resource_id
        result = parse_proxy_resource_id(ns.connection_id)
        ns.resource_group_name = result['resource_group']
        if result['type'] and 'managedHSM' in result['type']:
            ns.hsm_name = result['name']
        else:
            ns.vault_name = result['name']
        ns.private_endpoint_connection_name = result['child_name_1']

    if not ns.resource_group_name:
        ns.resource_group_name = _get_resource_group_from_resource_name(cli_ctx=cmd.cli_ctx,
                                                                        vault_name=getattr(ns, 'vault_name', None),
                                                                        hsm_name=getattr(ns, 'hsm_name', None))

    if not all([(getattr(ns, 'vault_name', None) or getattr(ns, 'hsm_name', None)),
                ns.resource_group_name, ns.private_endpoint_connection_name]):
        raise CLIError('incorrect usage: [--id ID | --name NAME --vault-name NAME | --name NAME --hsm-name NAME]')

    del ns.connection_id


def validate_principal(ns):
    num_set = sum(1 for p in [ns.object_id, ns.spn, ns.upn] if p)
    if num_set != 1:
        raise argparse.ArgumentError(
            None, 'specify exactly one: --object-id, --spn, --upn')


def validate_resource_group_name(cmd, ns):
    """
    Populate resource_group_name, if not provided
    """
    if 'keyvault purge' in cmd.name or 'keyvault recover' in cmd.name:
        return

    vault_name = getattr(ns, 'vault_name', None)
    hsm_name = getattr(ns, 'hsm_name', None)
    if 'keyvault update-hsm' in cmd.name:
        hsm_name = getattr(ns, 'name', None)

    if vault_name and hsm_name:
        raise CLIError('--name/-n and --hsm-name are mutually exclusive.')

    if vault_name:
        # This is a temporary solution for showing deprecation message only for vaults
        _show_vault_only_deprecate_message(ns)

    if not ns.resource_group_name:
        group_name = _get_resource_group_from_resource_name(cmd.cli_ctx, vault_name, hsm_name)
        if group_name:
            ns.resource_group_name = group_name
        else:
            if vault_name:
                resource_type = 'Vault'
            else:
                resource_type = 'HSM'
            msg = "The {} '{}' not found within subscription."
            raise CLIError(msg.format(resource_type, vault_name if vault_name else hsm_name))


def validate_deleted_vault_or_hsm_name(cmd, ns):
    """
    Validate a deleted vault name; populate or validate location and resource_group_name
    """
    from msrestazure.tools import parse_resource_id

    vault_name = getattr(ns, 'vault_name', None)
    hsm_name = getattr(ns, 'hsm_name', None)

    if not vault_name and not hsm_name:
        raise CLIError('Please specify --vault-name or --hsm-name.')

    if vault_name:
        resource_name = vault_name
    else:
        resource_name = hsm_name
    resource = None

    if vault_name:
        client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_KEYVAULT).vaults
    else:
        client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_KEYVAULT).managed_hsms

    # if the location is specified, use get_deleted rather than list_deleted
    if ns.location:
        resource = client.get_deleted(resource_name, ns.location)
        if vault_name:
            id_comps = parse_resource_id(resource.properties.vault_id)
        else:
            id_comps = parse_resource_id(resource.properties.mhsm_id)

    # otherwise, iterate through deleted vaults to find one with a matching name
    else:
        for v in client.list_deleted():
            if vault_name:
                id_comps = parse_resource_id(v.properties.vault_id)
            else:
                id_comps = parse_resource_id(v.properties.mhsm_id)
            if id_comps['name'].lower() == resource_name.lower():
                resource = v
                ns.location = resource.properties.location
                break

    # if the vault was not found, throw an error
    if not resource:
        raise CLIError('No deleted Vault or HSM was found with name ' + resource_name)

    if 'keyvault purge' not in cmd.name and 'keyvault show-deleted' not in cmd.name:
        setattr(ns, 'resource_group_name', getattr(ns, 'resource_group_name', None) or id_comps['resource_group'])

        # resource_group_name must match the resource group of the deleted vault
        if id_comps['resource_group'] != ns.resource_group_name:
            raise CLIError("The specified resource group does not match that of the deleted vault or hsm %s. The vault "
                           "or hsm must be recovered to the original resource group %s."
                           % (vault_name, id_comps['resource_group']))


def validate_x509_certificate_chain(ns):
    def _load_certificate_as_bytes(file_name):
        cert_list = []
        regex = r'-----BEGIN CERTIFICATE-----([^-]+)-----END CERTIFICATE-----'
        with open(file_name, 'r') as f:
            cert_data = f.read()
            for entry in re.findall(regex, cert_data):
                cert_list.append(base64.b64decode(entry.replace('\n', '')))
        return cert_list

    ns.x509_certificates = _load_certificate_as_bytes(ns.x509_certificates)


# ARGUMENT TYPES


def certificate_type(string):
    """ Loads file and outputs contents as base64 encoded string. """
    import os
    try:
        with open(os.path.expanduser(string), 'rb') as f:
            cert_data = f.read()
        return cert_data
    except (IOError, OSError) as e:
        raise CLIError("Unable to load certificate file '{}': {}.".format(string, e.strerror))


def datetime_type(string):
    """ Validates UTC datettime in accepted format. Examples: 2017-12-31T01:11:59Z,
    2017-12-31T01:11Z or 2017-12-31T01Z or 2017-12-31 """
    accepted_date_formats = ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%MZ',
                             '%Y-%m-%dT%HZ', '%Y-%m-%d']
    for form in accepted_date_formats:
        try:
            return datetime.strptime(string, form)
        except ValueError:  # checks next format
            pass
    raise ValueError("Input '{}' not valid. Valid example: 2000-12-31T12:59:59Z".format(string))


def _get_base_url_type(cli_ctx, service):
    suffix = ''
    if service == 'vault':
        suffix = cli_ctx.cloud.suffixes.keyvault_dns
    elif service == 'hsm':
        from azure.cli.core.cloud import CloudSuffixNotSetException
        try:
            suffix = cli_ctx.cloud.suffixes.mhsm_dns
        except CloudSuffixNotSetException:  # For Azure Stack and Air-Gaped Cloud
            suffix = ''

    def base_url_type(name):
        return 'https://{}{}'.format(name, suffix)

    return base_url_type


def get_vault_base_url_type(cli_ctx):
    return _get_base_url_type(cli_ctx, service='vault')


def get_hsm_base_url_type(cli_ctx):
    return _get_base_url_type(cli_ctx, service='hsm')


def _construct_vnet(cmd, resource_group_name, vnet_name, subnet_name):
    from msrestazure.tools import resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    return resource_id(
        subscription=get_subscription_id(cmd.cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.Network',
        type='virtualNetworks',
        name=vnet_name,
        child_type_1='subnets',
        child_name_1=subnet_name)


def validate_subnet(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id

    subnet = namespace.subnet
    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        return

    if subnet and not subnet_is_id and vnet:
        namespace.subnet = _construct_vnet(cmd, namespace.resource_group_name, vnet, subnet)
    else:
        raise CLIError('incorrect usage: [--subnet ID | --subnet NAME --vnet-name NAME]')


def validate_ip_address(namespace):
    # if there are overlapping ip ranges, throw an exception
    ip_address = namespace.ip_address

    if not ip_address:
        return

    ip_address_networks = [ip_network(ip) for ip in ip_address]
    for idx, ip_address_network in enumerate(ip_address_networks):
        for idx2, ip_address_network2 in enumerate(ip_address_networks):
            if idx == idx2:
                continue
            if ip_address_network.overlaps(ip_address_network2):
                raise InvalidArgumentValueError(f"ip addresses {ip_address_network} and {ip_address_network2} "
                                                f"provided are overlapping: --ip_address ip1 [ip2]...")


def validate_role_assignment_args(ns):
    if not any([ns.role_assignment_name, ns.scope, ns.assignee, ns.assignee_object_id, ns.role, ns.ids]):
        raise RequiredArgumentMissingError(
            'Please specify at least one of these parameters: '
            '--name, --scope, --assignee, --assignee-object-id, --role, --ids')


def validate_vault_or_hsm(ns):
    identifier = getattr(ns, 'identifier', None)
    vault_base_url = getattr(ns, 'vault_base_url', None)
    hsm_name = getattr(ns, 'hsm_name', None)
    if identifier:
        if vault_base_url:
            raise CLIError('--vault-name and --id are mutually exclusive.')
        if hsm_name:
            raise CLIError('--hsm-name and --id are mutually exclusive.')

        items = identifier.split('/')
        if len(items) < 3:
            raise CLIError('Invalid id for Vault or HSM.')

        ns.vault_base_url = ns.identifier = '/'.join(items[:3])
    else:
        if vault_base_url and hsm_name:
            raise CLIError('--vault-name and --hsm-name are mutually exclusive.')

        if not vault_base_url and not hsm_name:
            raise CLIError('Please specify --vault-name or --hsm-name.')


def _show_vault_only_deprecate_message(ns):
    message_dict = {
        'keyvault delete':
            Deprecated(ns.cmd.cli_ctx, message_func=lambda x:
                       'Warning! If you have soft-delete protection enabled on this key vault, you will '
                       'not be able to reuse this key vault name until the key vault has been purged from '
                       'the soft deleted state. Please see the following documentation for additional '
                       'guidance.\nhttps://docs.microsoft.com/azure/key-vault/general/soft-delete-overview'),
        'keyvault key delete':
            Deprecated(ns.cmd.cli_ctx, message_func=lambda x:
                       'Warning! If you have soft-delete protection enabled on this key vault, this key '
                       'will be moved to the soft deleted state. You will not be able to create a key with '
                       'the same name within this key vault until the key has been purged from the '
                       'soft-deleted state. Please see the following documentation for additional '
                       'guidance.\nhttps://docs.microsoft.com/azure/key-vault/general/soft-delete-overview')
    }
    cmds = ['keyvault delete', 'keyvault key delete']
    for cmd in cmds:
        if cmd == getattr(ns, 'command', None):
            print(message_dict[cmd].message, file=sys.stderr)


def set_vault_base_url(ns):
    vault_base_url = getattr(ns, 'vault_base_url', None)
    hsm_name = getattr(ns, 'hsm_name', None)

    if not hsm_name:
        # This is a temporary solution for showing deprecation message only for vaults
        _show_vault_only_deprecate_message(ns)

    if hsm_name and not vault_base_url:
        setattr(ns, 'vault_base_url', hsm_name)


def validate_key_id(entity_type):
    def _validate(ns):
        from azure.keyvault.key_vault_id import KeyVaultIdentifier

        pure_entity_type = entity_type.replace('deleted', '')
        name = getattr(ns, pure_entity_type + '_name', None)
        vault = getattr(ns, 'vault_base_url', None)
        if not vault:
            vault = getattr(ns, 'hsm_name', None)
        identifier = getattr(ns, 'identifier', None)

        if identifier:
            vault_base_url = getattr(ns, 'vault_base_url', None)
            hsm_name = getattr(ns, 'hsm_name', None)
            if vault_base_url:
                raise CLIError('--vault-name and --id are mutually exclusive.')
            if hsm_name:
                raise CLIError('--hsm-name and --id are mutually exclusive.')

            ident = KeyVaultIdentifier(uri=identifier, collection=entity_type + 's')
            setattr(ns, pure_entity_type + '_name', ident.name)
            setattr(ns, 'vault_base_url', ident.vault)
            if ident.version and hasattr(ns, pure_entity_type + '_version'):
                setattr(ns, pure_entity_type + '_version', ident.version)
        elif not (name and vault):
            raise CLIError('incorrect usage: --id ID | --vault-name/--hsm-name VAULT/HSM '
                           '--name/-n NAME [--version VERSION]')

    return _validate


def validate_keyvault_resource_id(entity_type):
    def _validate(ns):
        from azure.keyvault.key_vault_id import KeyVaultIdentifier

        pure_entity_type = entity_type.replace('deleted', '')
        name = getattr(ns, pure_entity_type + '_name', None) or getattr(ns, 'name', None)
        vault = getattr(ns, 'vault_base_url', None)
        if not vault:
            vault = getattr(ns, 'hsm_name', None)
        identifier = getattr(ns, 'identifier', None)

        if identifier:
            vault_base_url = getattr(ns, 'vault_base_url', None)
            hsm_name = getattr(ns, 'hsm_name', None)
            if vault_base_url:
                raise CLIError('--vault-name and --id are mutually exclusive.')
            if hsm_name:
                raise CLIError('--hsm-name and --id are mutually exclusive.')

            ident = KeyVaultIdentifier(uri=identifier, collection=entity_type + 's')
            if getattr(ns, 'command', None) and 'key rotation-policy' in ns.command:
                setattr(ns, 'key_name', ident.name)
            else:
                setattr(ns, 'name', ident.name)
            setattr(ns, 'vault_base_url', ident.vault)
            if ident.version and (hasattr(ns, pure_entity_type + '_version') or hasattr(ns, 'version')):
                setattr(ns, 'version', ident.version)
        elif not (name and vault):
            raise CLIError('incorrect usage: --id ID | --vault-name/--hsm-name VAULT/HSM '
                           '--name/-n NAME [--version VERSION]')

    return _validate


def validate_sas_definition_id(ns):
    from azure.keyvault import StorageSasDefinitionId
    acct_name = getattr(ns, 'storage_account_name', None)
    sas_name = getattr(ns, 'sas_definition_name', None)
    vault = getattr(ns, 'vault_base_url', None)
    identifier = getattr(ns, 'identifier', None)

    if identifier:
        ident = StorageSasDefinitionId(uri=identifier)
        setattr(ns, 'sas_definition_name', getattr(ident, 'sas_definition'))
        setattr(ns, 'storage_account_name', getattr(ident, 'account_name'))
        setattr(ns, 'vault_base_url', ident.vault)
    elif not (acct_name and sas_name and vault):
        raise CLIError('incorrect usage: --id ID | --vault-name VAULT --account-name --name NAME')


def validate_storage_account_id(ns):
    from azure.keyvault import StorageAccountId
    acct_name = getattr(ns, 'storage_account_name', None)
    vault = getattr(ns, 'vault_base_url', None)
    identifier = getattr(ns, 'identifier', None)

    if identifier:
        ident = StorageAccountId(uri=identifier)
        setattr(ns, 'storage_account_name', ident.name)
        setattr(ns, 'vault_base_url', ident.vault)
    elif not (acct_name and vault):
        raise CLIError('incorrect usage: --id ID | --vault-name VAULT --name NAME')


def validate_storage_disabled_attribute(attr_arg_name, attr_type):
    def _validate(ns):
        disabled = getattr(ns, 'disabled', None)
        attr_arg = attr_type(enabled=(not disabled))
        setattr(ns, attr_arg_name, attr_arg)
    return _validate


def validate_encryption(ns):
    if ns.data_type == KeyEncryptionDataType.BASE64:
        ns.value = base64.b64decode(ns.value.encode('utf-8'))
    else:
        ns.value = ns.value.encode('utf-8')
    del ns.data_type


def validate_decryption(ns):
    ns.value = base64.b64decode(ns.value)
