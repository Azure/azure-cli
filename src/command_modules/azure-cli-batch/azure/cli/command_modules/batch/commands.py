# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

from ._client_factory import batch_client_factory, batch_data_service_factory
from ._command_type import cli_data_plane_command
from ._validators import validate_pool_settings

data_path = 'azure.batch.operations.{}_operations#{}'
custom_path = 'azure.cli.command_modules.batch.custom#{}'
mgmt_path = 'azure.mgmt.batch.operations.{}_operations#{}'

# pylint: disable=line-too-long
# Mgmt Account Operations

factory = lambda args: batch_client_factory(**args).batch_account
cli_command(__name__, 'batch account list', custom_path.format('list_accounts'), factory)
cli_command(__name__, 'batch account show', mgmt_path.format('batch_account', 'BatchAccountOperations.get'), factory)
cli_command(__name__, 'batch account create', custom_path.format('create_account'), factory)
cli_command(__name__, 'batch account set', custom_path.format('update_account'), factory)
cli_command(__name__, 'batch account delete', mgmt_path.format('batch_account', 'BatchAccountOperations.delete'), factory, confirmation=True)
cli_command(__name__, 'batch account autostorage-keys sync', mgmt_path.format('batch_account', 'BatchAccountOperations.synchronize_auto_storage_keys'), factory)

cli_command(__name__, 'batch account keys list', mgmt_path.format('batch_account', 'BatchAccountOperations.get_keys'), factory)
cli_command(__name__, 'batch account keys renew', mgmt_path.format('batch_account', 'BatchAccountOperations.regenerate_key'), factory)

factory = lambda args: batch_client_factory(**args).application
cli_command(__name__, 'batch application list', mgmt_path.format('application', 'ApplicationOperations.list'), factory)
cli_command(__name__, 'batch application show', mgmt_path.format('application', 'ApplicationOperations.get'), factory)
cli_command(__name__, 'batch application create', mgmt_path.format('application', 'ApplicationOperations.create'), factory)
cli_command(__name__, 'batch application set', custom_path.format('update_application'), factory)
cli_command(__name__, 'batch application delete', mgmt_path.format('application', 'ApplicationOperations.delete'), factory)

factory = lambda args: batch_client_factory(**args).application_package
cli_command(__name__, 'batch application package create', custom_path.format('create_application_package'), factory)
cli_command(__name__, 'batch application package delete', mgmt_path.format('application_package', 'ApplicationPackageOperations.delete'), factory)
cli_command(__name__, 'batch application package show', mgmt_path.format('application_package', 'ApplicationPackageOperations.get'), factory)
cli_command(__name__, 'batch application package activate', mgmt_path.format('application_package', 'ApplicationPackageOperations.activate'), factory)

factory = lambda args: batch_client_factory(**args).location
cli_command(__name__, 'batch location quotas show', mgmt_path.format('location', 'LocationOperations.get_quotas'), factory)

# Data Plane Commands

factory = lambda args: batch_data_service_factory(args).application
cli_data_plane_command('batch application summary list', data_path.format('application', 'ApplicationOperations.list'), factory)
cli_data_plane_command('batch application summary show', data_path.format('application', 'ApplicationOperations.get'), factory)

factory = lambda args: batch_data_service_factory(args).account
cli_data_plane_command('batch pool node-agent-skus list', data_path.format('account', 'AccountOperations.list_node_agent_skus'), factory)

factory = lambda args: batch_data_service_factory(args).certificate
cli_command(__name__, 'batch certificate create', custom_path.format('create_certificate'), factory)
cli_command(__name__, 'batch certificate delete', custom_path.format('delete_certificate'), factory, confirmation=True)
cli_data_plane_command('batch certificate show', data_path.format('certificate', 'CertificateOperations.get'), factory)
cli_data_plane_command('batch certificate list', data_path.format('certificate', 'CertificateOperations.list'), factory)

factory = lambda args: batch_data_service_factory(args).pool
cli_data_plane_command('batch pool usage-metrics list', data_path.format('pool', 'PoolOperations.list_pool_usage_metrics'), factory)
cli_data_plane_command('batch pool all-stats show', data_path.format('pool', 'PoolOperations.get_all_pools_lifetime_statistics'), factory)
cli_data_plane_command('batch pool create', data_path.format('pool', 'PoolOperations.add'), factory, validator=validate_pool_settings)
cli_data_plane_command('batch pool list', data_path.format('pool', 'PoolOperations.list'), factory)
cli_data_plane_command('batch pool delete', data_path.format('pool', 'PoolOperations.delete'), factory)
cli_data_plane_command('batch pool show', data_path.format('pool', 'PoolOperations.get'), factory)
cli_data_plane_command('batch pool set', data_path.format('pool', 'PoolOperations.patch'), factory)
cli_command(__name__, 'batch pool reset', custom_path.format('update_pool'), factory)
cli_data_plane_command('batch pool autoscale disable', data_path.format('pool', 'PoolOperations.disable_auto_scale'), factory)
cli_data_plane_command('batch pool autoscale enable', data_path.format('pool', 'PoolOperations.enable_auto_scale'), factory)
cli_data_plane_command('batch pool autoscale evaluate', data_path.format('pool', 'PoolOperations.evaluate_auto_scale'), factory)
cli_command(__name__, 'batch pool resize', custom_path.format('resize_pool'), factory)
cli_data_plane_command('batch pool os upgrade', data_path.format('pool', 'PoolOperations.upgrade_os'), factory)
cli_data_plane_command('batch node delete', data_path.format('pool', 'PoolOperations.remove_nodes'), factory)

factory = lambda args: batch_data_service_factory(args).job
cli_data_plane_command('batch job all-stats show', data_path.format('job', 'JobOperations.get_all_jobs_lifetime_statistics'), factory)
cli_data_plane_command('batch job create', data_path.format('job', 'JobOperations.add'), factory)
cli_data_plane_command('batch job delete', data_path.format('job', 'JobOperations.delete'), factory)
cli_data_plane_command('batch job show', data_path.format('job', 'JobOperations.get'), factory)
cli_data_plane_command('batch job set', data_path.format('job', 'JobOperations.patch'), factory)
cli_data_plane_command('batch job reset', data_path.format('job', 'JobOperations.update'), factory)
cli_command(__name__, 'batch job list', custom_path.format('list_job'), factory)
cli_data_plane_command('batch job disable', data_path.format('job', 'JobOperations.disable'), factory)
cli_data_plane_command('batch job enable', data_path.format('job', 'JobOperations.enable'), factory)
cli_data_plane_command('batch job stop', data_path.format('job', 'JobOperations.terminate'), factory)
cli_data_plane_command('batch job prep-release-status list', data_path.format('job', 'JobOperations.list_preparation_and_release_task_status'), factory)

factory = lambda args: batch_data_service_factory(args).job_schedule
cli_data_plane_command('batch job-schedule create', data_path.format('job_schedule', 'JobScheduleOperations.add'), factory)
cli_data_plane_command('batch job-schedule delete', data_path.format('job_schedule', 'JobScheduleOperations.delete'), factory)
cli_data_plane_command('batch job-schedule show', data_path.format('job_schedule', 'JobScheduleOperations.get'), factory)
cli_data_plane_command('batch job-schedule set', data_path.format('job_schedule', 'JobScheduleOperations.patch'), factory)
cli_data_plane_command('batch job-schedule reset', data_path.format('job_schedule', 'JobScheduleOperations.update'), factory)
cli_data_plane_command('batch job-schedule disable', data_path.format('job_schedule', 'JobScheduleOperations.disable'), factory)
cli_data_plane_command('batch job-schedule enable', data_path.format('job_schedule', 'JobScheduleOperations.enable'), factory)
cli_data_plane_command('batch job-schedule stop', data_path.format('job_schedule', 'JobScheduleOperations.terminate'), factory)
cli_data_plane_command('batch job-schedule list', data_path.format('job_schedule', 'JobScheduleOperations.list'), factory)

factory = lambda args: batch_data_service_factory(args).task
cli_command(__name__, 'batch task create', custom_path.format('create_task'), factory)
cli_data_plane_command('batch task list', data_path.format('task', 'TaskOperations.list'), factory)
cli_data_plane_command('batch task delete', data_path.format('task', 'TaskOperations.delete'), factory)
cli_data_plane_command('batch task show', data_path.format('task', 'TaskOperations.get'), factory)
cli_data_plane_command('batch task reset', data_path.format('task', 'TaskOperations.update'), factory)
cli_data_plane_command('batch task reactivate', data_path.format('task', 'TaskOperations.reactivate'), factory)
cli_data_plane_command('batch task stop', data_path.format('task', 'TaskOperations.terminate'), factory)
cli_data_plane_command('batch task subtask list', data_path.format('task', 'TaskOperations.list_subtasks'), factory)

factory = lambda args: batch_data_service_factory(args).file
cli_data_plane_command('batch task file delete', data_path.format('file', 'FileOperations.delete_from_task'), factory)
cli_data_plane_command('batch task file download', data_path.format('file', 'FileOperations.get_from_task'), factory)
cli_data_plane_command('batch task file show', data_path.format('file', 'FileOperations.get_node_file_properties_from_task'), factory)
cli_data_plane_command('batch task file list', data_path.format('file', 'FileOperations.list_from_task'), factory)

factory = lambda args: batch_data_service_factory(args).compute_node
cli_data_plane_command('batch node-user create', data_path.format('compute_node', 'ComputeNodeOperations.add_user'), factory)
cli_data_plane_command('batch node-user delete', data_path.format('compute_node', 'ComputeNodeOperations.delete_user'), factory)
cli_data_plane_command('batch node-user set', data_path.format('compute_node', 'ComputeNodeOperations.update_user'), factory)
cli_data_plane_command('batch node show', data_path.format('compute_node', 'ComputeNodeOperations.get'), factory)
cli_data_plane_command('batch node list', data_path.format('compute_node', 'ComputeNodeOperations.list'), factory)
cli_data_plane_command('batch node reboot', data_path.format('compute_node', 'ComputeNodeOperations.reboot'), factory)
cli_data_plane_command('batch node reimage', data_path.format('compute_node', 'ComputeNodeOperations.reimage'), factory)
cli_data_plane_command('batch node scheduling disable', data_path.format('compute_node', 'ComputeNodeOperations.disable_scheduling'), factory)
cli_data_plane_command('batch node scheduling enable', data_path.format('compute_node', 'ComputeNodeOperations.enable_scheduling'), factory)
cli_data_plane_command('batch node remote-login-settings show', data_path.format('compute_node', 'ComputeNodeOperations.get_remote_login_settings'), factory)
cli_data_plane_command('batch node remote-desktop show', data_path.format('compute_node', 'ComputeNodeOperations.get_remote_desktop'), factory)

factory = lambda args: batch_data_service_factory(args).file
cli_data_plane_command('batch node file delete', data_path.format('file', 'FileOperations.delete_from_compute_node'), factory)
cli_data_plane_command('batch node file download', data_path.format('file', 'FileOperations.get_from_compute_node'), factory)
cli_data_plane_command('batch node file show', data_path.format('file', 'FileOperations.get_node_file_properties_from_compute_node'), factory)
cli_data_plane_command('batch node file list', data_path.format('file', 'FileOperations.list_from_compute_node'), factory)
