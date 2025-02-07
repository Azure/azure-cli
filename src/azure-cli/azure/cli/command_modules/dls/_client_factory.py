# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_dls_account(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.store import DataLakeStoreAccountManagementClient
    return get_mgmt_service_client(cli_ctx, DataLakeStoreAccountManagementClient).accounts


def cf_dls_account_firewall(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.store import DataLakeStoreAccountManagementClient
    return get_mgmt_service_client(cli_ctx, DataLakeStoreAccountManagementClient).firewall_rules


def cf_dls_account_trusted_provider(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.store import DataLakeStoreAccountManagementClient
    return get_mgmt_service_client(cli_ctx, DataLakeStoreAccountManagementClient).trusted_id_providers


def cf_dls_filesystem(cli_ctx, account_name):
    from azure.datalake.store import core
    from azure.cli.core._profile import Profile
    from azure.cli.core.auth.util import resource_to_scopes

    cred, _, _ = Profile(cli_ctx=cli_ctx).get_login_credentials()
    return core.AzureDLFileSystem(
        token_credential=cred,
        store_name=account_name,
        url_suffix=cli_ctx.cloud.suffixes.azure_datalake_store_file_system_endpoint,
        scopes=resource_to_scopes(cli_ctx.cloud.endpoints.active_directory_data_lake_resource_id)[0])
