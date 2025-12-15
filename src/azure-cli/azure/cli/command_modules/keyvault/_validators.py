# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import base64
import binascii
from datetime import datetime, timezone
import re
import sys
from ipaddress import ip_network

from enum import Enum
from knack.deprecation import Deprecated
from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import validate_tags
from azure.cli.core.azclierror import RequiredArgumentMissingError, InvalidArgumentValueError, AzureInternalError
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import get_file_json, shell_safe_json_parse

logger = get_logger(__name__)

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
    from azure.mgmt.core.tools import parse_resource_id

    if vault_name:
        client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT).vaults
        for vault in client.list(filter=f"resourceType eq 'Microsoft.KeyVault/vaults' and name eq '{vault_name}'"):
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
def process_secret_set_namespace(namespace):
    validate_tags(namespace)

    content = namespace.value
    file_path = namespace.file_path
    encoding = namespace.encoding
    tags = namespace.tags or {}

    use_error = CLIError("incorrect usage: [Required] --value VALUE | --file PATH")

    if (content and file_path) or (not content and not file_path):
        raise use_error

    namespace.enabled = not namespace.disabled if namespace.disabled is not None else None
    del namespace.file_path
    del namespace.encoding
    del namespace.disabled

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


def validate_retention_days_on_creation(ns):
    # If customer has specified retention days, nothing to do
    if ns.retention_days:
        return
    # If customer has not specified retention days,
    # ask for mandatory retention days for MHSM creation, else set to default '90' for keyvault creation
    if getattr(ns, 'hsm_name', None):
        raise RequiredArgumentMissingError("--retention-days is required for MHSM creation.")
    if getattr(ns, 'vault_name', None):
        ns.retention_days = '90'


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


# pylint: disable=line-too-long
def _fetch_default_release_policy(cli_ctx, vault_url, policy_type='cvm'):
    try:
        # get vault/hsm location
        mgmt_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT)
        location = None
        parsed_vault_url = vault_url.removeprefix('https://').split('.')
        if parsed_vault_url[1] == 'vault':
            vault_name_filter = f"resourceType eq 'Microsoft.KeyVault/vaults' and name eq '{parsed_vault_url[0]}'"
            for vault in mgmt_client.vaults.list(filter=vault_name_filter):
                location = vault.location
                break
        elif parsed_vault_url[1] == 'managedhsm':
            for hsm in mgmt_client.managed_hsms.list_by_subscription():
                if hsm.name == parsed_vault_url[0]:
                    location = hsm.location
                    break
        if not location:
            raise InvalidArgumentValueError(f"Fail to fetch default cvm policy due to invalid {vault_url}")

        # call MAA to get default cvm policy
        from azure.cli.core.util import send_raw_request
        from azure.cli.core.commands.client_factory import get_subscription_id
        _endpoint = cli_ctx.cloud.endpoints.resource_manager
        if _endpoint.endswith('/'):
            _endpoint = _endpoint[:-1]
        default_release_policy_url = f"{_endpoint}/subscriptions/{get_subscription_id(cli_ctx)}/providers/Microsoft.Attestation/Locations/{location}/defaultProvider?api-version=2020-10-01"
        response = send_raw_request(cli_ctx, 'get', default_release_policy_url)
        if response.status_code != 200:
            raise AzureInternalError(f"Fail to fetch default release policy from {default_release_policy_url}")

        # extract attest uri from response as authority in cvm policy
        import json
        res_json = json.loads(response.text)
        attest_uri = res_json['properties']['attestUri']
        if policy_type == 'cvm':
            default_release_policy = {
                'version': '1.0.0',
                'anyOf': [
                    {
                        'authority': attest_uri,
                        'allOf': [
                            {
                                'claim': 'x-ms-compliance-status',
                                'equals': 'azure-compliant-cvm'
                            }
                        ]
                    }
                ]
            }
        else:
            default_release_policy = {
                'version': '1.0.0',
                'anyOf': [
                    {
                        'authority': attest_uri,
                        'allOf': [
                            {
                                'anyOf': [
                                    {
                                        'claim': 'x-ms-isolation-tee.x-ms-attestation-type',
                                        'equals': 'sevsnpvm'
                                    },
                                    {
                                        'claim': 'x-ms-isolation-tee.x-ms-attestation-type',
                                        'equals': 'tdxvm'
                                    }
                                ]
                            },
                            {
                                'claim': 'x-ms-isolation-tee.x-ms-compliance-status',
                                'equals': 'azure-compliant-cvm'
                            }
                        ]
                    }
                ]
            }
        return default_release_policy
    except Exception as ex:  # pylint: disable=broad-except
        raise AzureInternalError(f"Fail to fetch default release policy: {ex}")


def process_key_release_policy(cmd, ns):
    default_cvm_policy = None
    default_data_disk_policy = None
    if hasattr(ns, 'default_cvm_policy'):
        default_cvm_policy = ns.default_cvm_policy
        del ns.default_cvm_policy
    if hasattr(ns, 'default_data_disk_policy'):
        default_data_disk_policy = ns.default_data_disk_policy
        del ns.default_data_disk_policy

    immutable = None
    if hasattr(ns, 'immutable'):
        immutable = ns.immutable
        del ns.immutable

    if not ns.release_policy and not default_cvm_policy and not default_data_disk_policy:
        if immutable is not None:
            raise InvalidArgumentValueError('Please provide policy when setting `--immutable`')
        return

    if ns.release_policy and default_cvm_policy:
        raise InvalidArgumentValueError('Can not specify both `--policy` and `--default-cvm-policy`')
    if ns.release_policy and default_data_disk_policy:
        raise InvalidArgumentValueError('Can not specify both `--policy` and `--default-data-disk-policy`')
    if default_cvm_policy and default_data_disk_policy:
        from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
        raise MutuallyExclusiveArgumentError('`--default-cvm-policy` and `--default-data-disk-policy` '
                                             'are mutually exclusive')

    import json
    KeyReleasePolicy = cmd.loader.get_sdk('KeyReleasePolicy', mod='_models',
                                          resource_type=ResourceType.DATA_KEYVAULT_KEYS)
    if default_cvm_policy or default_data_disk_policy:
        vault_url = getattr(ns, 'hsm_name', None) or getattr(ns, 'vault_base_url', None)
        if not vault_url:
            vault_url = getattr(ns, 'identifier', None)
        policy = _fetch_default_release_policy(cmd.cli_ctx, vault_url, 'cvm' if default_cvm_policy else 'data_disk')
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

    if key_perms is None and secret_perms is None and cert_perms is None and storage_perms is None:
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
    if 'keyvault update-hsm' in cmd.name or 'keyvault region' in cmd.name:
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
    from azure.mgmt.core.tools import parse_resource_id

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
    except OSError as e:
        raise CLIError("Unable to load certificate file '{}': {}.".format(string, e.strerror))


def datetime_type(string):
    """ Validates UTC datettime in accepted format. Examples: 2017-12-31T01:11:59Z,
    2017-12-31T01:11Z or 2017-12-31T01Z or 2017-12-31 """
    accepted_date_formats = ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%MZ',
                             '%Y-%m-%dT%HZ', '%Y-%m-%d']
    for form in accepted_date_formats:
        try:
            return datetime.strptime(string, form).replace(tzinfo=timezone.utc)
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
    from azure.mgmt.core.tools import resource_id
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
    from azure.mgmt.core.tools import is_valid_resource_id

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
                       'guidance.\nhttps://learn.microsoft.com/azure/key-vault/general/soft-delete-overview'),
        'keyvault key delete':
            Deprecated(ns.cmd.cli_ctx, message_func=lambda x:
                       'Warning! If you have soft-delete protection enabled on this key vault, this key '
                       'will be moved to the soft deleted state. You will not be able to create a key with '
                       'the same name within this key vault until the key has been purged from the '
                       'soft-deleted state. Please see the following documentation for additional '
                       'guidance.\nhttps://learn.microsoft.com/azure/key-vault/general/soft-delete-overview')
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
        from azure.keyvault.keys._shared import parse_key_vault_id

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

            ident = parse_key_vault_id(identifier)
            setattr(ns, pure_entity_type + '_name', ident.name)
            setattr(ns, 'vault_base_url', ident.vault_url)
            if ident.version and hasattr(ns, pure_entity_type + '_version'):
                setattr(ns, pure_entity_type + '_version', ident.version)
        elif not (name and vault):
            raise CLIError('incorrect usage: --id ID | --vault-name/--hsm-name VAULT/HSM '
                           '--name/-n NAME [--version VERSION]')

    return _validate


def validate_keyvault_resource_id(entity_type):
    def _validate(ns):
        from azure.keyvault.keys._shared import parse_key_vault_id

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

            kv_resource_id = parse_key_vault_id(identifier)
            if getattr(ns, 'command', None) and 'key rotation-policy' in ns.command:
                setattr(ns, 'key_name', kv_resource_id.name)
            elif getattr(ns, 'command', None) and 'certificate' in ns.command:
                setattr(ns, 'certificate_name', kv_resource_id.name)
            else:
                setattr(ns, 'name', kv_resource_id.name)
            setattr(ns, 'vault_base_url', kv_resource_id.vault_url)
            if kv_resource_id.version and (hasattr(ns, pure_entity_type + '_version') or hasattr(ns, 'version')):
                setattr(ns, 'version', kv_resource_id.version)
        elif not (name and vault):
            raise CLIError('incorrect usage: --id ID | --vault-name/--hsm-name VAULT/HSM '
                           '--name/-n NAME [--version VERSION]')

    return _validate


def validate_encryption(ns):
    if ns.data_type == KeyEncryptionDataType.BASE64:
        ns.value = base64.b64decode(ns.value.encode('utf-8'))
    else:
        ns.value = ns.value.encode('utf-8')
    del ns.data_type


def validate_decryption(ns):
    ns.value = base64.b64decode(ns.value)


def validate_key_create(cmd, ns):
    validate_tags(ns)
    set_vault_base_url(ns)
    validate_keyvault_resource_id('key')(ns)
    validate_key_type(ns)
    process_key_release_policy(cmd, ns)


# pylint: disable=line-too-long, too-many-locals
def process_certificate_policy(cmd, ns):
    policy = getattr(ns, 'policy', None)
    if policy is None:
        return
    if not isinstance(policy, dict):
        raise CLIError('incorrect usage: policy should be a JSON encoded string '
                       'or can use @{file} to load from a file(e.g.@my_policy.json).')

    secret_properties = policy.get('secret_properties') or {}
    if not secret_properties.get('content_type') \
            and hasattr(ns, 'certificate_bytes') and ns.certificate_bytes:
        from OpenSSL import crypto
        try:
            crypto.load_certificate(crypto.FILETYPE_PEM, ns.certificate_bytes)
            # if we get here, we know it was a PEM file
            secret_properties['content_type'] = 'application/x-pem-file'
        except (ValueError, crypto.Error):
            # else it should be a pfx file
            secret_properties['content_type'] = 'application/x-pkcs12'
        policy['secret_properties'] = secret_properties

    if hasattr(ns, 'validity'):
        x509_certificate_properties = policy.get('x509_certificate_properties') or {}
        if ns.validity:
            x509_certificate_properties['validity_in_months'] = ns.validity
            policy['x509_certificate_properties'] = x509_certificate_properties
        del ns.validity

    policyObj = build_certificate_policy(cmd.cli_ctx, policy)
    ns.policy = policyObj


def build_certificate_policy(cli_ctx, policy: dict):
    from azure.cli.core.profiles import get_sdk
    CertificatePolicy = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT_CERTIFICATES,
                                'CertificatePolicy', mod='_models')
    CertificateAttributes = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT_CERTIFICATES,
                                    'CertificateAttributes', mod='_generated_models')
    LifetimeAction = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT_CERTIFICATES,
                             'LifetimeAction', mod='_models')

    issuer_name = subject = exportable = key_type = key_size = reuse_key = key_curve_name = enhanced_key_usage \
        = key_usage = content_type = validity_in_months = issuer_certificate_type = certificate_transparency = san_emails \
        = san_dns_names = san_user_principal_names = None

    attributes = policy.get('attributes')
    if attributes:
        attributes = CertificateAttributes(
            enabled=attributes.get('enabled'),
            not_before=attributes.get('not_before'),
            expires=attributes.get('expires_on'),
        )

    issuer_parameters = policy.get('issuer_parameters')
    if issuer_parameters:
        issuer_name = issuer_parameters.get('name')
        issuer_certificate_type = issuer_parameters.get('certificate_type')
        certificate_transparency = issuer_parameters.get('certificate_transparency')

    key_properties = policy.get('key_properties')
    if key_properties:
        exportable = key_properties.get('exportable')
        key_type = key_properties.get('key_type')
        key_size = key_properties.get('key_size')
        reuse_key = key_properties.get('reuse_key')
        key_curve_name = key_properties.get('curve')

    lifetime_actions = policy.get('lifetime_actions')
    if lifetime_actions:
        lifetime_actions = [
            LifetimeAction(
                action=item['action'].get('action_type') if item.get('action') else None,
                lifetime_percentage=item['trigger'].get('lifetime_percentage') if item.get('trigger') else None,
                days_before_expiry=item['trigger'].get('days_before_expiry') if item.get('trigger') else None
            )
            for item in lifetime_actions]

    secret_properties = policy.get('secret_properties')
    if secret_properties:
        content_type = secret_properties.get('content_type')

    x509_certificate_properties = policy.get('x509_certificate_properties')
    if x509_certificate_properties:
        subject = x509_certificate_properties.get('subject')
        enhanced_key_usage = x509_certificate_properties.get('ekus')
        subject_alternative_names = x509_certificate_properties.get('subject_alternative_names')
        if subject_alternative_names:
            san_emails = subject_alternative_names.get('emails')
            san_user_principal_names = subject_alternative_names.get('upns')
            san_dns_names = subject_alternative_names.get('dns_names')
        key_usage = x509_certificate_properties.get('key_usage')
        validity_in_months = x509_certificate_properties.get('validity_in_months')

    policyObj = CertificatePolicy(issuer_name=issuer_name, subject=subject, attributes=attributes,
                                  exportable=exportable, key_type=key_type, key_size=key_size, reuse_key=reuse_key,
                                  key_curve_name=key_curve_name, enhanced_key_usage=enhanced_key_usage,
                                  key_usage=key_usage, content_type=content_type, validity_in_months=validity_in_months,
                                  lifetime_actions=lifetime_actions, certificate_type=issuer_certificate_type,
                                  certificate_transparency=certificate_transparency, san_emails=san_emails,
                                  san_dns_names=san_dns_names, san_user_principal_names=san_user_principal_names)
    return policyObj


def process_certificate_import(ns):
    if ns.disabled is not None:
        ns.enabled = not ns.disabled
    del ns.disabled
