# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.command_modules.batchai._client_factory import (
    batchai_client_factory,
    cluster_client_factory,
    job_client_factory,
    file_client_factory,
    file_server_client_factory)
from azure.cli.command_modules.batchai._format import (
    cluster_list_table_format,
    job_list_table_format,
    file_list_table_format,
    file_server_table_format,
    remote_login_table_format,
)
from azure.cli.core.commands import cli_command

custom_path = 'azure.cli.command_modules.batchai.custom#{}'
mgmt_path = 'azure.mgmt.batchai.operations.{}_operations#{}.{}'

cli_command(__name__, 'batchai cluster create', custom_path.format('create_cluster'), batchai_client_factory, no_wait_param='raw')
cli_command(__name__, 'batchai cluster delete', mgmt_path.format('clusters', 'ClustersOperations', 'delete'), cluster_client_factory, confirmation=True, no_wait_param='raw')
cli_command(__name__, 'batchai cluster show', mgmt_path.format('clusters', 'ClustersOperations', 'get'), cluster_client_factory)
cli_command(__name__, 'batchai cluster list', custom_path.format('list_clusters'), cluster_client_factory, table_transformer=cluster_list_table_format)
cli_command(__name__, 'batchai cluster list-nodes', mgmt_path.format('clusters', 'ClustersOperations', 'list_remote_login_information'), cluster_client_factory, table_transformer=remote_login_table_format)
cli_command(__name__, 'batchai cluster resize', custom_path.format('resize_cluster'), cluster_client_factory)
cli_command(__name__, 'batchai cluster auto-scale', custom_path.format('set_cluster_auto_scale_parameters'), cluster_client_factory)

cli_command(__name__, 'batchai job create', custom_path.format('create_job'), batchai_client_factory, no_wait_param='raw')
cli_command(__name__, 'batchai job delete', mgmt_path.format('jobs', 'JobsOperations', 'delete'), job_client_factory, confirmation=True, no_wait_param='raw')
cli_command(__name__, 'batchai job terminate', mgmt_path.format('jobs', 'JobsOperations', 'terminate'), job_client_factory, no_wait_param='raw')
cli_command(__name__, 'batchai job show', mgmt_path.format('jobs', 'JobsOperations', 'get'), job_client_factory)
cli_command(__name__, 'batchai job list', custom_path.format('list_jobs'), job_client_factory, table_transformer=job_list_table_format)
cli_command(__name__, 'batchai job list-nodes', mgmt_path.format('jobs', 'JobsOperations', 'list_remote_login_information'), job_client_factory, table_transformer=remote_login_table_format)
cli_command(__name__, 'batchai job list-files', custom_path.format('list_files'), file_client_factory, table_transformer=file_list_table_format)
cli_command(__name__, 'batchai job stream-file', custom_path.format('tail_file'), file_client_factory)

cli_command(__name__, 'batchai file-server create', custom_path.format('create_file_server'), file_server_client_factory, no_wait_param='raw')
cli_command(__name__, 'batchai file-server delete', mgmt_path.format('file_servers', 'FileServersOperations', 'delete'), file_server_client_factory, confirmation=True, no_wait_param='raw')
cli_command(__name__, 'batchai file-server show', mgmt_path.format('file_servers', 'FileServersOperations', 'get'), file_server_client_factory)
cli_command(__name__, 'batchai file-server list', custom_path.format('list_file_servers'), file_server_client_factory, table_transformer=file_server_table_format)
