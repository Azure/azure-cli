# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.batch import _client_factory as factories
from azure.cli.command_modules.batch._validators import (
    validate_pool_settings, validate_options)
from azure.cli.command_modules.batch._exception_handler import batch_exception_handler
from azure.cli.command_modules.batch._format import (
    job_list_table_format,
    task_create_table_format,
    account_keys_list_table_format,
    account_list_table_format,
    application_list_table_format,
    account_keys_renew_table_format)
from azure.cli.command_modules.batch._transformers import batch_transformer


def _operation(name):
    return "".join(x.title() for x in name.split('_')) + "Operations"


# pylint: disable=too-many-locals, too-many-statements, line-too-long
def load_command_table(self, _):

    data_path = 'azure.batch._operations._patch#BatchClientOperationsMixin.{}'
    # data_path = 'azure.batch._client#BatchClient.{}'
    mgmt_path = 'azure.mgmt.batch.operations._{}_operations#{}.'

    def get_data_type():
        return CliCommandType(
            operations_tmpl=data_path,
            client_factory=get_data_factory(),
            exception_handler=batch_exception_handler,
            resource_type=ResourceType.DATA_BATCH
        )

    def get_mgmt_type(name):
        return CliCommandType(
            operations_tmpl=mgmt_path.format(name, _operation(name)) + "{}",
            client_factory=get_mgmt_factory(name),
            exception_handler=batch_exception_handler
        )

    def get_mgmt_factory(name):
        return getattr(factories, f"mgmt_{name}_client_factory")

    def get_data_factory():
        return factories.batch_data_client_factory

    # Mgmt Account Operations
    with self.command_group('batch account', get_mgmt_type('batch_account'), client_factory=get_mgmt_factory('batch_account')) as g:
        g.custom_command('list', 'list_accounts', table_transformer=account_list_table_format)
        g.custom_show_command('show', 'get_account')
        g.custom_command('create', 'create_account', supports_no_wait=True)
        g.custom_command('set', 'update_account')
        g.command('delete', 'begin_delete', supports_no_wait=True, confirmation=True)
        g.custom_command('login', 'login_account')
        g.command('autostorage-keys sync', 'synchronize_auto_storage_keys')
        g.command('keys list', 'get_keys', table_transformer=account_keys_list_table_format)
        # g.command('keys renew', 'regenerate_key', table_transformer=account_keys_renew_table_format)
        g.custom_command('keys renew', 'renew_accounts_keys', table_transformer=account_keys_renew_table_format)
        g.command('outbound-endpoints', 'list_outbound_network_dependencies_endpoints')

    with self.command_group('batch account identity', get_mgmt_type('batch_account'), client_factory=get_mgmt_factory('batch_account')) as g:
        g.custom_command('assign', 'assign_batch_identity')
        g.custom_command('remove', 'remove_batch_identity', confirmation=True)
        g.custom_show_command('show', 'show_batch_identity')

    with self.command_group('batch account network-profile', get_mgmt_type('batch_account'), client_factory=get_mgmt_factory('batch_account')) as g:
        g.custom_show_command('show', 'get_network_profile')
        g.custom_command('set', 'update_network_profile')

    with self.command_group('batch account network-profile network-rule', get_mgmt_type('batch_account'), client_factory=get_mgmt_factory('batch_account')) as g:
        g.custom_show_command('list', 'list_network_rules')
        g.custom_command('add', 'add_network_rule')
        g.custom_command('delete', 'delete_network_rule', confirmation=True)

    with self.command_group('batch application', get_mgmt_type('application'), client_factory=get_mgmt_factory('application')) as g:
        g.command('list', 'list', table_transformer=application_list_table_format)
        g.show_command('show', 'get')
        g.command('create', 'create')
        g.custom_command('set', 'update_application')
        g.command('delete', 'delete', confirmation=True)

    with self.command_group('batch application package', get_mgmt_type('application_package'), client_factory=get_mgmt_factory('application_package'))as g:
        g.custom_command('create', 'create_application_package')
        g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get')
        # g.command('activate', 'activate')
        g.custom_command('activate', 'activate_application_package')
        g.command('list', 'list')

    with self.command_group('batch location quotas', get_mgmt_type('location')) as g:
        g.show_command('show', 'get_quotas')

    with self.command_group('batch location', get_mgmt_type('location')) as g:
        g.show_command('list-skus', 'list_supported_virtual_machine_skus')

    with self.command_group('batch private-link-resource', get_mgmt_type('private_link_resource'), client_factory=get_mgmt_factory('private_link_resource')) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_batch_account')

    with self.command_group('batch private-endpoint-connection', get_mgmt_type('private_endpoint_connection'), client_factory=get_mgmt_factory('private_endpoint_connection')) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_batch_account')

    # Data Plane Commands
    with self.command_group('batch job', get_data_type(), client_factory=get_data_factory()) as g:
        g.batch_command('create', 'create_job')
        g.batch_command('delete', 'delete_job')
        g.batch_command('show', 'get_job')
        g.batch_command('set', 'update_job', flatten=2)
        g.batch_command('reset', 'replace_job', flatten=2)
        g.batch_command('disable', 'disable_job')
        g.custom_command('list', 'list_jobs', table_transformer=job_list_table_format, transform=batch_transformer.transform_result)
        g.batch_command('enable', 'enable_job')
        g.batch_command('stop', 'terminate_job')
        g.batch_command('prep-release-status list', 'list_job_preparation_and_release_task_status')
        g.batch_command('task-counts show', 'get_job_task_counts')

    with self.command_group('batch application summary', get_data_type()) as g:
        g.batch_command('list', 'list_applications')
        g.batch_command('show', 'get_application')

    with self.command_group('batch pool supported-images', get_data_type()) as g:
        g.batch_command('list', 'list_supported_images')

    with self.command_group('batch pool node-counts', get_data_type()) as g:
        g.batch_command('list', 'list_pool_node_counts')

    with self.command_group('batch pool', get_data_type(), client_factory=get_data_factory()) as g:
        g.batch_command('usage-metrics list', 'list_pool_usage_metrics')
        g.batch_command('create', 'create_pool', validator=validate_pool_settings, flatten=10)
        g.batch_command('list', 'list_pools')
        g.batch_command('delete', 'delete_pool')
        g.batch_command('show', 'get_pool')
        g.batch_command('set', 'update_pool')
        g.custom_command('reset', 'replace_pool')
        g.custom_command('resize', 'resize_pool')
        g.batch_command('autoscale disable', 'disable_pool_auto_scale')
        g.batch_command('autoscale enable', 'enable_pool_auto_scale')
        g.batch_command('autoscale evaluate', 'evaluate_pool_auto_scale')

    with self.command_group('batch job-schedule', get_data_type()) as g:
        g.batch_command('create', 'create_job_schedule')
        g.batch_command('delete', 'delete_job_schedule')
        g.batch_command('show', 'get_job_schedule')
        g.batch_command('set', 'update_job_schedule')
        g.batch_command('reset', 'replace_job_schedule')
        g.batch_command('disable', 'disable_job_schedule')
        g.batch_command('enable', 'enable_job_schedule')
        g.batch_command('stop', 'terminate_job_schedule')
        g.batch_command('list', 'list_job_schedules')

    with self.command_group('batch task', get_data_type(), client_factory=get_data_factory()) as g:
        g.custom_command('create', 'create_task', table_transformer=task_create_table_format, transform=batch_transformer.transform_result)
        g.batch_command('list', 'list_tasks')
        g.batch_command('delete', 'delete_task')
        g.batch_command('show', 'get_task')
        g.custom_command('reset', 'replace_task')
        g.batch_command('reactivate', 'reactivate_task')
        g.batch_command('stop', 'terminate_task')
        g.batch_command('subtask list', 'list_sub_tasks')

    file_type = get_data_type()
    with self.command_group('batch task file', file_type) as g:
        g.batch_command('delete', 'delete_task_file')
        g.batch_command('download', 'get_task_file', validator=validate_options)
        g.batch_command('show', 'get_task_file_properties')
        g.batch_command('list', 'list_task_files')

    with self.command_group('batch node file', file_type) as g:
        g.batch_command('delete', 'delete_node_file')
        g.batch_command('download', 'get_node_file', validator=validate_options)
        g.batch_command('show', 'get_node_file_properties')
        g.batch_command('list', 'list_node_files')

    with self.command_group('batch node', get_data_type()) as g:
        g.batch_command('user create', 'create_node_user')
        g.batch_command('user delete', 'delete_node_user')
        g.batch_command('user reset', 'replace_node_user')
        g.batch_command('show', 'get_node')
        g.batch_command('list', 'list_nodes')
        g.batch_command('reboot', 'reboot_node')
        g.batch_command('delete', 'remove_nodes')
        g.batch_command('scheduling disable', 'disable_node_scheduling')
        g.batch_command('scheduling enable', 'enable_node_scheduling')
        g.batch_command('remote-login-settings show', 'get_node_remote_login_settings')
        g.batch_command('service-logs upload', 'upload_node_logs')
