# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core._profile import CLOUD, Profile


def cf_dls_account(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.store import DataLakeStoreAccountManagementClient
    return get_mgmt_service_client(DataLakeStoreAccountManagementClient).account


def cf_dls_account_firewall(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.store import DataLakeStoreAccountManagementClient
    return get_mgmt_service_client(DataLakeStoreAccountManagementClient).firewall_rules


def cf_dls_account_trusted_provider(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.store import DataLakeStoreAccountManagementClient
    return get_mgmt_service_client(DataLakeStoreAccountManagementClient).trusted_id_providers


def cf_dls_filesystem(account_name):
    from azure.datalake.store import core
    profile = Profile()
    subscription_id = None
    cred, subscription_id, _ = profile.get_login_credentials(subscription_id=subscription_id)
    return core.AzureDLFileSystem(
        token=cred,
        store_name=account_name,
        url_suffix=CLOUD.suffixes.azure_datalake_store_file_system_endpoint)
