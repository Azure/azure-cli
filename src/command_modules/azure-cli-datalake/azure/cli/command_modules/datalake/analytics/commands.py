# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.datalake.analytics._client_factory import (cf_datalake_analytics_account,
                                                                          cf_datalake_analytics_account_firewall,
                                                                          cf_datalake_analytics_account_adls,
                                                                          cf_datalake_analytics_account_storage,
                                                                          cf_datalake_analytics_job,
                                                                          cf_datalake_analytics_catalog)
adla_format_path = 'azure.mgmt.datalake.analytics.{}.operations.{}#{}.{}'
adla_custom_format_path = 'azure.cli.command_modules.datalake.analytics.custom#{}'

# account operations
cli_command(__name__, 'datalake analytics account create', adla_custom_format_path.format('create_adla_account'), cf_datalake_analytics_account)
cli_command(__name__, 'datalake analytics account update', adla_custom_format_path.format('update_adla_account'), cf_datalake_analytics_account)
cli_command(__name__, 'datalake analytics account list', adla_custom_format_path.format('list_adla_account'), cf_datalake_analytics_account)
cli_command(__name__, 'datalake analytics account show', adla_format_path.format('account', 'account_operations', 'AccountOperations', 'get'), cf_datalake_analytics_account)
cli_command(__name__, 'datalake analytics account delete', adla_format_path.format('account', 'account_operations', 'AccountOperations', 'delete'), cf_datalake_analytics_account)

# account fire wall operations
# TODO: implement
cli_command(__name__, 'datalake analytics account firewall create', adla_custom_format_path.format('add_adla_firewall_rule'), cf_datalake_analytics_account_firewall)
cli_command(__name__, 'datalake analytics account firewall update', adla_format_path.format('account', 'firewall_rules_operations', 'FirewallRulesOperations', 'update'), cf_datalake_analytics_account_firewall)
cli_command(__name__, 'datalake analytics account firewall list', adla_format_path.format('account', 'firewall_rules_operations', 'FirewallRulesOperations', 'list_by_account'), cf_datalake_analytics_account_firewall)
cli_command(__name__, 'datalake analytics account firewall show', adla_format_path.format('account', 'firewall_rules_operations', 'FirewallRulesOperations', 'get'), cf_datalake_analytics_account_firewall)
cli_command(__name__, 'datalake analytics account firewall delete', adla_format_path.format('account', 'firewall_rules_operations', 'FirewallRulesOperations', 'delete'), cf_datalake_analytics_account_firewall)

# job operations
# todo: update to allow for inclusion of statistics/debug data in show
# todo: add a polling command for jobs
cli_command(__name__, 'datalake analytics job submit', adla_custom_format_path.format('submit_adla_job'), cf_datalake_analytics_job)
cli_command(__name__, 'datalake analytics job wait', adla_custom_format_path.format('wait_adla_job'), cf_datalake_analytics_job)
cli_command(__name__, 'datalake analytics job show', adla_format_path.format('job', 'job_operations', 'JobOperations', 'get'), cf_datalake_analytics_job)
cli_command(__name__, 'datalake analytics job cancel', adla_format_path.format('job', 'job_operations', 'JobOperations', 'cancel'), cf_datalake_analytics_job)
cli_command(__name__, 'datalake analytics job list', adla_format_path.format('job', 'job_operations', 'JobOperations', 'list'), cf_datalake_analytics_job)

# account data source operations
cli_command(__name__, 'datalake analytics account blob show', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'get'), cf_datalake_analytics_account_storage)
cli_command(__name__, 'datalake analytics account blob add', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'add'), cf_datalake_analytics_account_storage)
cli_command(__name__, 'datalake analytics account blob update', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'update'), cf_datalake_analytics_account_storage)
cli_command(__name__, 'datalake analytics account blob delete', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'delete'), cf_datalake_analytics_account_storage)
cli_command(__name__, 'datalake analytics account blob list', adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations', 'list_by_account'), cf_datalake_analytics_account_storage)

cli_command(__name__, 'datalake analytics account datalake-store show', adla_format_path.format('account', 'data_lake_store_accounts_operations', 'DataLakeStoreAccountsOperations', 'get'), cf_datalake_analytics_account_adls)
cli_command(__name__, 'datalake analytics account datalake-store list', adla_format_path.format('account', 'data_lake_store_accounts_operations', 'DataLakeStoreAccountsOperations', 'list_by_account'), cf_datalake_analytics_account_adls)
cli_command(__name__, 'datalake analytics account datalake-store add', adla_format_path.format('account', 'data_lake_store_accounts_operations', 'DataLakeStoreAccountsOperations', 'add'), cf_datalake_analytics_account_adls)
cli_command(__name__, 'datalake analytics account datalake-store delete', adla_format_path.format('account', 'data_lake_store_accounts_operations', 'DataLakeStoreAccountsOperations', 'delete'), cf_datalake_analytics_account_adls)

# catalog operations
#credential
cli_command(__name__, 'datalake analytics catalog credential create', adla_custom_format_path.format('create_adla_catalog_credential'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog credential show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_credential'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog credential update', adla_custom_format_path.format('update_adla_catalog_credential'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog credential list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_credentials'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog credential delete', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'delete_credential'), cf_datalake_analytics_catalog)

# database
cli_command(__name__, 'datalake analytics catalog database show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_database'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog database list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_databases'), cf_datalake_analytics_catalog)

# schema
cli_command(__name__, 'datalake analytics catalog schema show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_schema'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog schema list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_schemas'), cf_datalake_analytics_catalog)

# table
cli_command(__name__, 'datalake analytics catalog table show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog table list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_tables'), cf_datalake_analytics_catalog)

# assembly
cli_command(__name__, 'datalake analytics catalog assembly show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_assembly'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog assembly list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_assemblies'), cf_datalake_analytics_catalog)

# external data source
cli_command(__name__, 'datalake analytics catalog externaldatasource show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_external_data_source'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog externaldatasource list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_external_data_sources'), cf_datalake_analytics_catalog)

# get procedure
cli_command(__name__, 'datalake analytics catalog procedure show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_procedure'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog procedure list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_procedures'), cf_datalake_analytics_catalog)

# get table partition
cli_command(__name__, 'datalake analytics catalog tablepartition show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table_partition'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog tablepartition list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_table_partitions'), cf_datalake_analytics_catalog)

# get table statistics
cli_command(__name__, 'datalake analytics catalog tablestats show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table_statistic'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog tablestats list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_table_statistics'), cf_datalake_analytics_catalog)

# get table types
cli_command(__name__, 'datalake analytics catalog tabletype show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table_type'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog tabletype list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_table_types'), cf_datalake_analytics_catalog)

# get table valued functions
cli_command(__name__, 'datalake analytics catalog tablevaluedfunction show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_table_valued_function'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog tablevaluedfunction list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_table_valued_functions'), cf_datalake_analytics_catalog)

# get views
cli_command(__name__, 'datalake analytics catalog view show', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'get_view'), cf_datalake_analytics_catalog)
cli_command(__name__, 'datalake analytics catalog view list', adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations', 'list_views'), cf_datalake_analytics_catalog)
