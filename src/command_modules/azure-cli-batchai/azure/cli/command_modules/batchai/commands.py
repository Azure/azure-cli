# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.command_modules.batchai._client_factory import (
    batchai_client_factory,
    cluster_client_factory,
    job_client_factory,
    file_server_client_factory,
    usage_client_factory)
from azure.cli.command_modules.batchai._format import (
    cluster_list_table_format,
    cluster_show_table_format,
    job_list_table_format,
    job_show_table_format,
    file_list_table_format,
    file_server_list_table_format,
    file_server_show_table_format,
    remote_login_table_format,
    node_setup_files_list_table_format,
    usage_table_format)
from azure.cli.core.commands import CliCommandType

custom_path = 'azure.cli.command_modules.batchai.custom#{}'

batchai_cluster_sdk = CliCommandType(
    operations_tmpl='azure.mgmt.batchai.operations.clusters_operations#ClustersOperations.{}',
    client_factory=cluster_client_factory)

batchai_job_sdk = CliCommandType(
    operations_tmpl='azure.mgmt.batchai.operations.jobs_operations#JobsOperations.{}',
    client_factory=job_client_factory)

batchai_server_sdk = CliCommandType(
    operations_tmpl='azure.mgmt.batchai.operations.file_servers_operations#FileServersOperations.{}',
    client_factory=file_server_client_factory)

batchai_usage_sdk = CliCommandType(
    operations_tmpl='azure.mgmt.batchai.operations.usage_operations#UsageOperations.{}',
    client_factory=usage_client_factory)


def load_command_table(self, _):

    with self.command_group('batchai cluster', batchai_cluster_sdk, client_factory=cluster_client_factory) as g:
        g.custom_command('create', 'create_cluster', client_factory=batchai_client_factory)
        g.command('delete', 'delete', supports_no_wait=True, confirmation=True)
        g.command('show', 'get', table_transformer=cluster_show_table_format)
        g.custom_command('list', 'list_clusters', table_transformer=cluster_list_table_format)
        g.command('list-nodes', 'list_remote_login_information', table_transformer=remote_login_table_format)
        g.custom_command('resize', 'resize_cluster')
        g.custom_command('auto-scale', 'set_cluster_auto_scale_parameters')
        g.custom_command('list-files', 'list_node_setup_files', table_transformer=node_setup_files_list_table_format)

    with self.command_group('batchai job', batchai_job_sdk, client_factory=job_client_factory) as g:
        g.custom_command('create', 'create_job', client_factory=batchai_client_factory)
        g.command('delete', 'delete', supports_no_wait=True, confirmation=True)
        g.command('terminate', 'terminate', supports_no_wait=True, confirmation=True)
        g.command('show', 'get', table_transformer=job_show_table_format)
        g.custom_command('list', 'list_jobs', table_transformer=job_list_table_format)
        g.command('list-nodes', 'list_remote_login_information', table_transformer=remote_login_table_format)
        g.custom_command('wait', 'wait_for_job_completion', client_factory=batchai_client_factory)

    with self.command_group('batchai job file', batchai_job_sdk, client_factory=job_client_factory) as g:
        g.custom_command('list', 'list_files', table_transformer=file_list_table_format)
        g.custom_command('stream', 'tail_file')

    with self.command_group('batchai file-server', batchai_server_sdk, client_factory=file_server_client_factory) as g:
        g.custom_command('create', 'create_file_server', no_wait_param='raw')
        g.command('delete', 'delete', supports_no_wait=True, confirmation=True)
        g.command('show', 'get', table_transformer=file_server_show_table_format)
        g.custom_command('list', 'list_file_servers', table_transformer=file_server_list_table_format)

    with self.command_group('batchai', batchai_usage_sdk, client_factory=usage_client_factory) as g:
        g.command('list-usages', 'list', table_transformer=usage_table_format)
