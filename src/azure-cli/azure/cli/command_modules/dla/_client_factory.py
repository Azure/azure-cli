# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_dla_account(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    return get_mgmt_service_client(cli_ctx, DataLakeAnalyticsAccountManagementClient).account


def cf_dla_account_firewall(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    return get_mgmt_service_client(cli_ctx, DataLakeAnalyticsAccountManagementClient).firewall_rules


def cf_dla_account_compute_policy(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    return get_mgmt_service_client(cli_ctx, DataLakeAnalyticsAccountManagementClient).compute_policies


def cf_dla_account_storage(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    return get_mgmt_service_client(cli_ctx, DataLakeAnalyticsAccountManagementClient).storage_accounts


def cf_dla_account_adls(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    return get_mgmt_service_client(cli_ctx, DataLakeAnalyticsAccountManagementClient).data_lake_store_accounts


def cf_dla_catalog(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.catalog import DataLakeAnalyticsCatalogManagementClient
    return get_mgmt_service_client(
        cli_ctx,
        DataLakeAnalyticsCatalogManagementClient,
        subscription_bound=False,
        base_url_bound=False,
        resource=cli_ctx.cloud.endpoints.active_directory_data_lake_resource_id,
        adla_catalog_dns_suffix=cli_ctx.cloud.suffixes.azure_datalake_analytics_catalog_and_job_endpoint).catalog


def cf_dla_job(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.job import DataLakeAnalyticsJobManagementClient
    return get_mgmt_service_client(
        cli_ctx,
        DataLakeAnalyticsJobManagementClient,
        subscription_bound=False,
        base_url_bound=False,
        resource=cli_ctx.cloud.endpoints.active_directory_data_lake_resource_id,
        adla_job_dns_suffix=cli_ctx.cloud.suffixes.azure_datalake_analytics_catalog_and_job_endpoint).job


def cf_dla_job_recurrence(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.job import DataLakeAnalyticsJobManagementClient
    return get_mgmt_service_client(
        cli_ctx,
        DataLakeAnalyticsJobManagementClient,
        subscription_bound=False,
        base_url_bound=False,
        resource=cli_ctx.cloud.endpoints.active_directory_data_lake_resource_id,
        adla_job_dns_suffix=cli_ctx.cloud.suffixes.azure_datalake_analytics_catalog_and_job_endpoint).recurrence


def cf_dla_job_pipeline(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datalake.analytics.job import DataLakeAnalyticsJobManagementClient
    return get_mgmt_service_client(
        cli_ctx,
        DataLakeAnalyticsJobManagementClient,
        subscription_bound=False,
        base_url_bound=False,
        resource=cli_ctx.cloud.endpoints.active_directory_data_lake_resource_id,
        adla_job_dns_suffix=cli_ctx.cloud.suffixes.azure_datalake_analytics_catalog_and_job_endpoint).pipeline
