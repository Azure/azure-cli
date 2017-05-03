# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def keyvault_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.keyvault import KeyVaultManagementClient
    return get_mgmt_service_client(KeyVaultManagementClient)


def keyvault_client_vaults_factory(kwargs):
    return keyvault_client_factory(**kwargs).vaults
