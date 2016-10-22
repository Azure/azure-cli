#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
from datetime import datetime

from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.keyvault.models.key_vault_management_client_enums import \
    (KeyPermissions, SecretPermissions, CertificatePermissions)

from azure.cli.command_modules.keyvault.keyvaultclient.models.key_vault_client_enums import \
    (JsonWebKeyOperation)

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import parse_resource_id
from azure.cli.core._util import CLIError

def _extract_version(item_id):
    return item_id.split('/')[-1]

# COMMAND NAMESPACE VALIDATORS

# PARAMETER NAMESPACE VALIDATORS

def get_attribute_validator(name, attribute_class, create=False):

    def validator(ns):
        ns_dict = ns.__dict__
        enabled = not ns_dict.pop('disabled') if create else ns_dict.pop('enabled') == 'true'
        attributes = attribute_class(
            enabled,
            ns_dict.pop('not_before'),
            ns_dict.pop('expires'))
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

def validate_key_ops(ns):
    allowed = [x.value.lower() for x in JsonWebKeyOperation]
    for p in ns.key_ops or []:
        if p not in allowed:
            raise ValueError("unrecognized key operation '{}'".format(p))

def validate_key_type(ns):
    if ns.destination:
        dest_to_type_map = {
            'software': 'RSA',
            'hsm': 'RSA-HSM'
        }
        ns.destination = dest_to_type_map[ns.destination]

def validate_policy_permissions(ns):
    key_perms = ns.key_permissions
    secret_perms = ns.secret_permissions
    cert_perms = ns.certificate_permissions

    if not any([key_perms, secret_perms, cert_perms]):
        raise argparse.ArgumentError(
            None,
            'specify at least one: --key-permissions, --secret-permissions, '
            '--certificate-permissions')

    key_allowed = [x.value for x in KeyPermissions]
    secret_allowed = [x.value for x in SecretPermissions]
    cert_allowed = [x.value for x in CertificatePermissions]

    for p in key_perms or []:
        if p not in key_allowed:
            raise ValueError("unrecognized key permission '{}'".format(p))

    for p in secret_perms or []:
        if p not in secret_allowed:
            raise ValueError("unrecognized secret permission '{}'".format(p))

    for p in cert_perms or []:
        if p not in cert_allowed:
            raise ValueError("unrecognized cert permission '{}'".format(p))

def validate_principal(ns):
    num_set = sum(1 for p in [ns.object_id, ns.spn, ns.upn] if p)
    if num_set != 1:
        raise argparse.ArgumentError(
            None, 'specify exactly one: --object-id, --spn, --upn')

def validate_resource_group_name(ns):
    if not ns.resource_group_name:
        vault_name = ns.vault_name
        client = get_mgmt_service_client(KeyVaultManagementClient).vaults
        for vault in client.list():
            id_comps = parse_resource_id(vault.id)
            if id_comps['name'] == vault_name:
                ns.resource_group_name = id_comps['resource_group']
                return
        raise CLIError(
            "The Resource 'Microsoft.KeyVault/vaults/{}'".format(vault_name) + \
            " not found within subscription")

# ARGUMENT TYPES

def datetime_type(string):
    ''' Validates UTC datettime in format '%Y-%m-%d\'T\'%H:%M\'Z\''. '''
    date_format = '%Y-%m-%dT%H:%MZ'
    return datetime.strptime(string, date_format)

def vault_base_url_type(name):
    from azure.cli.core._profile import CLOUD
    from azure.cli.core.cloud import CloudSuffix
    suffix = CLOUD.suffixes[CloudSuffix.KEYVAULT_DNS]
    return 'https://{}{}'.format(name, suffix)
