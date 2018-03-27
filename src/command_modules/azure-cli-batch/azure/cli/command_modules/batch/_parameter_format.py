# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# The level of complex object namespace to flatten.
FLATTEN = 3

# Non-complex types that should not be flattened.
BASIC_TYPES = {
    'str',
    'int',
    'bool',
    'float',
    'long',
    'duration',
    'iso-8601',
    'rfc-1123',
    'date',
    'decimal',
    'unix-time'
}

# Parameters that we want to be present in the namespace, but not exposed to the user as arguments
SILENT_PARAMETERS = [
    'pool.virtual_machine_configuration.image_reference'
]

# Common argument names the should always be prefixed by their context
QUALIFIED_PROPERTIES = [
    'id',
    'display_name',
    'command_line',
    'environment_settings',
    'wait_for_success',
    'max_task_retry_count',
    'constraints_max_task_retry_count',
    'max_wall_clock_time',
    'constraints_max_wall_clock_time',
    'retention_time',
    'constraints_retention_time',
    'application_package_references',
    'resource_files',
    'user_name'
]

# Header options that should not be exposed as arguments.
IGNORE_OPTIONS = {
    'ocp_date',
    'timeout',
    'client_request_id',
    'return_client_request_id',
    'max_results',
    'additional_properties'
}

# Parameters that can be completely ignored.
# This can be the complete path to a single parameter to be removed, or any part
# of a path. Any parameter that has a match to the partial path will be removed.
IGNORE_PARAMETERS = [
    'callback',
    'thumbprint_algorithm',
    'display_name',
    'common_environment_settings',
    'job_preparation_task',
    'job_release_task',
    'auto_pool_specification',
    'on_task_failure',
    'max_tasks_per_node',
    'job.on_all_tasks_complete',
    'job_manager_task.kill_job_on_completion',
    'job_manager_task.run_exclusive',
    'job_manager_task.constraints',
    'job_manager_task.allow_low_priority_node',
    'job.job_manager_task.application_package_references',
    'virtual_machine_configuration.windows_configuration',
    'virtual_machine_configuration.os_disk',
    'virtual_machine_configuration.container_configuration',
    'virtual_machine_configuration.license_type',
    'task_scheduling_policy',
    'container_settings',
    'user_identity',
    'network_configuration',
    'enable_auto_scale',
    'cloud_service_configuration.target_os_version',
    'pool.auto_scale_evaluation_interval',
    'pool.start_task.environment_settings',
    'pool.start_task.max_task_retry_count',
    'job_schedule_patch_parameter.job_specification.constraints',
    'job_schedule_update_parameter.job_specification.constraints',
    'job_schedule.job_specification.metadata',
    'job_schedule.job_specification.job_manager_task.application_package_references',
    'job_schedule.job_specification.job_manager_task.environment_settings'
]

# Options to be flattened into multiple arguments.
FLATTEN_OPTIONS = {
    'ocp_range': {
        'start_range': "The byte range to be retrieved. If not set the file will be retrieved from the beginning.",
        'end_range': "The byte range to be retrieved. If not set the file will be retrieved to the end."
    }
}
