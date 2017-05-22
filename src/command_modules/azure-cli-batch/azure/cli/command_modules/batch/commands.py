# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

from azure.cli.command_modules.batch._command_type import cli_batch_data_plane_command
from azure.cli.command_modules.batch._validators import (
    validate_pool_settings, validate_cert_settings)
from azure.cli.command_modules.batch._client_factory import (
    account_mgmt_client_factory,
    account_client_factory,
    application_mgmt_client_factory,
    application_package_client_factory,
    application_client_factory,
    certificate_client_factory,
    compute_node_client_factory,
    file_client_factory,
    job_client_factory,
    job_schedule_client_factory,
    location_client_factory,
    pool_client_factory,
    task_client_factory)
from azure.cli.command_modules.batch._format import (
    job_list_table_format,
    task_create_table_format,
    account_keys_list_table_format,
    account_list_table_format,
    application_list_table_format,
    account_keys_renew_table_format)


data_path = 'azure.batch.operations.{}_operations#{}'
custom_path = 'azure.cli.command_modules.batch.custom#{}'
mgmt_path = 'azure.mgmt.batch.operations.{}_operations#{}'

# pylint: disable=line-too-long
# Mgmt Account Operations

cli_command(__name__, 'batch account list', custom_path.format('list_accounts'), account_mgmt_client_factory, table_transformer=account_list_table_format)
cli_command(__name__, 'batch account show', mgmt_path.format('batch_account', 'BatchAccountOperations.get'), account_mgmt_client_factory)
cli_command(__name__, 'batch account create', custom_path.format('create_account'), account_mgmt_client_factory)
cli_command(__name__, 'batch account set', custom_path.format('update_account'), account_mgmt_client_factory)
cli_command(__name__, 'batch account delete', mgmt_path.format('batch_account', 'BatchAccountOperations.delete'), account_mgmt_client_factory, confirmation=True)
cli_command(__name__, 'batch account autostorage-keys sync', mgmt_path.format('batch_account', 'BatchAccountOperations.synchronize_auto_storage_keys'), account_mgmt_client_factory)
cli_command(__name__, 'batch account keys list', mgmt_path.format('batch_account', 'BatchAccountOperations.get_keys'), account_mgmt_client_factory, table_transformer=account_keys_list_table_format)
cli_command(__name__, 'batch account keys renew', mgmt_path.format('batch_account', 'BatchAccountOperations.regenerate_key'), account_mgmt_client_factory, table_transformer=account_keys_renew_table_format)
cli_command(__name__, 'batch account login', custom_path.format('login_account'), account_mgmt_client_factory)

cli_command(__name__, 'batch application list', mgmt_path.format('application', 'ApplicationOperations.list'), application_mgmt_client_factory, table_transformer=application_list_table_format)
cli_command(__name__, 'batch application show', mgmt_path.format('application', 'ApplicationOperations.get'), application_mgmt_client_factory)
cli_command(__name__, 'batch application create', mgmt_path.format('application', 'ApplicationOperations.create'), application_mgmt_client_factory)
cli_command(__name__, 'batch application set', custom_path.format('update_application'), application_mgmt_client_factory)
cli_command(__name__, 'batch application delete', mgmt_path.format('application', 'ApplicationOperations.delete'), application_mgmt_client_factory, confirmation=True)

cli_command(__name__, 'batch application package create', custom_path.format('create_application_package'), application_package_client_factory)
cli_command(__name__, 'batch application package delete', mgmt_path.format('application_package', 'ApplicationPackageOperations.delete'), application_package_client_factory, confirmation=True)
cli_command(__name__, 'batch application package show', mgmt_path.format('application_package', 'ApplicationPackageOperations.get'), application_package_client_factory)
cli_command(__name__, 'batch application package activate', mgmt_path.format('application_package', 'ApplicationPackageOperations.activate'), application_package_client_factory)

cli_command(__name__, 'batch location quotas show', mgmt_path.format('location', 'LocationOperations.get_quotas'), location_client_factory)

# Data Plane Commands

cli_batch_data_plane_command('batch application summary list', data_path.format('application', 'ApplicationOperations.list'), application_client_factory)
cli_batch_data_plane_command('batch application summary show', data_path.format('application', 'ApplicationOperations.get'), application_client_factory)

cli_batch_data_plane_command('batch pool node-agent-skus list', data_path.format('account', 'AccountOperations.list_node_agent_skus'), account_client_factory)

cli_command(__name__, 'batch certificate create', custom_path.format('create_certificate'), certificate_client_factory)
cli_command(__name__, 'batch certificate delete', custom_path.format('delete_certificate'), certificate_client_factory, confirmation=True)
cli_batch_data_plane_command('batch certificate show', data_path.format('certificate', 'CertificateOperations.get'), certificate_client_factory, validator=validate_cert_settings)
cli_batch_data_plane_command('batch certificate list', data_path.format('certificate', 'CertificateOperations.list'), certificate_client_factory)

cli_batch_data_plane_command('batch pool usage-metrics list', data_path.format('pool', 'PoolOperations.list_usage_metrics'), pool_client_factory)
cli_batch_data_plane_command('batch pool all-statistics show', data_path.format('pool', 'PoolOperations.get_all_lifetime_statistics'), pool_client_factory)
cli_batch_data_plane_command('batch pool create', data_path.format('pool', 'PoolOperations.add'), pool_client_factory, validator=validate_pool_settings,
                             ignore=['pool.cloud_service_configuration.current_os_version', 'pool.virtual_machine_configuration.windows_configuration',
                                     'pool.auto_scale_evaluation_interval', 'pool.enable_auto_scale', 'pool.max_tasks_per_node', 'pool.network_configuration',
                                     'pool.cloud_service_configuration.target_os_version', 'pool.task_scheduling_policy', 'pool.virtual_machine_configuration.os_disk',
                                     'pool.start_task.max_task_retry_count', 'pool.start_task.environment_settings', 'pool.start_task.user_identity'],
                             silent=['pool.virtual_machine_configuration.image_reference'])
cli_batch_data_plane_command('batch pool list', data_path.format('pool', 'PoolOperations.list'), pool_client_factory)
cli_batch_data_plane_command('batch pool delete', data_path.format('pool', 'PoolOperations.delete'), pool_client_factory)
cli_batch_data_plane_command('batch pool show', data_path.format('pool', 'PoolOperations.get'), pool_client_factory)
cli_batch_data_plane_command('batch pool set', data_path.format('pool', 'PoolOperations.patch'), pool_client_factory,
                             ignore=['pool_patch_parameter.start_task.user_identity'])
cli_command(__name__, 'batch pool reset', custom_path.format('update_pool'), pool_client_factory)
cli_batch_data_plane_command('batch pool autoscale disable', data_path.format('pool', 'PoolOperations.disable_auto_scale'), pool_client_factory)
cli_batch_data_plane_command('batch pool autoscale enable', data_path.format('pool', 'PoolOperations.enable_auto_scale'), pool_client_factory)
cli_batch_data_plane_command('batch pool autoscale evaluate', data_path.format('pool', 'PoolOperations.evaluate_auto_scale'), pool_client_factory)
cli_command(__name__, 'batch pool resize', custom_path.format('resize_pool'), pool_client_factory)
cli_batch_data_plane_command('batch pool os upgrade', data_path.format('pool', 'PoolOperations.upgrade_os'), pool_client_factory)
cli_batch_data_plane_command('batch node delete', data_path.format('pool', 'PoolOperations.remove_nodes'), pool_client_factory)

cli_batch_data_plane_command('batch job all-statistics show', data_path.format('job', 'JobOperations.get_all_lifetime_statistics'), job_client_factory)
cli_batch_data_plane_command('batch job create', data_path.format('job', 'JobOperations.add'), job_client_factory,
                             ignore=['job.job_preparation_task', 'job.job_release_task', 'job.pool_info.auto_pool_specification', 'job.on_task_failure',
                                     'job.job_manager_task.kill_job_on_completion', 'job.common_environment_settings', 'job.on_all_tasks_complete',
                                     'job.job_manager_task.run_exclusive', 'job.job_manager_task.constraints', 'job.job_manager_task.application_package_references',
                                     'job.job_manager_task.user_identity', 'job.job_manager_task.allow_low_priority_node'])
cli_batch_data_plane_command('batch job delete', data_path.format('job', 'JobOperations.delete'), job_client_factory)
cli_batch_data_plane_command('batch job show', data_path.format('job', 'JobOperations.get'), job_client_factory)
cli_batch_data_plane_command('batch job set', data_path.format('job', 'JobOperations.patch'), job_client_factory, flatten=2)
cli_batch_data_plane_command('batch job reset', data_path.format('job', 'JobOperations.update'), job_client_factory, flatten=2)
cli_command(__name__, 'batch job list', custom_path.format('list_job'), job_client_factory, table_transformer=job_list_table_format)
cli_batch_data_plane_command('batch job disable', data_path.format('job', 'JobOperations.disable'), job_client_factory)
cli_batch_data_plane_command('batch job enable', data_path.format('job', 'JobOperations.enable'), job_client_factory)
cli_batch_data_plane_command('batch job stop', data_path.format('job', 'JobOperations.terminate'), job_client_factory)
cli_batch_data_plane_command('batch job prep-release-status list', data_path.format('job', 'JobOperations.list_preparation_and_release_task_status'), job_client_factory)

cli_batch_data_plane_command('batch job-schedule create', data_path.format('job_schedule', 'JobScheduleOperations.add'), job_schedule_client_factory,
                             ignore=['cloud_job_schedule.job_specification.job_preparation_task', 'cloud_job_schedule.job_specification.on_task_failure',
                                     'cloud_job_schedule.job_specification.job_release_task', 'cloud_job_schedule.job_specification.metadata',
                                     'cloud_job_schedule.job_specification.job_manager_task.kill_job_on_completion',
                                     'cloud_job_schedule.job_specification.job_manager_task.run_exclusive',
                                     'cloud_job_schedule.job_specification.job_manager_task.application_package_references',
                                     'cloud_job_schedule.job_specification.job_manager_task.environment_settings',
                                     'cloud_job_schedule.job_specification.job_manager_task.allow_low_priority_node'])
cli_batch_data_plane_command('batch job-schedule delete', data_path.format('job_schedule', 'JobScheduleOperations.delete'), job_schedule_client_factory)
cli_batch_data_plane_command('batch job-schedule show', data_path.format('job_schedule', 'JobScheduleOperations.get'), job_schedule_client_factory)
cli_batch_data_plane_command('batch job-schedule set', data_path.format('job_schedule', 'JobScheduleOperations.patch'), job_schedule_client_factory,
                             ignore=['job_schedule_patch_parameter.job_specification.job_preparation_task',
                                     'job_schedule_patch_parameter.job_specification.job_release_task',
                                     'job_schedule_patch_parameter.job_specification.constraints',
                                     'job_schedule_patch_parameter.job_specification.on_task_failure',
                                     'job_schedule_patch_parameter.job_specification.job_manager_task.kill_job_on_completion',
                                     'job_schedule_patch_parameter.job_specification.job_manager_task.run_exclusive',
                                     'job_schedule_patch_parameter.job_specification.job_manager_task.constraints',
                                     'job_schedule_patch_parameter.job_specification.job_manager_task.allow_low_priority_node'])
cli_batch_data_plane_command('batch job-schedule reset', data_path.format('job_schedule', 'JobScheduleOperations.update'), job_schedule_client_factory,
                             ignore=['job_schedule_update_parameter.job_specification.job_preparation_task',
                                     'job_schedule_update_parameter.job_specification.job_release_task',
                                     'job_schedule_update_parameter.job_specification.constraints',
                                     'job_schedule_update_parameter.job_specification.on_task_failure',
                                     'job_schedule_update_parameter.job_specification.job_manager_task.kill_job_on_completion',
                                     'job_schedule_update_parameter.job_specification.job_manager_task.run_exclusive',
                                     'job_schedule_update_parameter.job_specification.job_manager_task.constraints',
                                     'job_schedule_update_parameter.job_specification.job_manager_task.allow_low_priority_node'])
cli_batch_data_plane_command('batch job-schedule disable', data_path.format('job_schedule', 'JobScheduleOperations.disable'), job_schedule_client_factory)
cli_batch_data_plane_command('batch job-schedule enable', data_path.format('job_schedule', 'JobScheduleOperations.enable'), job_schedule_client_factory)
cli_batch_data_plane_command('batch job-schedule stop', data_path.format('job_schedule', 'JobScheduleOperations.terminate'), job_schedule_client_factory)
cli_batch_data_plane_command('batch job-schedule list', data_path.format('job_schedule', 'JobScheduleOperations.list'), job_schedule_client_factory)

cli_command(__name__, 'batch task create', custom_path.format('create_task'), task_client_factory, table_transformer=task_create_table_format)
cli_batch_data_plane_command('batch task list', data_path.format('task', 'TaskOperations.list'), task_client_factory)
cli_batch_data_plane_command('batch task delete', data_path.format('task', 'TaskOperations.delete'), task_client_factory)
cli_batch_data_plane_command('batch task show', data_path.format('task', 'TaskOperations.get'), task_client_factory)
cli_batch_data_plane_command('batch task reset', data_path.format('task', 'TaskOperations.update'), task_client_factory)
cli_batch_data_plane_command('batch task reactivate', data_path.format('task', 'TaskOperations.reactivate'), task_client_factory)
cli_batch_data_plane_command('batch task stop', data_path.format('task', 'TaskOperations.terminate'), task_client_factory)
cli_batch_data_plane_command('batch task subtask list', data_path.format('task', 'TaskOperations.list_subtasks'), task_client_factory)

cli_batch_data_plane_command('batch task file delete', data_path.format('file', 'FileOperations.delete_from_task'), file_client_factory)
cli_batch_data_plane_command('batch task file download', data_path.format('file', 'FileOperations.get_from_task'), file_client_factory)
cli_batch_data_plane_command('batch task file show', data_path.format('file', 'FileOperations.get_properties_from_task'), file_client_factory)
cli_batch_data_plane_command('batch task file list', data_path.format('file', 'FileOperations.list_from_task'), file_client_factory)

cli_batch_data_plane_command('batch node user create', data_path.format('compute_node', 'ComputeNodeOperations.add_user'), compute_node_client_factory)
cli_batch_data_plane_command('batch node user delete', data_path.format('compute_node', 'ComputeNodeOperations.delete_user'), compute_node_client_factory)
cli_batch_data_plane_command('batch node user reset', data_path.format('compute_node', 'ComputeNodeOperations.update_user'), compute_node_client_factory)
cli_batch_data_plane_command('batch node show', data_path.format('compute_node', 'ComputeNodeOperations.get'), compute_node_client_factory)
cli_batch_data_plane_command('batch node list', data_path.format('compute_node', 'ComputeNodeOperations.list'), compute_node_client_factory)
cli_batch_data_plane_command('batch node reboot', data_path.format('compute_node', 'ComputeNodeOperations.reboot'), compute_node_client_factory)
cli_batch_data_plane_command('batch node reimage', data_path.format('compute_node', 'ComputeNodeOperations.reimage'), compute_node_client_factory)
cli_batch_data_plane_command('batch node scheduling disable', data_path.format('compute_node', 'ComputeNodeOperations.disable_scheduling'), compute_node_client_factory)
cli_batch_data_plane_command('batch node scheduling enable', data_path.format('compute_node', 'ComputeNodeOperations.enable_scheduling'), compute_node_client_factory)
cli_batch_data_plane_command('batch node remote-login-settings show', data_path.format('compute_node', 'ComputeNodeOperations.get_remote_login_settings'), compute_node_client_factory)
cli_batch_data_plane_command('batch node remote-desktop download', data_path.format('compute_node', 'ComputeNodeOperations.get_remote_desktop'), compute_node_client_factory)

cli_batch_data_plane_command('batch node file delete', data_path.format('file', 'FileOperations.delete_from_compute_node'), file_client_factory)
cli_batch_data_plane_command('batch node file download', data_path.format('file', 'FileOperations.get_from_compute_node'), file_client_factory)
cli_batch_data_plane_command('batch node file show', data_path.format('file', 'FileOperations.get_properties_from_compute_node'), file_client_factory)
cli_batch_data_plane_command('batch node file list', data_path.format('file', 'FileOperations.list_from_compute_node'), file_client_factory)
