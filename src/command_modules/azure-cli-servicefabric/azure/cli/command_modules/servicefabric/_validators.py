# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

from azure.mgmt.keyvault import KeyVaultManagementClient

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import parse_resource_id

secret_text_encoding_values = ['utf-8', 'utf-16le', 'utf-16be', 'ascii']
secret_binary_encoding_values = ['base64', 'hex']


def _extract_version(item_id):
    return item_id.split('/')[-1]


def _get_resource_group_from_vault_name(vault_name):
    """
    Fetch resource group from vault name
    :param str vault_name: name of the key vault
    :return: resource group name or None
    :rtype: str
    """
    client = get_mgmt_service_client(KeyVaultManagementClient).vaults
    for vault in client.list():
        id_comps = parse_resource_id(vault.id)
        if id_comps['name'] == vault_name:
            return id_comps['resource_group']
    return None


def validate_principal(ns):
    num_set = sum(1 for p in [ns.object_id, ns.spn, ns.upn] if p)
    if num_set != 1:
        raise argparse.ArgumentError(
            None, 'specify exactly one: --object-id, --spn, --upn')


def vault_base_url_type(name):
    from azure.cli.core._profile import CLOUD
    suffix = CLOUD.suffixes.keyvault_dns
    return 'https://{}{}'.format(name, suffix)
