# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core._profile import CLOUD


def cf_dla_account(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    return get_mgmt_service_client(DataLakeAnalyticsAccountManagementClient).account


def cf_dla_account_firewall(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    return get_mgmt_service_client(DataLakeAnalyticsAccountManagementClient).firewall_rules


def cf_dla_account_storage(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    return get_mgmt_service_client(DataLakeAnalyticsAccountManagementClient).storage_accounts


def cf_dla_account_adls(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    return get_mgmt_service_client(DataLakeAnalyticsAccountManagementClient).data_lake_store_accounts


def cf_dla_catalog(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.catalog import DataLakeAnalyticsCatalogManagementClient
    return get_mgmt_service_client(
        DataLakeAnalyticsCatalogManagementClient,
        subscription_bound=False,
        base_url_bound=False,
        adla_catalog_dns_suffix=CLOUD.suffixes.azure_datalake_analytics_catalog_and_job_endpoint).catalog


def cf_dla_job(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.job import DataLakeAnalyticsJobManagementClient
    return get_mgmt_service_client(
        DataLakeAnalyticsJobManagementClient,
        subscription_bound=False,
        base_url_bound=False,
        adla_job_dns_suffix=CLOUD.suffixes.azure_datalake_analytics_catalog_and_job_endpoint).job
