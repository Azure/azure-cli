# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import cli_command
from azure.cli.command_modules.dla._client_factory import (cf_dla_account,
                                                           cf_dla_account_firewall,
                                                           cf_dla_account_adls,
                                                           cf_dla_account_storage,
                                                           cf_dla_job,
                                                           cf_dla_catalog)
adla_format_path = 'azure.mgmt.datalake.analytics.{}.operations.{}#{}.{}'
adla_custom_format_path = 'azure.cli.command_modules.dla.custom#{}'

# account operations
cli_command(__name__, 'dla account create', adla_custom_format_path.format('create_adla_account'), cf_dla_account)
cli_command(__name__, 'dla account update', adla_custom_format_path.format('update_adla_account'), cf_dla_account)
cli_command(__name__, 'dla account list', adla_custom_format_path.format('list_adla_account'), cf_dla_account)
cli_command(__name__, 'dla account show', adla_format_path.format('account', 'account_operations', 'AccountOperations', 'get'), cf_dla_account)
cli_command(__name__, 'dla account delete', adla_format_path.format('account', 'account_operations', 'AccountOperations', 'delete'), cf_dla_account)

# account fire wall operations
# TODO: implement
cli_command(__name__, 'dla account firewall create', adla_custom_format_path.format('add_adla_firewall_rule'), cf_dla_account_firewall)
cli_command(__name__, 'dla account firewall update', adla_format_path.format('account', 'firewall_rules_operations', 'FirewallRulesOperations', 'update'), cf_dla_account_firewall)
cli_command(__name__, 'dla account firewall list', adla_format_path.format('account', 'firewall_rules_operations', 'FirewallRulesOperations', 'list_by_account'), cf_dla_account_firewall)
cli_command(__name__, 'dla account firewall show', adla_format_path.format('account', 'firewall_rules_operations', 'FirewallRulesOperations', 'get'), cf_dla_account_firewall)
cli_command(__name__, 'dla account firewall delete', adla_format_path.format('account', 'firewall_rules_operations', 'FirewallRulesOperations', 'delete'), cf_dla_account_firewall)

# job operations
# todo: update to allow for inclusion of statistics/debug data in show
# todo: add a polling command for jobs
cli_command(__name__, 'dla job submit', adla_custom_format_path.format('submit_adla_job'), cf_dla_job)
cli_command(__name__, 'dla job wait', adla_custom_format_path.format('wait_adla_job'), cf_dla_job)
cli_command(__name__, 'dla job show', adla_format_path.format('job', 'job_operations', 'JobOperations', 'get'), cf_dla_job)
cli_command(__name__, 'dla job cancel', adla_format_path.format('job', 'job_operations', 'JobOperations', 'cancel'), cf_dla_job)
cli_command(__name__, 'dla job list', adla_custom_format_path.format('list_adla_jobs'), cf_dla_job)

# account data source operations
cli_command(__name__, 'dla account blob-storage show', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'get'), cf_dla_account_storage)
cli_command(__name__, 'dla account blob-storage add', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'add'), cf_dla_account_storage)
cli_command(__name__, 'dla account blob-storage update', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'update'), cf_dla_account_storage)
cli_command(__name__, 'dla account blob-storage delete', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'delete'), cf_dla_account_storage)
cli_command(__name__, 'dla account blob-storage list', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'list_by_account'), cf_dla_account_storage)

cli_command(__name__, 'dla account data-lake-store show', adla_format_path.format('account', 'data_lake_store_accounts_operations', 'DataLakeStoreAccountsOperations', 'get'), cf_dla_account_adls)
cli_command(__name__, 'dla account data-lake-store list', adla_format_path.format('account', 'data_lake_store_accounts_operations', 'DataLakeStoreAccountsOperations', 'list_by_account'), cf_dla_account_adls)
cli_command(__name__, 'dla account data-lake-store add', adla_format_path.format('account', 'data_lake_store_accounts_operations', 'DataLakeStoreAccountsOperations', 'add'), cf_dla_account_adls)
cli_command(__name__, 'dla account data-lake-store delete', adla_format_path.format('account', 'data_lake_store_accounts_operations', 'DataLakeStoreAccountsOperations', 'delete'), cf_dla_account_adls)

# catalog operations
# credential
cli_command(__name__, 'dla catalog credential create', adla_custom_format_path.format('create_adla_catalog_credential'), cf_dla_catalog)
cli_command(__name__, 'dla catalog credential show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_credential'), cf_dla_catalog)
cli_command(__name__, 'dla catalog credential update', adla_custom_format_path.format('update_adla_catalog_credential'), cf_dla_catalog)
cli_command(__name__, 'dla catalog credential list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_credentials'), cf_dla_catalog)
cli_command(__name__, 'dla catalog credential delete', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'delete_credential'), cf_dla_catalog)

# database
cli_command(__name__, 'dla catalog database show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_database'), cf_dla_catalog)
cli_command(__name__, 'dla catalog database list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_databases'), cf_dla_catalog)

# schema
cli_command(__name__, 'dla catalog schema show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_schema'), cf_dla_catalog)
cli_command(__name__, 'dla catalog schema list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_schemas'), cf_dla_catalog)

# table
cli_command(__name__, 'dla catalog table show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table'), cf_dla_catalog)
cli_command(__name__, 'dla catalog table list', adla_custom_format_path.format('list_catalog_tables'), cf_dla_catalog)

# assembly
cli_command(__name__, 'dla catalog assembly show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_assembly'), cf_dla_catalog)
cli_command(__name__, 'dla catalog assembly list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_assemblies'), cf_dla_catalog)

# external data source
cli_command(__name__, 'dla catalog external-data-source show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_external_data_source'), cf_dla_catalog)
cli_command(__name__, 'dla catalog external-data-source list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_external_data_sources'), cf_dla_catalog)

# get procedure
cli_command(__name__, 'dla catalog procedure show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_procedure'), cf_dla_catalog)
cli_command(__name__, 'dla catalog procedure list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_procedures'), cf_dla_catalog)

# get table partition
cli_command(__name__, 'dla catalog table-partition show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table_partition'), cf_dla_catalog)
cli_command(__name__, 'dla catalog table-partition list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_table_partitions'), cf_dla_catalog)

# get table statistics
cli_command(__name__, 'dla catalog table-stats show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table_statistic'), cf_dla_catalog)
cli_command(__name__, 'dla catalog table-stats list', adla_custom_format_path.format('list_catalog_table_statistics'), cf_dla_catalog)

# get table types
cli_command(__name__, 'dla catalog table-type show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table_type'), cf_dla_catalog)
cli_command(__name__, 'dla catalog table-type list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_table_types'), cf_dla_catalog)

# get table valued functions
cli_command(__name__, 'dla catalog tvf show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table_valued_function'), cf_dla_catalog)
cli_command(__name__, 'dla catalog tvf list', adla_custom_format_path.format('list_catalog_tvfs'), cf_dla_catalog)

# get views
cli_command(__name__, 'dla catalog view show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_view'), cf_dla_catalog)
cli_command(__name__, 'dla catalog view list', adla_custom_format_path.format('list_catalog_views'), cf_dla_catalog)

# get packages
cli_command(__name__, 'dla catalog package show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_package'), cf_dla_catalog)
cli_command(__name__, 'dla catalog package list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_packages'), cf_dla_catalog)
