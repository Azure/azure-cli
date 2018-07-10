# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.dla._client_factory import (
    cf_dla_account,
    cf_dla_account_firewall,
    cf_dla_account_adls,
    cf_dla_account_storage,
    cf_dla_job,
    cf_dla_catalog,
    cf_dla_job_pipeline,
    cf_dla_job_recurrence,
    cf_dla_account_compute_policy)
from azure.cli.command_modules.dla._validators import process_dla_job_submit_namespace


# pylint: disable=too-many-statements
def load_command_table(self, _):

    adla_format_path = 'azure.mgmt.datalake.analytics.{}.operations.{}#{}.{{}}'

    dla_account_sdk = CliCommandType(
        operations_tmpl=adla_format_path.format('account', 'account_operations', 'AccountOperations'),
        client_factory=cf_dla_account)

    dla_firewall_sdk = CliCommandType(
        operations_tmpl=adla_format_path.format('account', 'firewall_rules_operations', 'FirewallRulesOperations'),
        client_factory=cf_dla_account_firewall)

    dla_job_sdk = CliCommandType(
        operations_tmpl=adla_format_path.format('job', 'job_operations', 'JobOperations'),
        client_factory=cf_dla_job)

    dla_job_pipeline_sdk = CliCommandType(
        operations_tmpl=adla_format_path.format('job', 'pipeline_operations', 'PipelineOperations'),
        client_factory=cf_dla_job_pipeline)

    dla_job_recurrence_sdk = CliCommandType(
        operations_tmpl=adla_format_path.format('job', 'recurrence_operations', 'RecurrenceOperations'),
        client_factory=cf_dla_job_recurrence)

    dla_storage_sdk = CliCommandType(
        operations_tmpl=adla_format_path.format('account', 'storage_accounts_operations', 'StorageAccountsOperations'),
        client_factory=cf_dla_account_storage)

    dla_dls_sdk = CliCommandType(
        operations_tmpl=adla_format_path.format('account', 'data_lake_store_accounts_operations', 'DataLakeStoreAccountsOperations'),
        client_factory=cf_dla_account_adls
    )

    dla_catalog_sdk = CliCommandType(
        operations_tmpl=adla_format_path.format('catalog', 'catalog_operations', 'CatalogOperations'),
        client_factory=cf_dla_catalog
    )

    dla_compute_policy_sdk = CliCommandType(
        operations_tmpl=adla_format_path.format('account', 'compute_policies_operations', 'ComputePoliciesOperations'),
        client_factory=cf_dla_account_compute_policy
    )

    # account operations
    with self.command_group('dla account', dla_account_sdk, client_factory=cf_dla_account) as g:
        g.custom_command('create', 'create_adla_account')
        g.custom_command('update', 'update_adla_account')
        g.custom_command('list', 'list_adla_account')
        g.show_command('show', 'get')
        g.command('delete', 'delete')

    # account fire wall operations
    with self.command_group('dla account firewall', dla_firewall_sdk, client_factory=cf_dla_account_firewall) as g:
        g.custom_command('create', 'add_adla_firewall_rule')
        g.command('update', 'update')
        g.command('list', 'list_by_account')
        g.show_command('show', 'get')
        g.command('delete', 'delete')

    # job operations
    # todo: update to allow for inclusion of statistics/debug data in show
    with self.command_group('dla job', dla_job_sdk, client_factory=cf_dla_job) as g:
        g.custom_command('submit', 'submit_adla_job', validator=process_dla_job_submit_namespace)
        g.custom_command('wait', 'wait_adla_job')
        g.show_command('show', 'get')
        g.command('cancel', 'cancel')
        g.custom_command('list', 'list_adla_jobs')

    # job relationship operations
    with self.command_group('dla job pipeline', dla_job_pipeline_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')

    with self.command_group('dla job recurrence', dla_job_recurrence_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')

    # account data source operations
    with self.command_group('dla account blob-storage', dla_storage_sdk, client_factory=cf_dla_account_storage) as g:
        g.show_command('show', 'get')
        g.custom_command('add', 'add_adla_blob_storage')
        g.custom_command('update', 'update_adla_blob_storage')
        g.command('delete', 'delete')
        g.command('list', 'list_by_account')

    with self.command_group('dla account data-lake-store', dla_dls_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_account')
        g.command('add', 'add')
        g.command('delete', 'delete')

    # catalog operations
    # credential
    with self.command_group('dla catalog credential', dla_catalog_sdk, client_factory=cf_dla_catalog) as g:
        g.custom_command('create', 'create_adla_catalog_credential')
        g.show_command('show', 'get_credential')
        g.custom_command('update', 'update_adla_catalog_credential')
        g.command('list', 'list_credentials')
        g.command('delete', 'delete_credential')

    # database
    with self.command_group('dla catalog database', dla_catalog_sdk) as g:
        g.show_command('show', 'get_database')
        g.command('list', 'list_databases')

    # schema
    with self.command_group('dla catalog schema', dla_catalog_sdk) as g:
        g.show_command('show', 'get_schema')
        g.command('list', 'list_schemas')

    # table
    with self.command_group('dla catalog table', dla_catalog_sdk, client_factory=cf_dla_catalog) as g:
        g.show_command('show', 'get_table')
        g.custom_command('list', 'list_catalog_tables')

    # assembly
    with self.command_group('dla catalog assembly', dla_catalog_sdk) as g:
        g.show_command('show', 'get_assembly')
        g.command('list', 'list_assemblies')

    # external data source
    with self.command_group('dla catalog external-data-source', dla_catalog_sdk) as g:
        g.show_command('show', 'get_external_data_source')
        g.command('list', 'list_external_data_sources')

    # get procedure
    with self.command_group('dla catalog procedure', dla_catalog_sdk) as g:
        g.show_command('show', 'get_procedure')
        g.command('list', 'list_procedures')

    # get table partition
    with self.command_group('dla catalog table-partition', dla_catalog_sdk) as g:
        g.show_command('show', 'get_table_partition')
        g.command('list', 'list_table_partitions')

    # get table statistics
    with self.command_group('dla catalog table-stats', dla_catalog_sdk, client_factory=cf_dla_catalog) as g:
        g.show_command('show', 'get_table_statistic')
        g.custom_command('list', 'list_catalog_table_statistics')

    # get table types
    with self.command_group('dla catalog table-type', dla_catalog_sdk) as g:
        g.show_command('show', 'get_table_type')
        g.command('list', 'list_table_types')

    # get table valued functions
    with self.command_group('dla catalog tvf', dla_catalog_sdk, client_factory=cf_dla_catalog) as g:
        g.show_command('show', 'get_table_valued_function')
        g.custom_command('list', 'list_catalog_tvfs')

    # get views
    with self.command_group('dla catalog view', dla_catalog_sdk, client_factory=cf_dla_catalog) as g:
        g.show_command('show', 'get_view')
        g.custom_command('list', 'list_catalog_views')

    # get packages
    with self.command_group('dla catalog package', dla_catalog_sdk) as g:
        g.show_command('show', 'get_package')
        g.command('list', 'list_packages')

    # compute policy
    with self.command_group('dla account compute-policy', dla_compute_policy_sdk, client_factory=cf_dla_account_compute_policy) as g:
        g.custom_command('create', 'create_adla_compute_policy')
        g.custom_command('update', 'update_adla_compute_policy')
        g.command('list', 'list_by_account')
        g.show_command('show', 'get')
        g.command('delete', 'delete')
