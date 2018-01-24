# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import base64
import binascii
from datetime import datetime
import re

from knack.util import CLIError

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import validate_tags


secret_text_encoding_values = ['utf-8', 'utf-16le', 'utf-16be', 'ascii']
secret_binary_encoding_values = ['base64', 'hex']


def _extract_version(item_id):
    return item_id.split('/')[-1]


def _get_resource_group_from_vault_name(cli_ctx, vault_name):
    """
    Fetch resource group from vault name
    :param str vault_name: name of the key vault
    :return: resource group name or None
    :rtype: str
    """
    from azure.mgmt.keyvault import KeyVaultManagementClient
    from msrestazure.tools import parse_resource_id

    client = get_mgmt_service_client(cli_ctx, KeyVaultManagementClient).vaults
    for vault in client.list():
        id_comps = parse_resource_id(vault.id)
        if id_comps['name'] == vault_name:
            return id_comps['resource_group']
    return None


# COMMAND NAMESPACE VALIDATORS


def process_certificate_cancel_namespace(namespace):
    namespace.cancellation_requested = True


def process_secret_set_namespace(namespace):
    validate_tags(namespace)

    content = namespace.value
    file_path = namespace.file_path
    encoding = namespace.encoding
    tags = namespace.tags or {}

    use_error = CLIError("incorrect usage: [Required] --value VALUE | --file PATH")

    if (content and file_path) or (not content and not file_path):
        raise use_error

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


# PARAMETER NAMESPACE VALIDATORS


def get_attribute_validator(name, attribute_class, create=False):
    def validator(ns):
        ns_dict = ns.__dict__
        enabled = not ns_dict.pop('disabled') if create else ns_dict.pop('enabled')
        attributes = attribute_class(
            enabled,
            ns_dict.pop('not_before', None),
            ns_dict.pop('expires', None))
        setattr(ns, '{}_attributes'.format(name), attributes)

    return validator


def validate_key_import_source(ns):
    byok_file = ns.byok_file
    pem_file = ns.pem_file
    pem_password = ns.pem_password
    if (not byok_file and not pem_file) or (byok_file and pem_file):
        raise ValueError('supply exactly one: --byok-file, --pem-file')
    if byok_file and pem_password:
        raise ValueError('--byok-file cannot be used with --pem-password')
    if pem_password and not pem_file:
        raise ValueError('--pem-password must be used with --pem-file')


def validate_key_type(ns):
    if ns.destination:
        dest_to_type_map = {
            'software': 'RSA',
            'hsm': 'RSA-HSM'
        }
        ns.destination = dest_to_type_map[ns.destination]
        if ns.destination == 'RSA' and hasattr(ns, 'byok_file') and ns.byok_file:
            raise CLIError('BYOK keys are hardware protected. Omit --protection')


def validate_policy_permissions(ns):
    key_perms = ns.key_permissions
    secret_perms = ns.secret_permissions
    cert_perms = ns.certificate_permissions

    if not any([key_perms, secret_perms, cert_perms]):
        raise argparse.ArgumentError(
            None,
            'specify at least one: --key-permissions, --secret-permissions, '
            '--certificate-permissions')


def validate_principal(ns):
    num_set = sum(1 for p in [ns.object_id, ns.spn, ns.upn] if p)
    if num_set != 1:
        raise argparse.ArgumentError(
            None, 'specify exactly one: --object-id, --spn, --upn')


def validate_resource_group_name(cmd, ns):
    if not ns.resource_group_name:
        vault_name = ns.vault_name
        group_name = _get_resource_group_from_vault_name(cmd.cli_ctx, vault_name)
        if group_name:
            ns.resource_group_name = group_name
        else:
            msg = "The Resource 'Microsoft.KeyVault/vaults/{}' not found within subscription."
            raise CLIError(msg.format(vault_name))


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
    with open(os.path.expanduser(string), 'rb') as f:
        cert_data = f.read()
    return cert_data


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


def get_vault_base_url_type(cli_ctx):

    suffix = cli_ctx.cloud.suffixes.keyvault_dns

    def vault_base_url_type(name):
        return 'https://{}{}'.format(name, suffix)

    return vault_base_url_type
